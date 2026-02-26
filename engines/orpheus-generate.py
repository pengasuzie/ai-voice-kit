#!/usr/bin/env python3
"""
Orpheus TTS — standalone local generation (no server required).
Uses llama-cpp-python to load the GGUF model directly, decodes audio tokens with SNAC.

Usage:
    python orpheus-generate.py --text "Hello world" --voice tara --output output.wav
    python orpheus-generate.py --file input.txt --voice leah --output output.wav
    python orpheus-generate.py --list-voices
"""

import argparse
import os
import sys
import time
import wave
import numpy as np
import torch
from snac import SNAC

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(SCRIPT_DIR, "orpheus-3b-0.1-ft-q4_k_m.gguf")
SAMPLE_RATE = 24000
MAX_TOKENS = 8192
TEMPERATURE = 0.6
TOP_P = 0.9
REPETITION_PENALTY = 1.1

AVAILABLE_VOICES = ["tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe"]
DEFAULT_VOICE = "tara"

START_TOKEN_ID = 128259
END_TOKEN_IDS = {128009, 128260, 128261, 128257}
CUSTOM_TOKEN_PREFIX = "<custom_token_"


def load_snac():
    """Load SNAC decoder model on best available device."""
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"SNAC device: {device}")
    model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval().to(device)
    return model, device


def load_llm(model_path):
    """Load the Orpheus GGUF model via llama-cpp-python."""
    from llama_cpp import Llama

    print(f"Loading model: {os.path.basename(model_path)}")
    llm = Llama(
        model_path=model_path,
        n_ctx=8192,
        n_gpu_layers=-1,  # Use Metal on Mac
        verbose=False,
    )
    return llm


def format_prompt(text, voice):
    """Format text with voice prefix and special tokens."""
    return f"<|audio|>{voice}: {text}<|eot_id|>"


def turn_token_into_id(token_string, index):
    """Convert a custom token string to a numeric ID."""
    token_string = token_string.strip()
    last_start = token_string.rfind(CUSTOM_TOKEN_PREFIX)
    if last_start == -1:
        return None
    last_token = token_string[last_start:]
    if last_token.startswith(CUSTOM_TOKEN_PREFIX) and last_token.endswith(">"):
        try:
            number_str = last_token[14:-1]
            return int(number_str) - 10 - ((index % 7) * 4096)
        except ValueError:
            return None
    return None


def convert_to_audio(snac_model, device, multiframe):
    """Decode a buffer of token IDs into raw audio bytes via SNAC."""
    if len(multiframe) < 7:
        return None

    codes_0 = torch.tensor([], device=device, dtype=torch.int32)
    codes_1 = torch.tensor([], device=device, dtype=torch.int32)
    codes_2 = torch.tensor([], device=device, dtype=torch.int32)

    num_frames = len(multiframe) // 7
    frame = multiframe[:num_frames * 7]

    for j in range(num_frames):
        i = 7 * j
        codes_0 = torch.cat([codes_0, torch.tensor([frame[i]], device=device, dtype=torch.int32)])
        codes_1 = torch.cat([codes_1, torch.tensor([frame[i + 1]], device=device, dtype=torch.int32)])
        codes_1 = torch.cat([codes_1, torch.tensor([frame[i + 4]], device=device, dtype=torch.int32)])
        codes_2 = torch.cat([codes_2, torch.tensor([frame[i + 2]], device=device, dtype=torch.int32)])
        codes_2 = torch.cat([codes_2, torch.tensor([frame[i + 3]], device=device, dtype=torch.int32)])
        codes_2 = torch.cat([codes_2, torch.tensor([frame[i + 5]], device=device, dtype=torch.int32)])
        codes_2 = torch.cat([codes_2, torch.tensor([frame[i + 6]], device=device, dtype=torch.int32)])

    codes = [codes_0.unsqueeze(0), codes_1.unsqueeze(0), codes_2.unsqueeze(0)]

    # Validate token ranges
    for c in codes:
        if torch.any(c < 0) or torch.any(c > 4096):
            return None

    with torch.inference_mode():
        audio_hat = snac_model.decode(codes)

    audio_slice = audio_hat[:, :, 2048:4096]
    audio_np = audio_slice.detach().cpu().numpy()
    audio_int16 = (audio_np * 32767).astype(np.int16)
    return audio_int16.tobytes()


def generate_speech(llm, snac_model, snac_device, text, voice, output_path):
    """Generate speech from text and save as WAV."""
    prompt = format_prompt(text, voice)
    print(f"Generating: {voice}: {text[:80]}{'...' if len(text) > 80 else ''}")

    # Tokenize the prompt
    tokens = llm.tokenize(prompt.encode("utf-8"), special=True)

    # Generate tokens
    buffer = []
    count = 0
    audio_segments = []
    audio_started = False

    start_time = time.time()

    for token_obj in llm.generate(tokens, top_p=TOP_P, temp=TEMPERATURE, repeat_penalty=REPETITION_PENALTY):
        # The model emits a few preamble tokens (128257, 128260, 128261) before
        # audio starts. Only treat them as end tokens once we've seen real audio.
        if token_obj in END_TOKEN_IDS:
            if audio_started:
                break
            else:
                continue

        # Decode the token to text
        token_text = llm.detokenize([token_obj]).decode("utf-8", errors="ignore")

        token_id = turn_token_into_id(token_text, count)
        if token_id is not None and token_id > 0:
            buffer.append(token_id)
            count += 1
            audio_started = True

            # Decode audio when we have enough tokens
            if count % 7 == 0 and count > 27:
                buffer_to_proc = buffer[-28:]
                audio_bytes = convert_to_audio(snac_model, snac_device, buffer_to_proc)
                if audio_bytes is not None:
                    audio_segments.append(audio_bytes)

        if count >= MAX_TOKENS:
            break

    elapsed = time.time() - start_time

    if not audio_segments:
        print("Error: No audio generated")
        return False

    # Write WAV
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        for seg in audio_segments:
            wf.writeframes(seg)

    duration = sum(len(s) // 2 for s in audio_segments) / SAMPLE_RATE
    print(f"  {duration:.1f}s audio in {elapsed:.1f}s → {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Orpheus TTS — local generation")
    parser.add_argument("--text", type=str, help="Text to synthesize")
    parser.add_argument("--file", type=str, help="Text file to synthesize")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE,
                        help=f"Voice (default: {DEFAULT_VOICE})")
    parser.add_argument("--output", type=str, default="output.wav",
                        help="Output WAV path (default: output.wav)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_PATH,
                        help="Path to GGUF model file")
    parser.add_argument("--list-voices", action="store_true", help="List voices")
    args = parser.parse_args()

    if args.list_voices:
        print("Available voices: " + ", ".join(AVAILABLE_VOICES))
        print(f"Default: {DEFAULT_VOICE}")
        print("\nEmotion tags: <laugh> <chuckle> <sigh> <gasp> <yawn> <groan> <cough> <sniffle>")
        return

    text = args.text
    if args.file:
        with open(args.file, "r") as f:
            text = f.read().strip()
    if not text:
        print("Error: Provide --text or --file")
        sys.exit(1)

    if args.voice not in AVAILABLE_VOICES:
        print(f"Unknown voice '{args.voice}'. Available: {', '.join(AVAILABLE_VOICES)}")
        sys.exit(1)

    # Load models
    snac_model, snac_device = load_snac()
    llm = load_llm(args.model)

    # Generate
    generate_speech(llm, snac_model, snac_device, text, args.voice, args.output)


if __name__ == "__main__":
    main()
