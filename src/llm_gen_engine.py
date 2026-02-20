import os
import time
import google.generativeai as genai
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
    """
    if chunk_duration_sec is None:
        chunk_duration_sec = config.chunk_duration_sec
    
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
                "images": current_chunk_images.copy()
            })
            current_chunk_text = []
            current_chunk_images = []
            chunk_start_time = segment['end']
            
    # Gestisci l'ultimo pezzo rimasto (la fine della lezione)
    if current_chunk_text:
        for kf in keyframes:
            if kf['timestamp'] >= chunk_start_time:
                current_chunk_images.append(kf['path'])
        chunks.append({"text": "\n".join(current_chunk_text), "images": current_chunk_images})
        
    return chunks

def generate_notes(transcript: List[Dict], keyframes: List[Dict], api_key: str = None,
                   prompt_path: str = None, history_path: str = "") -> str:
    """
    Motore principale che coordina LLM, memorie e generazione LaTeX.
    Tutti i parametri LLM sono caricati da config.yaml.
    """
    
    if api_key is None:
        api_key = config.api_key
    
    if prompt_path is None:
        prompt_path = config.writer_prompt_path
    
    genai.configure(api_key=api_key)
    
    system_instruction = _load_text_file(prompt_path)
    previous_notes = _load_text_file(history_path)
    
    if previous_notes:
        # Inietta gli appunti passati direttamente nelle istruzioni di sistema
        system_instruction += f"\n\nNOTES UNTIL THE LAST LESSON (Use as context or base to generate new notes):\n{previous_notes}"

    # Configurazione parametri modello (caricati da config.yaml)
    generation_config = genai.types.GenerationConfig(
        temperature=config.writer_temperature,
        top_p=config.writer_top_p,
        top_k=config.writer_top_k,
        max_output_tokens=config.writer_max_tokens
    )

    # Inizializza il modello caricando le istruzioni di sistema e i vincoli di generazione
    model = genai.GenerativeModel(
        model_name=config.model_name,
        system_instruction=system_instruction,
        generation_config=generation_config
    )
    
    # Avvia una sessione chat per mantenere la continuità logica tra i chunk
    chat_session = model.start_chat(history=[])
    
    chunks = create_chunks(transcript, keyframes, chunk_duration_sec=900)
    final_latex_document = []
    
    # vengono inviati in una sessione si chat i singoli chank uno per volta per non saturare il limite 
    # di token che prevede il modello. Il tutto tramite chat session perchè ci aiuta a dare continuità di logica 
    # nelle risposte ottenute. Ogni risposta viene unita opportunamente per ottenere interamente gli appunti della lezione.
    for idx, chunk in enumerate(chunks):
        uploaded_files = []
        
        # Inizializza il payload multimodale (Lista Python che il modello sa decodificare)
        payload = [f"=== CHUNK {idx + 1} di {len(chunks)} ===\nTrascrizione:\n{chunk['text']}"]
        
        # Carica le immagini sui server di Google e aggiungi il 'puntatore' al payload
        for img_path in chunk['images']:
            try:
                g_file = genai.upload_file(path=img_path)
                uploaded_files.append(g_file)
                payload.append(g_file)
            except Exception as e:
                print(f"Errore caricamento immagine {img_path}: {e}")
                
        # Invia il pacchetto multimodale intero alla sessione di chat
        response = chat_session.send_message(payload)
        final_latex_document.append(response.text)
        il limite RPM configurato
        if idx < len(chunks) - 1:
            wait_time = 60 / config.rpm
            if config.debug_mode:
                print(f"Attesa di {wait_time:.1f} secondi per rispettare il limite di {config.rpm} RPM...")
            time.sleep(wait_timeile.name)
            except Exception as e:
                print(f"Errore eliminazione file {g_file.name}: {e}")
        
        # Garantisce di non superare MAI il limite di 2 richieste al minuto
        if idx < len(chunks) - 1:
            wait_for_limit = 60/rpm 
            print(f"Attesa di 15 secondi per rispettare il limite di 5 RPM...")
            time.sleep(wait_for_limit)
            
    return "\n\n".join(final_latex_document)