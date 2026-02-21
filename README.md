# AI-Studio 🎓

*(🇬🇧 English version below | 🇮🇹 Versione italiana in basso)*

---

## 🇬🇧 English

**AI-Studio** is an open-source software developed to automate the conversion of university video lectures into structured LaTeX notes. The system processes the audio track and the visual stream (slides/whiteboard) in parallel, generating an academic document that is coherent with your pre-existing study materials.

### Technical Manual: Architecture and Workflow

The core of the system is based on a modular architecture divided into sequential processing phases.

The pipeline begins with **Audio Extraction and Speech-to-Text processing**. To optimize computation times, a Voice Activity Detection (VAD) module identifies and discards silences, transcribing only the actual speech segments. In parallel, the video stream undergoes **Computer Vision Analysis**: a keyframing script extracts frames only when significant visual changes occur (e.g., a slide transition or new equations on a whiteboard). These frames are then perfectly synchronized with the audio timestamps.

Semantic processing and LaTeX formatting are handled by an **Advanced Multimodal LLM**. The model receives the chronologically aligned text chunks and images, generating the LaTeX code. It is designed to extract visual/mathematical information even if not explicitly verbalized by the professor. A key feature is the **Historical Context Management**: the system parses previously provided `.tex` files to inherit custom macros, document structure, and writing style, ensuring didactic continuity and avoiding repetition of already covered concepts.

Finally, the system features a **Refactoring Module and a Virtual Tutor** operating distinctly on the same data in cache memory. This isolates user interaction: the LLM can apply targeted edits to specific sections of the generated code upon user request or answer student questions based strictly on the lecture's context, without ever reprocessing the entire multimedia workspace. These two modules optimize the entire system so that through various iterations the student can obtain the desired notes block while simultaneously asking questions to the AI tutor for comprehensive study.

### User Manual: Setup and Usage

AI-Studio is designed to be executed entirely within a cloud-based notebook environment (e.g., Google Colab), leveraging cloud GPUs for audio and vision processing without draining local hardware resources.

#### GPU Configuration in Google Colab
For optimal performance, it is **highly recommended to configure the runtime environment with T4 GPU**:
1. In the Colab menu, select **Runtime** → **Change runtime type**
2. Choose **T4 GPU** as the hardware accelerator
3. Save the settings

This configuration significantly accelerates audio transcription (Whisper) and video frame extraction.

#### Video Upload Optimization
To speed up the upload of large video files, you can compress the file using **ffmpeg** before uploading:

```bash
ffmpeg -i "lecture.mp4" -vcodec libx264 -crf 28 -preset faster -acodec aac -b:a 128k "lecture_compressed.mp4"
```

**Replace** `"lecture.mp4"` and `"lecture_compressed.mp4"` with the appropriate names of your files. This command significantly reduces file size while maintaining sufficient quality for transcription and frame extraction. 

To start generating notes, no external cloud storage is required. Users simply provide the video via direct temporary upload or URL. For lectures hosted on protected university portals, server-side downloading is supported by uploading a simple `cookies.txt` file extracted from the user's browser. During this preliminary phase, it is highly recommended to also upload the `.tex` file of previous notes to align the writing style and obtain a result consistent with the notes already taken during past lectures of the course under study.

Once the generation process is complete, an interactive review interface opens. Here, the user can inspect the output and use two tools: **Editor Mode**, to issue rewrite commands on specific LaTeX paragraphs, and **Tutor Mode**, to ask direct questions about the content explained by the professor. 

When the final document is ready, the `.tex` file is automatically downloaded to the user's local computer. At the end of the session, all temporary files are destroyed by Google's hosting servers, ensuring privacy and cleanliness.

### Project Structure

The repository is organized to separate the core engine from the user interface and the AI instructions:

