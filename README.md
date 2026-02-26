# ai-voice-kit

Local AI voice tools for Claude Code. Text-to-speech with 50 voices, audio transcription with speaker identification, and strategic analysis that bridges the two. No cloud APIs, everything runs on your machine.

## What's in the box

Three Claude Code skills that work standalone or chained together:

| Skill | Command | What it does |
|-------|---------|-------------|
| **Voice to Text** | `/voice-to-text meeting.m4a` | Transcribes audio with speaker identification |
| **Strategic Analysis** | `/strategic-analysis transcript.txt` | Analyzes meetings with full project context, produces voice-ready output |
| **Text to Voice** | `/text-to-voice analysis-voice.txt` | Converts any text file to MP3 using Kokoro TTS |

**The full chain:** record a meeting, transcribe it, get a strategic analysis with action items, then listen to the briefing as audio on your commute.

```
Voice memo → /voice-to-text → transcript
                                  ↓
                         /strategic-analysis → analysis.md + analysis-voice.txt
                                                                   ↓
                                                          /text-to-voice → briefing.mp3
```

## Quick Start

### 1. Install the skills

Copy the skill folders into your Claude Code skills directory:

```bash
# Clone the repo
git clone https://github.com/pengasuzie/ai-voice-kit.git

# Copy skills to your Claude Code config
cp -r ai-voice-kit/skills/text-to-voice ~/.claude/skills/
cp -r ai-voice-kit/skills/voice-to-text ~/.claude/skills/
cp -r ai-voice-kit/skills/strategic-analysis ~/.claude/skills/
```

### 2. Install Kokoro TTS

Kokoro is the default TTS engine. Fast (seconds per clip), 50 voices, runs locally.

```bash
# Install the CLI
pipx install kokoro-tts

# Create model directory
mkdir -p ~/.local/share/kokoro

# Download model files (~350 MB total)
curl -L -o ~/.local/share/kokoro/kokoro-v1.0.onnx \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx

curl -L -o ~/.local/share/kokoro/voices-v1.0.bin \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

### 3. Install ffmpeg

Required for WAV to MP3 conversion:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 4. Use it

Open Claude Code and run:

```
> /text-to-voice path/to/your-text.txt
```

That's it. You'll get an MP3 file in seconds.

## Text to Voice

### Basic usage

```
> /text-to-voice meeting-notes.txt
```

The skill will:
1. Read the file and estimate duration
2. Ask which engine (defaults to Kokoro)
3. Generate WAV, convert to MP3
4. Report the output path, duration, and file size

### Markdown input

If you pass a `.md` file, the skill automatically converts it to speech-friendly text:
- Strips formatting (headings, bold, bullets, tables)
- Converts lists to flowing prose
- Expands acronyms for Kokoro (AI → A.I., API → A.P.I.)
- Adds natural transition phrases

### Voices

Kokoro ships with 50 voices. The default is `bf_lily` (British female).

**American English:**
- Female: `af_heart`, `af_bella`, `af_sarah`, `af_nova`
- Male: `am_adam`, `am_michael`, `am_eric`, `am_liam`

**British English:**
- Female: `bf_emma`, `bf_lily`, `bf_isabella`
- Male: `bm_george`, `bm_daniel`, `bm_lewis`

List all voices: `kokoro-tts --help-voices`

### Alternative engines

The skill supports two additional engines for different use cases:

| Engine | Speed | Install | Best for |
|--------|-------|---------|----------|
| **Kokoro** (default) | Seconds | `pipx install kokoro-tts` | Daily use, bulk generation |
| **Orpheus** | ~3.5x real-time | See [Orpheus setup](#orpheus-setup) | Natural prosody, emotion tags |
| **Coqui XTTS v2** | ~1x real-time | See [Coqui setup](#coqui-setup) | Voice cloning from any WAV |

## Voice to Text

### Setup

```bash
# Install whisperX
pipx install "whisperx @ git+https://github.com/m-bain/whisperX.git" --python python3.13

