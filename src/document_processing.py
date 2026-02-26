"""
Modulo per processare documenti PDF (slide del corso, appunti di altri studenti).
Sfrutta il supporto PDF nativo di Gemini API senza bisogno di OCR.
Divide i PDF in chunks intelligenti basati sul conteggio parole.
"""

import os
import io
from typing import List, Dict, Tuple, Optional
from google.genai import types
from config_loader import config

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
    print("⚠️ PyPDF2 non installato. Chunking avanzato disabilitato. Installa con: pip install PyPDF2")


def extract_text_from_pdf(pdf_path: str) -> Dict[int, str]:
    """Estrae testo da ogni pagina PDF. Returns: dict {page_num: text}"""
    if PyPDF2 is None:
        raise RuntimeError(
            "PyPDF2 non installato. Impossibile estrarre testo per chunking intelligente.\n"
            "Installa con: pip install PyPDF2"
        )
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            page_texts = {}
            
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                page_texts[page_num] = text
            
            return page_texts
    except Exception as e:
        raise RuntimeError(f"Errore estrazione testo da {pdf_path}: {e}") from e


def count_words(text: str) -> int:
    """Conta le parole in un testo (semplice split su spazi)."""
    return len(text.split())


def create_pdf_chunk_from_pages(pdf_path: str, start_page: int, end_page: int) -> bytes:
    """Crea PDF con solo le pagine [start_page, end_page). Returns: bytes"""
    if PyPDF2 is None:
        # Fallback: ritorna tutto il PDF
        with open(pdf_path, 'rb') as f:
            return f.read()
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            writer = PyPDF2.PdfWriter()
            
            for page_num in range(start_page, min(end_page, len(reader.pages))):
                writer.add_page(reader.pages[page_num])
            
            output_buffer = io.BytesIO()
            writer.write(output_buffer)
            return output_buffer.getvalue()
    except Exception as e:
        print(f"⚠️ Errore creazione chunk PDF: {e}. Uso PDF completo.")
        with open(pdf_path, 'rb') as f:
            return f.read()


def create_document_chunks(pdf_path: str,
                          document_name: str,
                          document_type: str = "slides",
                          max_words_per_chunk: Optional[int] = None,
                          use_estimation: bool = True,
                          fallback_pages_per_chunk: int = 10) -> List[Dict]:
    """
    Divide PDF in chunks basati su conteggio parole.
    document_type: "slides" o "notes" (determina il comportamento del LLM)
    use_estimation=True (default): stima veloce campionando prime 10 pagine
    use_estimation=False: conta esatto (lento, per PDF piccoli)
    Returns: [{"text": str, "files": [types.Part], "doc_type": str}]
    """
    if max_words_per_chunk is None:
        max_words_per_chunk = config.get('documents.max_words_per_chunk', 20000)
    
    chunks = []
    
    if PyPDF2 is None:
        print(f"⚠️ Chunking semplice per {document_name} (PyPDF2 non installato)")
        
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        pdf_part = types.Part.from_bytes(data=pdf_data, mime_type='application/pdf')
        
        chunks.append({
            "text": f"DOCUMENTO: {document_name}\nAnalizza questo documento e genera appunti strutturati.",
            "files": [pdf_part],
            "doc_type": document_type
        })
        return chunks
    
    if use_estimation:
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)
            
            if total_pages == 0:
                raise ValueError(f"PDF vuoto: {pdf_path}")
            
            words_per_page = estimate_words_per_page(pdf_path, sample_pages=10)
            pages_per_chunk = max(1, int(max_words_per_chunk / words_per_page))
            
            chunk_num = 1
            for start_page in range(0, total_pages, pages_per_chunk):
                end_page = min(start_page + pages_per_chunk, total_pages)
                
                chunk_pdf_bytes = create_pdf_chunk_from_pages(pdf_path, start_page, end_page)
                pdf_part = types.Part.from_bytes(data=chunk_pdf_bytes, mime_type='application/pdf')
                
                estimated_words = int((end_page - start_page) * words_per_page)
                page_range = f"pagine {start_page + 1}-{end_page}"
                
                chunks.append({
                    "text": (
                        f"DOCUMENTO: {document_name} (CHUNK {chunk_num})\n"
                        f"Contenuto: {page_range} (~{estimated_words} parole stimate)\n"
                        f"Analizza questo segmento e genera appunti strutturati."
                    ),
                    "files": [pdf_part],
                    "doc_type": document_type
                })
                
                chunk_num += 1
            
            print(f"📄 {document_name}: {total_pages} pagine → {len(chunks)} chunks (~{int(words_per_page)} parole/pag, stima veloce)")
            return chunks
            
        except Exception as e:
            print(f"⚠️ Errore campionamento per {document_name}: {e}. Uso fallback.")
            use_estimation = False
    
    try:
        page_texts = extract_text_from_pdf(pdf_path)
        total_pages = len(page_texts)
        
        if total_pages == 0:
            raise ValueError(f"PDF vuoto o illeggibile: {pdf_path}")
        
        current_chunk_start = 0
        current_word_count = 0
        chunk_num = 1
        
        for page_num in range(total_pages):
            page_word_count = count_words(page_texts[page_num])
            
            if current_word_count + page_word_count > max_words_per_chunk and current_word_count > 0:
                chunk_pdf_bytes = create_pdf_chunk_from_pages(pdf_path, current_chunk_start, page_num)
                pdf_part = types.Part.from_bytes(data=chunk_pdf_bytes, mime_type='application/pdf')
                
                page_range = f"pagine {current_chunk_start + 1}-{page_num}"
                chunks.append({
                    "text": (
                        f"DOCUMENTO: {document_name} (CHUNK {chunk_num})\n"
                        f"Contenuto: {page_range} ({current_word_count} parole)\n"
                        f"Analizza questo segmento e genera appunti strutturati."
                    ),
                    "files": [pdf_part],
                    "doc_type": document_type
                })
                
                current_chunk_start = page_num
                current_word_count = page_word_count
                chunk_num += 1
            else:
                current_word_count += page_word_count
        
        if current_chunk_start < total_pages:
            chunk_pdf_bytes = create_pdf_chunk_from_pages(pdf_path, current_chunk_start, total_pages)
            pdf_part = types.Part.from_bytes(data=chunk_pdf_bytes, mime_type='application/pdf')
            
            page_range = f"pagine {current_chunk_start + 1}-{total_pages}"
            chunks.append({
                "text": (
                    f"DOCUMENTO: {document_name} (CHUNK {chunk_num})\n"
                    f"Contenuto: {page_range} ({current_word_count} parole)\n"
                    f"Analizza questo segmento e genera appunti strutturati."
                ),
                "files": [pdf_part],
                "doc_type": document_type
            })
        
        total_words = sum(count_words(t) for t in page_texts)
        print(f"📄 {document_name}: {total_pages} pagine, {total_words} parole → {len(chunks)} chunks (conteggio preciso)")
        return chunks
        
    except Exception as e:
        print(f"⚠️ Errore chunking per {document_name}: {e}")
        print(f"   Fallback: uso PDF completo in 1 chunk")
        
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        pdf_part = types.Part.from_bytes(data=pdf_data, mime_type='application/pdf')
        
        return [{
            "text": f"DOCUMENTO: {document_name}\nAnalizza questo documento e genera appunti strutturati.",
            "files": [pdf_part],
            "doc_type": document_type
        }]