* `config.yaml`: **Centralized configuration file** - All system parameters (LLM, audio, vision) can be configured here without modifying the code.
* `src/`: Contains the core Python modules.
  * `config_loader.py`: Manages configuration loading and access.
  * `audio_processing.py`: Handles audio extraction, VAD, and transcription.
  * `vision_processing.py`: Handles video stream analysis and dynamic keyframe extraction.
  * `llm_engine.py`: Manages the API calls to the multimodal LLM and data synchronization.
  * `interactive_agent.py`: Manages the Editor and Tutor logic using cached memory.
* `prompts/`: Isolated `.txt` files containing the system instructions and behavioral rules for the LLM.
* `notebooks/`: The executable cloud notebook (`.ipynb`) containing the user interface.
* `requirements.txt`: Project dependencies and required libraries.
* `CONFIGURATION_GUIDE.md`: Detailed guide to the configuration system.

### Configuration

AI-Studio uses a **centralized configuration system** based on YAML files. This allows you to:
- Modify LLM parameters (temperature, model, rate limits) without touching the code
- Customize audio processing (Whisper model, VAD, sample rate)
- Adjust computer vision (change threshold, blur, sensitivity)
- Manage API keys through environment variables for security

For complete details, see [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md).

### License
This software is distributed under the **GNU GPL v3** license. It is free and open-source.

---

## 🇮🇹 Italiano

**AI-Studio** è un software open source sviluppato per automatizzare la conversione di videolezioni universitarie in appunti strutturati in formato LaTeX. Il sistema elabora parallelamente la traccia audio e il flusso visivo delle presentazioni o della proiezione video, generando un documento accademico coerente con i materiali di studio preesistenti.

### Manuale Tecnico: Architettura e Funzionamento

Il cuore del sistema si basa su un'architettura modulare suddivisa in diverse fasi di elaborazione. 

La pipeline inizia con l'**Estrazione Audio e il processo di Speech-to-Text**. Per ottimizzare i tempi di calcolo, un modulo di Voice Activity Detection (VAD) identifica e scarta automaticamente i silenzi, passando alla trascrizione solo i segmenti di parlato effettivo. Parallelamente, il flusso video viene analizzato tramite tecniche di **Computer Vision**: uno script estrae i fotogrammi chiave solo in presenza di variazioni visive significative (es. cambio slide o nuove equazioni alla lavagna). Questi fotogrammi vengono poi sincronizzati con i timestamp temporali della trascrizione audio.

L'elaborazione semantica e la formattazione in LaTeX sono affidate a un **LLM Multimodale avanzato**. Il modello riceve in input i frammenti di testo cronologicamente allineati alle rispettive immagini e genera il codice LaTeX, estraendo anche le informazioni visive o matematiche non verbalizzate dal docente. Un aspetto fondamentale dell'architettura è la **Gestione del Contesto Storico**: il sistema è in grado di parsare file `.tex` precedenti forniti in input, ereditandone le macro personalizzate, la struttura e lo stile di scrittura per garantire la massima continuità didattica ed evitare ripetizioni.

Il sistema prevede inoltre un **Modulo di Refactoring e un Tutor virtuale** che operano distintamente sui medesimi dati in memoria cache. Questo permette di isolare l'interazione: l'LLM può apportare modifiche mirate a singole sezioni del codice generato su richiesta dell'utente o rispondere alle domande dello studente basandosi sul contesto della lezione, senza dover mai riprocessare l'intero workspace multimediale. Questi due moduli permettono di ottimizzare l'intero sistema in modo tale che con le varie iterazioni lo studente possa ottenere il blocco appunti desiderato e possa contestualmente porgere delle domande al tutor AI per uno studio completo.

### Manuale Utente: Setup e Utilizzo

L'utilizzo operativo di AI-Studio è progettato per avvenire all'interno di un ambiente notebook in cloud (es. Google Colab), permettendo di sfruttare l'accelerazione hardware (GPU) fornita dai server per la trascrizione e la computer vision, senza gravare sulle risorse del computer locale.

