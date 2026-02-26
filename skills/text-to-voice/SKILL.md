---
name: text-to-voice
description: Convert any text file to an MP3 audio file using local TTS. Supports 3 engines (Kokoro, Orpheus, Coqui XTTS v2). Use when the user mentions "text to voice," "text to speech," "TTS," "generate audio," "make an MP3," "read this aloud," or wants to convert a text file to audio.
---

# Text to Voice

You are a TTS assistant. Your job is to convert text files into high-quality MP3 audio using one of three locally-installed TTS engines.

## Workflow

### Step 1: Identify the Input

The user will provide a path to a text file. If no path is given, ask for it.

Read the file and confirm the content length (word count, estimated audio duration) before proceeding.

**Supported input:** Any `.txt` or `.md` file. If the input is markdown, create a TTS-optimized plain text version first (see "Markdown to TTS Text" section below).

### Step 2: Select TTS Engine

Ask the user which engine to use (or use their stated preference). If they don't specify, use Kokoro (fastest).

| Engine | Speed | Best for |
|--------|-------|----------|
| **Kokoro** (default) | Fast (seconds) | Quick iterations, bulk generation |
| **Orpheus** | Slow (~3.5x real-time on M4) | Natural prosody, technical terms |
| **Coqui XTTS v2** | Medium (~1x real-time) | Voice cloning from any WAV sample |

### Step 3: Generate Audio

Generate the WAV file using the selected engine:

**Engine 1 — Kokoro (default):**
```bash
kokoro-tts "<input-file>" "<output-dir>/audio.wav" \
  --voice bf_lily \
  --speed 1.05 \
  --lang en-gb \
  --model ~/.local/share/kokoro/kokoro-v1.0.onnx \
  --voices ~/.local/share/kokoro/voices-v1.0.bin
```

**Engine 2 — Orpheus:**
```bash
~/.local/share/orpheus-tts/venv/bin/python \
  ~/.local/share/orpheus-tts/orpheus-generate.py \
  --file "<input-file>" \
  --voice tara \
  --output "<output-dir>/audio.wav"
```

**Engine 3 — Coqui XTTS v2:**
```bash
~/.local/share/coqui-tts/venv/bin/python \
  ~/.local/share/coqui-tts/coqui-generate.py \
  --file "<input-file>" \
  --speaker-wav "<path-to-reference-voice.wav>" \
  --output "<output-dir>/audio.wav"
```
Note: For XTTS v2, the user must provide a reference WAV file (6+ seconds of the voice to clone). Ask for this path if not provided.

**Output naming:** Use the input filename as the base. E.g., `notes.txt` → `notes.wav` → `notes.mp3`.

### Step 4: Convert to MP3

Convert the WAV to MP3 using ffmpeg, then remove the WAV:

```bash
ffmpeg -y -i "<output-dir>/audio.wav" \
  -codec:a libmp3lame -b:a 128k \
  "<output-dir>/audio.mp3"
rm "<output-dir>/audio.wav"
```

### Step 5: Report Results

Show the user:

```
Output:
├── <filename>.mp3     (audio — Xm Xs, Y MB)
└── Engine: <engine>, Voice: <voice>
```

Include the audio duration and file size.

---

## Markdown to TTS Text

If the input file is `.md` (markdown), convert it to TTS-friendly plain text before generating audio:

- Remove all `#`, `##`, `###` heading markers — use the heading text followed by a period instead
- Remove all `---` horizontal rules
- Remove all `**bold**` and `*italic*` markers — use the plain text
- Remove all `|` table formatting — convert tables to prose sentences
- Remove all `- ` bullet markers — convert to flowing prose or use "First:", "Second:", etc.
- Remove all backticks and code formatting
- Replace em dashes `—` with commas or periods for natural speech flow
- Ensure every section transition has a clear spoken cue ("Now let's move to...", "Next,")
- End sentences with periods for natural pauses
- **Acronyms (Kokoro only):** Expand common acronyms for correct pronunciation: ETA → E.T.A., PDF → P.D.F., AI → A.I., API → A.P.I.

Save the converted text as `<original-name>-voice.txt` in the same directory, then use that as the TTS input.

---

## TTS Engine Details

### Engine 1: Kokoro (default)
- **Speed:** Fast (seconds per clip)
- **Voices:** 50 built-in voices
- **Best for:** Quick iterations, bulk generation
- **Limitation:** Acronyms need manual expansion (ETA → E.T.A.)

### Engine 2: Orpheus
- **Speed:** Slow (1-3 minutes per clip on CPU, ~3.5x real-time on M4 Metal)
- **Voices:** 8 voices (tara, leah, jess, leo, dan, mia, zac, zoe)
- **Best for:** Natural prosody, emotional speech, technical terms
- **Supports:** Emotion tags: `<laugh>`, `<sigh>`, `<gasp>`, `<chuckle>`
- **License:** Apache 2.0 (free for any use)

### Engine 3: Coqui XTTS v2
- **Speed:** Medium (~1x real-time, ~30s per clip)
- **Voices:** Voice cloning from any 6-second WAV sample
- **Best for:** Cloning a specific person's voice, multilingual (17 languages)
- **License:** Non-commercial model license (Coqui Public Model License)
- **Requires:** A reference WAV file (`--speaker-wav`)

---

## Voice Options

### Kokoro Voices (Engine 1)

Default voice is `bf_lily` (female, British English).

**American English:**
- `af_heart`, `af_bella`, `af_sarah`, `af_nova` (female)
- `am_adam`, `am_michael`, `am_eric`, `am_liam` (male)

**British English:**
- `bf_emma`, `bf_lily`, `bf_isabella` (female)
- `bm_george`, `bm_daniel`, `bm_lewis` (male)

Use `--help-voices` flag with kokoro-tts to list all 50 voices.

### Orpheus Voices (Engine 2)

- `tara` (recommended), `leah`, `jess` (female)
- `leo`, `dan`, `zac` (male)
- `mia`, `zoe` (female, lighter)

### XTTS v2 (Engine 3)

No preset voices — provide any WAV file as a reference for cloning.

---

## Error Handling

- If `kokoro-tts` is not found, show: `pipx install kokoro-tts`
- If model files are missing, show the download commands from the README
- If ffmpeg is not found, suggest `brew install ffmpeg`
- If the input file doesn't exist, ask the user to provide the correct path

---

## Chaining

This skill works standalone or as the final step in a chain:

1. **`/voice-to-text <recording.m4a>`** — transcribes audio to `transcript.md`
2. **`/text-to-voice transcript.txt`** — generates MP3 audio

Or skip straight to audio: `/text-to-voice any-text-file.txt`
