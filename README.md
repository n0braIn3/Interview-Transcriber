# Chatbot – Interview-Bot mit Spracheingabe

Ein Chainlit-basierter Chatbot, der automatisiert Interviews führen kann – sowohl per **Texteingabe** als auch per **Spracheingabe** (Mikrofon → OpenAI Whisper → GPT-4o).

---

## Voraussetzungen

- **Python 3.10+** (getestet mit 3.13)
- **OpenAI API-Key** (für GPT-4o und Whisper)
- **Mikrofon** (für Spracheingabe)
- **Browser**: Chrome oder Edge empfohlen (Firefox hat teilweise Probleme mit der Audio-API)

---

## Installation

### 1. Repository/Ordner herunterladen

Den gesamten `chatbot`-Ordner herunterladen oder klonen.

### 2. Virtuelle Umgebung erstellen & aktivieren

```bash
# Virtuelle Umgebung erstellen
python -m venv venv

# Aktivieren (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Aktivieren (Windows CMD)
.\venv\Scripts\activate.bat

# Aktivieren (macOS / Linux)
source venv/bin/activate
```

### 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 4. API-Key konfigurieren

Eine Datei namens `.env` im Projektordner erstellen (oder die vorhandene anpassen) mit folgendem Inhalt:

```
OPENAI_API_KEY=sk-proj-DEIN_API_KEY_HIER
```

> ⚠️ **Wichtig:** Den API-Key **niemals** in den Code schreiben oder per Chat/E-Mail versenden. Immer über die `.env`-Datei konfigurieren.

---

## Starten

```bash
chainlit run chatbot.py
```

Der Server startet auf **http://localhost:8000** – diese URL im Browser öffnen.

---

## Nutzung

| Funktion          | Wie                                                                                     |
| ----------------- | --------------------------------------------------------------------------------------- |
| **Texteingabe**   | Nachricht ins Textfeld tippen und Enter drücken                                         |
| **Spracheingabe** | Mikrofon-Button klicken (oder `P` drücken), sprechen, Button erneut klicken zum Stoppen |

Bei der Spracheingabe wird das Audio automatisch per OpenAI Whisper transkribiert und die Antwort per GPT-4o generiert.

---

## Projektstruktur

```
chatbot/
├── chatbot.py              # Hauptprogramm
├── requirements.txt        # Python-Abhängigkeiten
├── .env                    # API-Key (NICHT weitergeben!)
├── .chainlit/
│   └── config.toml         # Chainlit-Konfiguration (Audio aktiviert)
└── chainlit.md             # Willkommensseite im Chat
```

---

## Changelog

### 24.02.2026
1. Doppelten `@cl.on_audio_chunk`-Block (leer, mit `pass`) entfernt – hat Audio-Logik blockiert
2. `[features.audio] enabled = true` in `.chainlit/config.toml` gesetzt – Mikrofon-Button war deaktiviert
3. `audioop.rms()` durch numpy-basierte `compute_rms()` ersetzt – `audioop` in Python 3.13 entfernt
4. `@cl.on_audio_end`-Handler hinzugefügt – Chainlit 2.x erwartet diesen, sonst `NoneType`-Error
5. Audio-Datei mit Filename an Whisper API übergeben (`("audio.wav", buffer, "audio/wav")`) – sonst `Unrecognized file format`
6. API-Key aus Code in `.env`-Datei verschoben – Sicherheitsrisiko behoben
7. Unbenutzte Imports entfernt (`audioop`, `httpx`)