def estimate_words_per_page(pdf_path: str, sample_pages: int = 10) -> float:
    """Stima media parole/pagina campionando prime N pagine (default: 10)"""
    if PyPDF2 is None:
        return 300.0  # Stima conservativa
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)
            
            if total_pages == 0:
                return 0.0
            
            pages_to_sample = min(sample_pages, total_pages)
            total_words = 0
            
            for page_num in range(pages_to_sample):
                page = reader.pages[page_num]
                text = page.extract_text()
                total_words += count_words(text)
            
            avg_words = total_words / pages_to_sample
            return avg_words
            
    except Exception as e:
        print(f"⚠️ Errore stima parole/pagina: {e}. Uso stima default.")
        return 300.0  # Fallback


def merge_sources(video_transcript: List[Dict] = None,
                 video_keyframes: List[Dict] = None,
                 pdf_chunks: List[Dict] = None) -> Tuple[List[Dict], str, str]:
    """Unifica video + PDF in formato comune. Returns: (chunks, description, input_mode)
    
    input_mode può essere:
    - 'video': solo video o video + qualsiasi PDF
    - 'only_slides': solo PDF di tipo slides
    - 'only_notes': solo PDF di tipo notes (appunti da trascrivere)
    - 'mixed_pdf': mix di slides + notes senza video
    """
    if not any([video_transcript, pdf_chunks]):
        raise ValueError("Almeno una fonte deve essere fornita (video o PDF)")
    
    unified_chunks = []
    sources = []
    has_video = False
    
    if video_transcript and video_keyframes:
        from llm_gen_engine import create_chunks
        video_chunks = create_chunks(
            video_transcript, 
            video_keyframes, 
            chunk_duration_sec=config.chunk_duration_sec
        )
        
        for chunk in video_chunks:
            unified_chunks.append({
                "text": chunk["text"],
                "images": chunk["images"],
                "files": []
            })
        sources.append("videolezione")
        has_video = True
    
    pdf_types_present = set()
    if pdf_chunks:
        for chunk in pdf_chunks:
            unified_chunks.append({
                "text": chunk["text"],
                "images": [],
                "files": chunk["files"],
                "doc_type": chunk.get("doc_type", "slides")
            })
            pdf_types_present.add(chunk.get("doc_type", "slides"))
        sources.append("documenti PDF")
    
    source_description = " + ".join(sources)
    
    # Determina modalità di input
    if has_video:
        input_mode = "video"
    elif "notes" in pdf_types_present and "slides" not in pdf_types_present:
        input_mode = "only_notes"
    elif "slides" in pdf_types_present and "notes" not in pdf_types_present:
        input_mode = "only_slides"
    elif pdf_chunks:
        input_mode = "mixed_pdf"
    else:
        input_mode = "video"
    
    return unified_chunks, source_description, input_mode


def process_documents(pdf_paths: List[str], 
                     document_types: List[str] = None,
                     max_words_per_chunk: Optional[int] = None) -> List[Dict]:
    """Processa multipli PDF con chunking intelligente. Returns: chunks pronti per generate_notes()"""
    if document_types is None:
        document_types = ["slides"] * len(pdf_paths)
    
    if len(pdf_paths) != len(document_types):
        raise ValueError("Numero di PDF e tipi devono coincidere")
    
    all_chunks = []
    
    # Processa ogni PDF singolarmente con chunking intelligente
    for pdf_path, doc_type in zip(pdf_paths, document_types):
        doc_name = os.path.basename(pdf_path)
        
        pdf_chunks = create_document_chunks(
            pdf_path=pdf_path,
            document_name=f"{doc_name} ({doc_type})",
            document_type=doc_type,
            max_words_per_chunk=max_words_per_chunk
        )
        
        all_chunks.extend(pdf_chunks)
    
    return all_chunks
