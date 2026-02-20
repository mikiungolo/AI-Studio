import subprocess
from faster_whisper import WhisperModel
import os

def extract_audio(video_path: str, audio_output_path: str = "temp_audio.wav") -> str:
    # Usa FFmpeg per estrarre l'audio a 16kHz, mono (formato ottimale per Whisper)
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        audio_output_path
    ]
    
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return audio_output_path

def transcribe_with_timestamps(audio_path: str, model_size: str = "large-v3") -> list:
    # Inizializza il modello Whisper ottimizzato
    model = WhisperModel(model_size, device="cuda", compute_type="float16")
    
    # Trascrizione con VAD (Voice Activity Detection) integrato
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True, # for VAD Coice Activity Detection
        vad_parameters=dict(min_silence_duration_ms=1000) # transcription off if silence.
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
    temp_audio = extract_audio(video_path)
    transcript = transcribe_with_timestamps(temp_audio)
    
    # Pulizia del file temporaneo
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
        
    return transcript