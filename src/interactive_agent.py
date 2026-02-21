import os
from google import genai
from config_loader import config

def _load_text_file(filepath: str) -> str:
    """Helper per caricare i file di testo dei prompt."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Il file di prompt {filepath} non è stato trovato.")
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def run_editor_agent(latex_snippet: str, user_request: str, lesson_transcript: str, 
                     api_key: str = None, prompt_path: str = None) -> str:
    """
    Agente Chirurgo: Riceve un pezzo di LaTeX, la richiesta di modifica e l'intera 
    trascrizione. Restituisce SOLO il nuovo codice LaTeX sovrascrivibile.
    Parametri LLM caricati da config.yaml.
    """
    if api_key is None:
        api_key = config.api_key
    
    if prompt_path is None:
        prompt_path = config.editor_prompt_path
    
    genai.configure(api_key=api_key)
    system_instruction = _load_text_file(prompt_path)
    
    # Configurazione severissima caricata da config.yaml
    generation_config = genai.types.GenerationConfig(
        temperature=config.editor_temperature,
        top_p=config.editor_top_p,
        top_k=config.editor_top_k,
        max_output_tokens=config.editor_max_tokens
    )
    
    model = genai.GenerativeModel(
        model_name=config.model_name,
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
                    api_key: str = None, prompt_path: str = None) -> str:
    """
    Agente Tutor: Riceve una domanda e la trascrizione. Risponde in modo empatico 
    e discorsivo, rigorosamente in plain text (senza markdown).
    Parametri LLM caricati da config.yaml.
    """
    if api_key is None:
        api_key = config.api_key
    
    if prompt_path is None:
        prompt_path = config.tutor_prompt_path
    
    genai.configure(api_key=api_key)
    system_instruction = _load_text_file(prompt_path)
    
    # Configurazione caricata da config.yaml
    generation_config = genai.types.GenerationConfig(
        temperature=config.tutor_temperature,
        top_p=config.tutor_top_p,
        top_k=config.tutor_top_k,
        max_output_tokens=config.tutor_max_tokens
    )
    
    model = genai.GenerativeModel(
        model_name=config.model_name,
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