# Log in to Hugging Face (needed for speaker diarization)
~/.local/pipx/venvs/whisperx/bin/huggingface-cli login
```

You also need to accept the model terms:
- https://huggingface.co/pyannote/speaker-diarization-3.1
- https://huggingface.co/pyannote/segmentation-3.0

### Basic usage

```
> /voice-to-text meeting-recording.m4a
```

The skill will:
1. Transcribe the audio using Whisper
2. Identify and label speakers
3. Output a clean transcript
4. Offer to replace generic labels (SPEAKER_00) with real names

Supports: `.m4a`, `.mp3`, `.wav`, `.flac`, `.ogg`, `.webm`, `.mp4`, `.mkv`, `.avi`

## Strategic Analysis

The middle skill in the chain. It reads a transcript (or any document), gathers context from your project directory, and produces two outputs:

- `analysis.md` — full strategic analysis in markdown
- `analysis-voice.txt` — TTS-optimized plain text, ready for `/text-to-voice`

### Four analysis modes

| Mode | Best for |
|------|----------|
| **Sales Deal Analysis** | Win probability, feature fit, competitive threats, next actions |
| **Consulting Engagement** | What the client actually needs, AI opportunity map, engagement approach |
| **Competitive / Market Signal** | Intelligence extraction, positioning, market trends |
| **Meeting Debrief** | Clean summary, decisions, action items, open questions |

### Project-aware

The skill automatically reads your project's `CLAUDE.md`, docs, notes, competitor files, and git history before analyzing. This means the analysis is grounded in everything you know about the client, not just the transcript.

### Basic usage

```
> /strategic-analysis transcript.txt

What type of analysis?
1. Sales Deal Analysis
2. Consulting Engagement Analysis
3. Competitive / Market Signal Analysis
4. Meeting Debrief

> 2

Gathering project context...
Reading CLAUDE.md, 3 docs, 2 competitor files...
Analyzing transcript (4,231 words, 2 speakers)...

Output:
├── analysis.md            (strategic analysis)
└── analysis-voice.txt     (TTS-ready, for /text-to-voice)
```

## Examples

### Daily briefing from notes

```
> /text-to-voice meeting-notes.md

Reading meeting-notes.md... 847 words, ~4 min audio.
Converting markdown to speech text...
Generating with Kokoro (voice: bf_lily)...

Output:
├── meeting-notes.mp3     (audio — 4m 12s, 3.8 MB)
└── Engine: Kokoro, Voice: bf_lily
```

### Full chain: meeting to audio briefing

```
# Step 1: Transcribe the recording
> /voice-to-text client-call.m4a

Transcribing... 2 speakers detected.
Output: client-call.txt (4,231 words)

# Step 2: Analyze the meeting
> /strategic-analysis client-call.txt

> 2  (Consulting Engagement)

Gathering project context...
Output:
├── analysis.md            (strategic analysis)
└── analysis-voice.txt     (TTS-ready)

# Step 3: Generate the audio briefing
> /text-to-voice analysis-voice.txt

Output:
├── analysis-voice.mp3     (audio — 6m 18s, 5.7 MB)
└── Engine: Kokoro, Voice: bf_lily
```

Listen to your briefing on the drive home.

## Optional Engine Setup

### Orpheus Setup

Orpheus uses llama-cpp for natural-sounding speech with emotion tags.

```bash
mkdir -p ~/.local/share/orpheus-tts
cd ~/.local/share/orpheus-tts

# Create venv and install deps
python3.12 -m venv venv
./venv/bin/pip install llama-cpp-python soundfile numpy

# Download the model (~2.4 GB)
curl -L -o orpheus-3b-0.1-ft-q4_k_m.gguf \
  https://huggingface.co/lex-hue/Orpheus-3b-0.1-ft-GGUF/resolve/main/orpheus-3b-0.1-ft-q4_k_m.gguf

# Copy the generate script from this repo
cp ai-voice-kit/engines/orpheus-generate.py .
```

Orpheus supports emotion tags: `<laugh>`, `<sigh>`, `<gasp>`, `<chuckle>`, `<yawn>`

### Coqui Setup

Coqui XTTS v2 clones voices from a 6-second WAV sample.

```bash
mkdir -p ~/.local/share/coqui-tts
cd ~/.local/share/coqui-tts

# Create venv and install
python3.12 -m venv venv
./venv/bin/pip install TTS

# Copy the generate script from this repo
cp ai-voice-kit/engines/coqui-generate.py .
```

**Note:** Coqui's model license is non-commercial. The model (~1.9 GB) auto-downloads on first run.

## How it works

```
Text file → Kokoro TTS → WAV → ffmpeg → MP3
                ↑
        50 voices, runs locally
        No API key needed

Audio file → whisperX → Transcript with speakers
                ↑
         Runs locally, ~360MB model
         Speaker diarization via pyannote
```

## Requirements

- macOS (Apple Silicon recommended) or Linux
- Python 3.12+
- pipx (`brew install pipx`)
- ffmpeg (`brew install ffmpeg`)
- Claude Code (for the `/slash-command` interface)

## License

MIT
