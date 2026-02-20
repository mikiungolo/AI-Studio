import cv2
import os
from config_loader import config

def _save_keyframe(frame, timestamp: float, output_dir: str, keyframes_list: list):
    """Funzione helper per salvare il frame e aggiornare la lista."""
    frame_name = f"{output_dir}/slide_{timestamp:.0f}s.jpg"
    cv2.imwrite(frame_name, frame)
    keyframes_list.append({"timestamp": timestamp, "path": frame_name})

def extract_keyframes(video_path: str, output_dir: str = None, threshold: float = None) -> list:
    """
    Estrae i keyframe dal video quando rileva cambiamenti significativi.
    Tutti i parametri sono configurabili tramite config.yaml.
    """
    if output_dir is None:
        output_dir = config.vision_output_dir
    
    if threshold is None:
        threshold = config.change_threshold
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    cap = cv2.VideoCapture(video_path)
    # Interroga il video per sapere quanti fotogrammi ci sono per secondo (es. 30 o 60)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # Processeremo esattamente 1 frame per ogni secondo di video reale
    frame_interval = int(fps) 
    
    keyframes = []
    prev_frame = None
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break 
            
        # Se FPS=30 o 60, il check passa solo a frame multipli, ovvero si cattura un frame al secondo 
        # per evitare di controllarne di più inutilmente. 
        if frame_count % frame_interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # GaussianBlur: sfuma i contorni per ignorare piccoli movimenti del professore
            # Un pixel che passa da "Grigio 40%" a "Grigio 45%" diventa impercettibile 
            # -> contrariamente senza la scala di grigi e la sfumatura applicata un minimo movimento 
            #    è considerato un grande cambiamento a livello visivo nel video.
            gray = cv2.GaussianBlur(gray, (config.blur_kernel_size, config.blur_kernel_size), config.blur_sigma)
            timestamp = frame_count / fps
            
            if prev_frame is None:
                # il primo frame viene sempre salvato come punto di partenza
                _save_keyframe(frame, timestamp, output_dir, keyframes)
                prev_frame = gray
            else:
                # Crea un frame differenza, dove i punti di cambiamento assumono un colore 
                # tanto più chiaro quant'è il cambiamento tra i due frame confrontati.  
                diff = cv2.absdiff(prev_frame, gray)
                # Il "buttafuori": cambiamenti sotto pixel_threshold (colore poco chiaro) → azzerati (rumore/movimento prof)
                # Cambiamenti sopra pixel_threshold → portati a 255 (es. nuova scritta sulla slide)
                _, thresh = cv2.threshold(diff, config.pixel_threshold, 255, cv2.THRESH_BINARY)
                
                # Conta quanti pixel bianchi (=cambiamenti reali) sono rimasti
                change_ratio = cv2.countNonZero(thresh) / (gray.shape[0] * gray.shape[1])
                
                # Se più del 3% dello schermo è cambiato, è cambiata la scena, quindi da catturare 
                if change_ratio > threshold:
                    _save_keyframe(frame, timestamp, output_dir, keyframes)
                    prev_frame = gray 
                    
        frame_count += 1
        
    cap.release()
    return keyframes