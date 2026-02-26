import os
import time
from google.genai import types
from typing import List, Dict
from config_loader import config

def _load_text_file(filepath: str) -> str:
    """Helper per caricare i file di testo (prompt e/o appunti precedenti)."""
    if not os.path.exists(filepath):
        return ""
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def create_chunks(transcript: List[Dict], keyframes: List[Dict], chunk_duration_sec: int = None) -> List[Dict]:
    """
    Divide la lezione in blocchi logici senza tagliare le frasi.
    La durata del chunk è configurabile in config.yaml.
    
    NOTA: Se transcript contiene già chunks unificati (da merge_sources),
    ritorna direttamente quelli invece di creare nuovi chunks.
    """
    if chunk_duration_sec is None:
        chunk_duration_sec = config.chunk_duration_sec
    
    # Check se sono già chunks unificati (contengono 'images' o 'files')
    if transcript and ('images' in transcript[0] or 'files' in transcript[0]):
        return transcript  # Già nel formato corretto
    
    chunks = []
    current_chunk_text = []
    current_chunk_images = []
    chunk_start_time = 0.0
    
    # inserisco tutta la trascrizione del chunk in esame e poi allego tutte le immagini corrispondenti
    for segment in transcript:
        current_chunk_text.append(f"[{segment['start']:.1f}s - {segment['end']:.1f}s]: {segment['text']}")
        
        # Se superiamo la durata prevista per il blocco (es. 900 secondi = 15 min)
        if segment['end'] - chunk_start_time >= chunk_duration_sec:
            # Trova le immagini che appartengono a questo lasso di tempo
            for kf in keyframes:
                if chunk_start_time <= kf['timestamp'] <= segment['end']:
                    current_chunk_images.append(kf['path'])
            
            # Salva il pacchetto e resetta i contatori per il blocco successivo
            chunks.append({
                "text": "\n".join(current_chunk_text),
                "images": current_chunk_images.copy(),
                "files": []
            })
            current_chunk_text = []
            current_chunk_images = []
            chunk_start_time = segment['end']
            
    # Gestisci l'ultimo pezzo rimasto (la fine della lezione)
    if current_chunk_text:
        for kf in keyframes:
            if kf['timestamp'] >= chunk_start_time:
                current_chunk_images.append(kf['path'])
        chunks.append({
            "text": "\n".join(current_chunk_text), 
            "images": current_chunk_images,
            "files": []
        })
        
    return chunks

def generate_notes(transcript: List[Dict], keyframes: List[Dict], api_key: str = None,
                   prompt_path: str = None, history_path: str = "", input_mode: str = "video") -> str:
    """
    Motore principale che coordina LLM, memorie e generazione LaTeX.
    Tutti i parametri LLM sono caricati da config.yaml.
    
    input_mode può essere:
    - 'video': videolezione (prompt standard multi-source)
    - 'only_slides': solo slide PDF (prompt espansione)
    - 'only_notes': solo appunti studenti PDF (prompt trascrizione fedele)
    - 'mixed_pdf': mix slides + notes (prompt espansione con fusion)
    """
    # Validazione input
    if not transcript:
        raise ValueError("Transcript vuoto: impossibile generare appunti senza trascrizione")
    
    if not isinstance(transcript, list) or not all('text' in seg for seg in transcript):
        raise ValueError("Transcript malformato: deve essere una lista di dict con chiave 'text'")
    
    if api_key is None:
        api_key = config.api_key
    
    # Selezione automatica del prompt in base al tipo di input
    if prompt_path is None:
        base_path = config.writer_prompt_path.replace('writer_system_prompt.txt', '')
        
        if input_mode == "only_notes":
            prompt_path = base_path + 'writer_system_prompt_notes.txt'
            print("📝 Modalità TRASCRIZIONE: appunti studenti → LaTeX fedele")
        elif input_mode in ["only_slides", "mixed_pdf"]:
            prompt_path = base_path + 'writer_system_prompt_pdf.txt'
            print("📄 Modalità ESPANSIONE: slide/documenti → appunti dettagliati")
        else:
            prompt_path = config.writer_prompt_path
            print("🎬 Modalità STANDARD: videolezione multi-source")
    
    # Usa client condiviso da config (lazy-loaded)
    client = config.genai_client
    
    try:
        system_instruction = _load_text_file(prompt_path)
    except Exception as e:
        raise FileNotFoundError(f"Impossibile caricare prompt da {prompt_path}: {e}") from e
    
    previous_notes = _load_text_file(history_path)
    
    if previous_notes:
        system_instruction += f"\n\nNOTES UNTIL THE LAST LESSON (Use as context or base to generate new notes):\n{previous_notes}"

    # Configurazione generazione
    generation_config = types.GenerateContentConfig(
        temperature=config.writer_temperature,
        top_p=config.writer_top_p,
        top_k=config.writer_top_k,
        max_output_tokens=config.writer_max_tokens,
        system_instruction=system_instruction
    )
    
    chunks = create_chunks(transcript, keyframes, chunk_duration_sec=config.chunk_duration_sec)
    final_latex_document = []
    
    # Storia della conversazione per continuità
    chat_history = []
    
    for idx, chunk in enumerate(chunks):
        # Prepara il contenuto multimodale
        parts = [types.Part(text=f"=== CHUNK {idx + 1} di {len(chunks)} ===\nTrascrizione:\n{chunk['text']}")]
        
        # Aggiungi immagini come blob (da keyframes video)
        if 'images' in chunk and chunk['images']:
            for img_path in chunk['images']:
                try:
                    with open(img_path, 'rb') as f:
                        image_data = f.read()
                    parts.append(types.Part.from_bytes(data=image_data, mime_type='image/jpeg'))
                except Exception as e:
                    print(f"Errore lettura immagine {img_path}: {e}")
        
        # Aggiungi file PDF (da documenti caricati)
        if 'files' in chunk and chunk['files']:
            for pdf_part in chunk['files']:
                parts.append(pdf_part)
        
        # Costruisci i contenuti per la chat
        contents = chat_history + [types.Content(role='user', parts=parts)]
        
        # Genera risposta
        try:
            response = client.models.generate_content(
                model=config.model_name,
                contents=contents,
                config=generation_config
            )
            response_text = response.text
        except Exception as e:
            raise RuntimeError(f"Errore chiamata API Gemini per chunk {idx+1}/{len(chunks)}: {e}") from e
        
        # Estrai testo e aggiorna storia
        final_latex_document.append(response_text)
        
        chat_history.append(types.Content(role='user', parts=parts))
        chat_history.append(types.Content(role='model', parts=[types.Part(text=response_text)]))
        
        # Rate limiting
        if idx < len(chunks) - 1:
            wait_time = 60 / config.rpm
            time.sleep(wait_time)
            
    return "\n\n".join(final_latex_document)