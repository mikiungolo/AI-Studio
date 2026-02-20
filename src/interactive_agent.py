import os
import google.generativeai as genai

def _load_text_file(filepath: str) -> str:
    """Helper per caricare i file di testo dei prompt."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Il file di prompt {filepath} non è stato trovato.")
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def run_editor_agent(latex_snippet: str, user_request: str, lesson_transcript: str, 
                     api_key: str, prompt_path: str = "prompts/editor_prompt.txt") -> str:
    """
    Agente Chirurgo: Riceve un pezzo di LaTeX, la richiesta di modifica e l'intera 
    trascrizione. Restituisce SOLO il nuovo codice LaTeX sovrascrivibile.
    """
    genai.configure(api_key=api_key)
    system_instruction = _load_text_file(prompt_path)
    
    # Configurazione severissima: l'output DEVE essere solo codice stabile
    generation_config = genai.types.GenerationConfig(
        temperature=0.3,       # Molto basso: nessuna libertà creativa, solo esecuzione
        top_p=0.8,
        top_k=30,
    )
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=system_instruction,
        generation_config=generation_config
    )
    
    # Costruiamo il prompt strutturato per non far confondere l'LLM
    prompt_str = (
        f"CONTESTO DELLA LEZIONE (Trascrizione):\n{lesson_transcript}\n\n"
        f"CODICE LATEX DA MODIFICARE:\n```latex\n{latex_snippet}\n```\n\n"
        f"RICHIESTA DELLO STUDENTE:\n{user_request}\n\n"
        "Esegui la modifica e restituisci ESCLUSIVAMENTE il nuovo codice LaTeX."
    )
    
    response = model.generate_content(prompt_str)
    
    # Pulizia di sicurezza: rimuove eventuali formattazioni markdown "```latex" residue 
    # che Gemini potrebbe inserire nonostante i divieti
    clean_output = response.text.replace("```latex", "").replace("```", "").strip()
    return clean_output

def run_tutor_agent(user_question: str, lesson_transcript: str, 
                    api_key: str, prompt_path: str = "prompts/tutor_prompt.txt") -> str:
    """
    Agente Tutor: Riceve una domanda e la trascrizione. Risponde in modo empatico 
    e discorsivo, rigorosamente in plain text (senza markdown).
    """
    genai.configure(api_key=api_key)
    system_instruction = _load_text_file(prompt_path)
    
    # Configurazione leggermente più morbida per permettere un tono empatico e naturale
    generation_config = genai.types.GenerationConfig(
        temperature=0.75,       # Più alto dell'editor per sembrare umano, ma basso per non allucinare
        top_p=0.9,
    )
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=system_instruction,
        generation_config=generation_config
    )
    
    prompt_str = (
        f"CONTESTO DELLA LEZIONE (Trascrizione base per la tua risposta):\n{lesson_transcript}\n\n"
        f"DOMANDA DELLO STUDENTE:\n{user_question}\n\n"
        "Rispondi seguendo le regole del tuo prompt (empatia, plain text puro)."
    )
    
    response = model.generate_content(prompt_str)
    return response.text.strip()