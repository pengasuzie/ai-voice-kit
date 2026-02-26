#!/usr/bin/env python3
"""
Coqui XTTS v2 — voice cloning TTS wrapper.

Usage:
    python coqui-generate.py --text "Hello world" --speaker-wav sample.wav --output output.wav
    python coqui-generate.py --file input.txt --speaker-wav sample.wav --output output.wav
    python coqui-generate.py --list-speakers
"""

import argparse
import os
import sys
import time

def main():
    parser = argparse.ArgumentParser(description="Coqui XTTS v2 — voice cloning TTS")
    parser.add_argument("--text", type=str, help="Text to synthesize")
    parser.add_argument("--file", type=str, help="Text file to synthesize")
    parser.add_argument("--speaker-wav", type=str, required=True,
                        help="Reference audio WAV for voice cloning (6+ seconds)")
    parser.add_argument("--output", type=str, default="output.wav",
                        help="Output WAV path (default: output.wav)")
    parser.add_argument("--language", type=str, default="en",
                        help="Language code (default: en)")
    parser.add_argument("--list-speakers", action="store_true",
                        help="Note: XTTS v2 uses voice cloning, not preset speakers")
    args = parser.parse_args()

    if args.list_speakers:
        print("XTTS v2 uses voice cloning — provide any WAV file as --speaker-wav")
        print("Supported languages: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh, ja, hu, ko, hi")
        return

    text = args.text
    if args.file:
        with open(args.file, "r") as f:
            text = f.read().strip()
    if not text:
        print("Error: Provide --text or --file")
        sys.exit(1)

    if not os.path.exists(args.speaker_wav):
        print(f"Error: Speaker WAV not found: {args.speaker_wav}")
        sys.exit(1)

    # Import here so --help and --list-speakers are fast
    import torch
    from TTS.api import TTS

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Device: {device}")
    print(f"Loading XTTS v2 model...")

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    print(f"Generating: {text[:80]}{'...' if len(text) > 80 else ''}")
    start = time.time()

    tts.tts_to_file(
        text=text,
        speaker_wav=args.speaker_wav,
        language=args.language,
        file_path=args.output,
    )

    elapsed = time.time() - start
    size_kb = os.path.getsize(args.output) // 1024
    print(f"  {elapsed:.1f}s → {args.output} ({size_kb} KB)")


if __name__ == "__main__":
    main()
