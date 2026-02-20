# 📋 Guida alla Configurazione - AI-Studio

## Panoramica

AI-Studio utilizza un **file di configurazione centralizzato** (`config.yaml`) per gestire tutti i parametri del sistema. Questo approccio segue le **best practices** dell'ingegneria del software moderna.

## 🎯 Perché un File di Configurazione?

### Vantaggi:

1. **Separazione Codice/Configurazione**: Modifichi i parametri senza toccare il codice Python
2. **Gestione Centralizzata**: Un parametro usato in più punti si cambia una sola volta
3. **Accessibilità**: Chiunque può modificare i parametri senza conoscere Python
4. **Versionamento**: Puoi tenere diverse configurazioni per scenari diversi
5. **Sicurezza**: Le API key possono essere gestite tramite variabili d'ambiente

## 📂 Struttura del Sistema

```
AI-Studio/
├── config.yaml               # ← File di configurazione principale
├── src/
│   ├── config_loader.py      # Modulo che carica config.yaml
│   ├── llm_gen_engine.py     # Usa config per i parametri LLM
│   ├── audio_processing.py   # Usa config per Whisper e FFmpeg
│   ├── vision_processing.py  # Usa config per Computer Vision
│   └── interactive_agent.py  # Usa config per Editor e Tutor
└── requirements.txt          # Include PyYAML
```

## 🔧 Come Funziona

### 1. File di Configurazione (YAML)

Il formato **YAML** è stato scelto perché:
- È **leggibile** come testo normale
- Supporta **commenti** per documentare ogni parametro
- È lo **standard** per configurazioni (Kubernetes, Docker, GitHub Actions, ecc.)
- Supporta **strutture gerarchiche** intuitive

Esempio da `config.yaml`:
```yaml
llm:
  model_name: "gemini-2.0-flash-exp"
  writer:
    temperature: 0.5      # Precisione logica per gli appunti
    top_p: 0.8
    max_output_tokens: 45000
  editor:
    temperature: 0.3      # Severità massima per modifiche precise
```

### 2. Config Loader (Pattern Singleton)

Il file `config_loader.py` implementa il **Singleton Pattern**:
- Carica il YAML **una sola volta** all'avvio
- È accessibile da **tutti i moduli** come oggetto globale
- Fornisce **proprietà type-safe** (autocompletamento IDE)
- Supporta **variabili d'ambiente** per API keys

```python
from config_loader import config

# Accesso diretto alle proprietà
temperature = config.writer_temperature  # 0.5
model = config.model_name                # "gemini-2.0-flash-exp"
```

### 3. Variabili d'Ambiente (Sicurezza)

Per le **API keys** sensibili, usa variabili d'ambiente:

```yaml
llm:
  api_key: "${GOOGLE_API_KEY}"  # Viene sostituita automaticamente
```

Nel tuo ambiente:
```bash
# Linux/Mac
export GOOGLE_API_KEY="your-secret-key-here"

# Windows PowerShell
$env:GOOGLE_API_KEY = "your-secret-key-here"
```

## ⚙️ Parametri Configurabili

### 🤖 LLM (Large Language Model)

| Parametro | Descrizione | Default |
|-----------|-------------|---------|
| `model_name` | Modello Gemini da usare | `gemini-2.0-flash-exp` |
| `rpm` | Richieste al minuto (rate limit) | `5` |
| `writer.temperature` | Creatività nella generazione appunti | `0.5` |
| `writer.chunk_duration_sec` | Durata chunk in secondi (15min) | `900` |
| `editor.temperature` | Precisione nelle modifiche | `0.3` |
| `tutor.temperature` | Naturalità nelle risposte | `0.75` |

### 🎤 Audio Processing

| Parametro | Descrizione | Default |
|-----------|-------------|---------|
| `whisper_model_size` | Modello Whisper (`tiny`, `base`, `small`, `medium`, `large-v3`) | `large-v3` |
| `device` | Hardware (`cpu`, `cuda`) | `cuda` |
| `vad_enabled` | Voice Activity Detection attivo | `true` |
| `audio_sample_rate` | Frequenza campionamento (Hz) | `16000` |

### 👁️ Vision Processing

| Parametro | Descrizione | Default |
|-----------|-------------|---------|
| `change_threshold` | % schermo che deve cambiare (0.0-1.0) | `0.03` (3%) |
| `blur_kernel_size` | Dimensione kernel GaussianBlur | `21` |
| `pixel_threshold` | Soglia cambiamento pixel (0-255) | `25` |

## 🚀 Come Usare

### Scenario 1: Cambiare Modello LLM

Invece di modificare 3+ file Python, editi **una riga** in `config.yaml`:

```yaml
llm:
  model_name: "gemini-2.0-flash-exp"  # Cambia qui
```

### Scenario 2: Ottimizzare per GPU Meno Potente

```yaml
audio:
  whisper_model_size: "medium"  # Invece di large-v3
  compute_type: "int8"          # Invece di float16
```

### Scenario 3: Aumentare RPM (Account Pro)

```yaml
llm:
  rpm: 15  # Account Pro Gemini supporta 15 RPM
```

