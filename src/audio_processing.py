import subprocess
from faster_whisper import WhisperModel
import os
from config_loader import config

def extract_audio(video_path: str, audio_output_path: str = None) -> str:
    """
    Estrae la traccia audio dal video usando FFmpeg.
    I parametri di qualità audio sono caricati da config.yaml.
    """
    if audio_output_path is None:
        audio_output_path = config.temp_audio_filename
    
    # Usa FFmpeg per estrarre l'audio con parametri configurabili
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", str(config.audio_sample_rate),  # Sample rate da config
        "-ac", str(config.audio_channels),     # Canali audio da config
        "-y",
        audio_output_path
    ]
    
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return audio_output_path

def transcribe_with_timestamps(audio_path: str, model_size: str = None) -> list:
    """
    Trascrizione con Whisper + VAD (Voice Activity Detection).
    Tutti i parametri sono caricati da config.yaml.
    """
    if model_size is None:
        model_size = config.whisper_model_size
    
    # Inizializza il modello Whisper con parametri configurabili
    model = WhisperModel(
        model_size, 
        device=config.audio_device, 
        compute_type=config.compute_type
    )
    
    # Trascrizione con VAD integrato
    segments, info = model.transcribe(
        audio_path,
        beam_size=config.beam_size,
        vad_filter=config.vad_enabled,
        vad_parameters=dict(min_silence_duration_ms=config.vad_min_silence_ms)
    )
    
    transcript_data = []
    
    for segment in segments:
        transcript_data.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
        
    return transcript_data

def process_video_audio(video_path: str) -> list:
    """Pipeline completa: estrazione audio + trascrizione + cleanup."""
    temp_audio = extract_audio(video_path)
    transcript = transcribe_with_timestamps(temp_audio)
    
    # Pulizia del file temporaneo (se auto_cleanup è abilitato in config)
    if config.auto_cleanup and os.path.exists(temp_audio):
        os.remove(temp_audio)
        
    return transcript