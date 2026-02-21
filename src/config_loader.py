""")
Modulo per la gestione centralizzata della configurazione di AI-Studio.
Carica il file config.yaml e fornisce accesso type-safe ai parametri.
"""

import yaml
import os
from typing import Any, Dict, Optional
from pathlib import Path

class Config:
    """
    Singleton per la configurazione dell'applicazione.
    Carica config.yaml e supporta override tramite variabili d'ambiente.
    """
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: str = None):
        """
        Inizializza la configurazione caricando il file YAML.
        
        Args:
            config_path: Percorso al file config.yaml (default: root del progetto)
        """
        if self._config is not None:
            return  # Già inizializzato
        
        if config_path is None:
            # Trova la root del progetto (dove si trova config.yaml)
            current_dir = Path(__file__).parent.parent  # src -> root
            config_path = current_dir / "config.yaml"
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"File di configurazione non trovato: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        # Sostituisci variabili d'ambiente (es: ${GOOGLE_API_KEY})
        self._resolve_env_vars(self._config)
    
    def _resolve_env_vars(self, obj: Any) -> None:
        """Risolve ricorsivamente le variabili d'ambiente nel formato ${VAR_NAME}."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]  # Estrae il nome della variabile
                    obj[key] = os.getenv(env_var, value)  # Sostituisce o lascia il placeholder
                elif isinstance(value, (dict, list)):
                    self._resolve_env_vars(value)
        elif isinstance(obj, list):
            for item in obj:
                self._resolve_env_vars(item)
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Ottieni un valore di configurazione usando la notazione dot (es: 'llm.writer.temperature').
        
        Args:
            path: Percorso dot-separated al valore (es: 'audio.whisper_model_size')
            default: Valore di default se la chiave non esiste
            
        Returns:
            Il valore della configurazione o il default
        """
        keys = path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    # ========== PROPRIETÀ DI ACCESSO RAPIDO (Type-safe) ==========
    
    # --- LLM ---
    @property
    def api_key(self) -> str:
        """
        API Key di Google Gemini.
        Legge SEMPRE la variabile d'ambiente GOOGLE_API_KEY a runtime,
        bypassando il config.yaml. Questo permette di settare la chiave
        dinamicamente nel notebook dopo l'import del modulo.
        """
        # Prima prova a leggere direttamente dalla variabile d'ambiente
        env_key = os.environ.get('GOOGLE_API_KEY', '').strip()
        if env_key:
            return env_key
        
        # Se non c'è nella variabile d'ambiente, leggi dal config
        key = self.get('llm.api_key', '')
        if key.startswith("${"):
            raise ValueError(
                f"API Key non configurata. Imposta la variabile d'ambiente GOOGLE_API_KEY "
                f"nel notebook prima di eseguire la cella di processing."
            )
        return key
    
    @property
    def model_name(self) -> str:
        return self.get('llm.model_name', 'gemini-2.0-flash-exp')
    
    @property
    def rpm(self) -> int:
        return self.get('llm.rpm', 5)
    
    # Writer
    @property
    def writer_temperature(self) -> float:
        return self.get('llm.writer.temperature', 0.5)
    
    @property
    def writer_top_p(self) -> float:
        return self.get('llm.writer.top_p', 0.8)
    
    @property
    def writer_top_k(self) -> int:
        return self.get('llm.writer.top_k', 40)
    
    @property
    def writer_max_tokens(self) -> int:
        return self.get('llm.writer.max_output_tokens', 45000)
    
    @property
    def chunk_duration_sec(self) -> int:
        return self.get('llm.writer.chunk_duration_sec', 900)
    
    # Editor
    @property
    def editor_temperature(self) -> float:
        return self.get('llm.editor.temperature', 0.3)
    
    @property
    def editor_top_p(self) -> float:
        return self.get('llm.editor.top_p', 0.8)
    
    @property
    def editor_top_k(self) -> int:
        return self.get('llm.editor.top_k', 30)
    
    @property
    def editor_max_tokens(self) -> int:
        return self.get('llm.editor.max_output_tokens', 8000)
    
    # Tutor
    @property
    def tutor_temperature(self) -> float:
        return self.get('llm.tutor.temperature', 0.75)
    
    @property
    def tutor_top_p(self) -> float:
        return self.get('llm.tutor.top_p', 0.9)
    
    @property
    def tutor_top_k(self) -> int:
        return self.get('llm.tutor.top_k', 50)
    
    @property
    def tutor_max_tokens(self) -> int:
        return self.get('llm.tutor.max_output_tokens', 4000)
    
    # --- AUDIO ---
    @property
    def whisper_model_size(self) -> str:
        return self.get('audio.whisper_model_size', 'large-v3')
    
    @property
    def audio_device(self) -> str:
        return self.get('audio.device', 'cuda')
    
    @property
    def compute_type(self) -> str:
        return self.get('audio.compute_type', 'float16')
    
    @property
    def beam_size(self) -> int:
        return self.get('audio.beam_size', 5)
    
    @property
    def vad_enabled(self) -> bool:
        return self.get('audio.vad_enabled', True)
    
    @property
    def vad_min_silence_ms(self) -> int:
        return self.get('audio.vad_min_silence_duration_ms', 1000)
    
    @property
    def audio_sample_rate(self) -> int:
        return self.get('audio.audio_sample_rate', 16000)
    
    @property
    def audio_channels(self) -> int:
        return self.get('audio.audio_channels', 1)
    
    @property
    def temp_audio_filename(self) -> str:
        return self.get('audio.temp_audio_filename', 'temp_audio.wav')
    
    # --- VISION ---
    @property
    def vision_output_dir(self) -> str:
        return self.get('vision.output_dir', 'extracted_frames')
    
    @property
    def frame_sample_interval(self) -> int:
        """Intervallo in secondi tra i frame da analizzare (default: 5s)"""
        return self.get('vision.frame_sample_interval', 5)
    
    @property
    def change_threshold(self) -> float:
        return self.get('vision.change_threshold', 0.03)
    
    @property
    def blur_kernel_size(self) -> int:
        return self.get('vision.blur_kernel_size', 21)
    
    @property
    def blur_sigma(self) -> int:
        return self.get('vision.blur_sigma', 0)
    
    @property
    def pixel_threshold(self) -> int:
        return self.get('vision.pixel_threshold', 25)
    
    # --- PATHS ---
    @property
    def prompts_dir(self) -> str:
        return self.get('paths.prompts_dir', 'prompts')
    
    @property
    def writer_prompt_path(self) -> str:
        prompts_dir = self.prompts_dir
        filename = self.get('paths.writer_prompt', 'writer_system_prompt.txt')
        return f"{prompts_dir}/{filename}"
    
    @property
    def editor_prompt_path(self) -> str:
        prompts_dir = self.prompts_dir
        filename = self.get('paths.editor_prompt', 'reviewer_editor_prompt.txt')
        return f"{prompts_dir}/{filename}"
    
    @property
    def tutor_prompt_path(self) -> str:
        prompts_dir = self.prompts_dir
        filename = self.get('paths.tutor_prompt', 'professor_q&a_prompt.txt')
        return f"{prompts_dir}/{filename}"
    
    # --- SYSTEM ---
    @property
    def auto_cleanup(self) -> bool:
        return self.get('system.auto_cleanup', True)
    
    # --- GOOGLE GENAI CLIENT (Lazy-loaded singleton) ---
    @property
    def genai_client(self):
        """
        Client Google Gemini condiviso (lazy-loaded).
        Crea il client una sola volta e lo riutilizza.
        """
        if not hasattr(self, '_genai_client'):
            try:
                from google import genai
                self._genai_client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise RuntimeError(
                    "Libreria google-genai non installata. "
                    "Installa con: pip install google-genai>=0.2.0"
                ) from None
            except Exception as e:
                raise RuntimeError(f"Errore creazione client Gemini: {e}") from e
        return self._genai_client


# Singleton globale accessibile da tutti i moduli
config = Config()