#### Configurazione GPU in Google Colab
Per ottenere prestazioni ottimali, è **fortemente consigliato configurare l'ambiente di runtime con GPU T4**:
1. Nel menu di Colab, seleziona **Runtime** → **Cambia tipo di runtime**
2. Scegli **T4 GPU** come acceleratore hardware
3. Salva le impostazioni

Questa configurazione accelera significativamente la trascrizione audio (Whisper) e l'estrazione dei frame video.

#### Ottimizzazione Upload Video
Per velocizzare il caricamento di video di grandi dimensioni, è possibile comprimere il file utilizzando **ffmpeg** prima dell'upload:

```bash
ffmpeg -i "lezione.mp4" -vcodec libx264 -crf 28 -preset faster -acodec aac -b:a 128k "lezione_compressa.mp4"
```

**Sostituisci** `"lezione.mp4"` e `"lezione_compressa.mp4"` con i nomi appropriati dei tuoi file. Questo comando riduce notevolmente le dimensioni del file mantenendo una qualità sufficiente per la trascrizione e l'estrazione dei frame. 

Per avviare la generazione degli appunti, non è necessario configurare storage cloud esterni. È sufficiente fornire in input il video della lezione tramite upload diretto temporaneo oppure inserendo un URL. Nel caso in cui la videolezione risieda su una piattaforma universitaria protetta, il download lato server è supportato caricando un semplice file `cookies.txt` estratto dal proprio browser. In questa fase preliminare è fortemente consigliato caricare anche il file `.tex` degli appunti pregressi per far allineare lo stile di scrittura e per ottenere un risultato in linea agli appunti già presi durante le lezioni passate del corso in esame.

Completata la stesura, si apre un'interfaccia di revisione interattiva. Da qui l'utente può esaminare l'output e utilizzare due strumenti: la **Modalità Editor**, per impartire comandi di riscrittura su specifici paragrafi LaTeX, e la **Modalità Tutor**, per fare domande dirette sui contenuti spiegati dal professore.

Quando il documento finale è pronto, il file `.tex` viene automaticamente scaricato sul proprio computer locale. Al termine della sessione, tutti i file temporanei vengono distrutti dai server ospitanti di Google, garantendo privacy e pulizia.

### Struttura del Progetto

Il repository è organizzato per separare il motore di elaborazione dall'interfaccia utente e dalle direttive per l'IA:

* `config.yaml`: **File di configurazione centralizzato** - Tutti i parametri del sistema (LLM, audio, vision) sono configurabili qui senza modificare il codice.
* `src/`: Contiene i moduli Python principali.
  * `config_loader.py`: Gestisce il caricamento e l'accesso alla configurazione.
  * `audio_processing.py`: Gestisce l'estrazione audio, il VAD e la trascrizione.
  * `vision_processing.py`: Gestisce l'analisi del flusso video e l'estrazione dinamica dei frame.
  * `llm_gen_engine.py`: Gestisce le chiamate API all'LLM multimodale e la sincronizzazione dei dati.
  * `interactive_agent.py`: Gestisce la logica dell'Editor e del Tutor sfruttando la cache.
* `prompts/`: File di testo (`.txt`) isolati contenenti le istruzioni di sistema e le regole comportamentali per l'LLM.
* `notebooks/`: Il notebook cloud esecutivo (`.ipynb`) che funge da interfaccia utente.
* `requirements.txt`: Dipendenze e librerie necessarie.
* `CONFIGURATION_GUIDE.md`: Guida dettagliata al sistema di configurazione.

### Configurazione

AI-Studio utilizza un **sistema di configurazione centralizzato** basato su file YAML. Questo permette di:
- Modificare parametri LLM (temperatura, modello, rate limits) senza toccare il codice
- Personalizzare audio processing (modello Whisper, VAD, sample rate)
- Regolare computer vision (threshold cambiamento, blur, sensibilità)
- Gestire API keys tramite variabili d'ambiente per sicurezza

Per dettagli completi, consulta [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md).

### Licenza
Questo software è distribuito sotto licenza **GNU GPL v3**. È libero e open source.