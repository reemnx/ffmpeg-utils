import os
import sys
import re
import subprocess
import shutil
from openai import OpenAI
from dotenv import load_dotenv

def get_audio_duration(file_path):
    """
    Returns the duration of an audio file in seconds using ffprobe.
    """
    cmd = [
        "ffprobe", 
        "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration for {file_path}: {e}")
        return None

def change_audio_speed(input_path, output_path, speed_factor):
    """
    Changes the speed of an audio file using ffmpeg atempo filter.
    """
    # ffmpeg atempo filter supports 0.5 to 2.0.
    # If speed_factor is outside this range, we need to chain filters.
    
    filters = []
    remaining_factor = speed_factor
    
    while remaining_factor > 2.0:
        filters.append("atempo=2.0")
        remaining_factor /= 2.0
    while remaining_factor < 0.5:
        filters.append("atempo=0.5")
        remaining_factor /= 0.5
    
    filters.append(f"atempo={remaining_factor}")
    filter_str = ",".join(filters)
    
    print(f"Applying speed factor {speed_factor:.2f} (Filter: {filter_str})...")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-filter:a", filter_str,
        "-vn",
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
        print(f"Speed adjusted audio saved to '{output_path}'")
    except subprocess.CalledProcessError as e:
        print(f"Error changing audio speed: {e}")

def extract_text_from_srt(srt_path):
    """
    Extracts text content from an SRT file, ignoring indices and timestamps.
    Joins the text into a single string.
    """
    print(f"Extracting text from '{srt_path}'...")
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.splitlines()
    text_parts = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.isdigit():
            continue
        if '-->' in line:
            continue
            
        text_parts.append(line)

    full_text = " ".join(text_parts)
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    return full_text

def generate_voiceover(text, output_path, model="gpt-4o-mini-tts", voice="ash"):
    """
    Generates audio from text using OpenAI API.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found.")
        return False

    client = OpenAI(api_key=api_key)

    print(f"Generating voiceover for text ({len(text)} chars)...")
    print(f"Model: {model}, Voice: {voice}")

    try:
        with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=text,
            instructions="Personality: Relatable and engaging. Language: Hebrew. Style: Casual, Millennial/Gen Z., accent: Israeli."
        ) as response:
            print(f"Saving to '{output_path}'...")
            response.stream_to_file(output_path)
        print("Done!")
        return True

    except Exception as e:
        print(f"Error generating voiceover: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_voiceover.py <input_file> [output_file] [reference_audio]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = "hebrew_voiceover.mp3"
    reference_audio = None
    
    # Basic arg parsing
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        reference_audio = sys.argv[3]
    else:
        # Try to auto-detect input_audio.mp3 if not provided
        if os.path.exists("input_audio.mp3"):
            reference_audio = "input_audio.mp3"
            print(f"Auto-detected reference audio: {reference_audio}")

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    # Determine if input is SRT or TXT
    if input_file.lower().endswith('.srt'):
        text = extract_text_from_srt(input_file)
    else:
        print(f"Reading text from '{input_file}'...")
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
            text = text.replace('\n', ' ')

    if not text:
        print("Error: No text found in input file.")
        sys.exit(1)

    # Generate initial voiceover
    temp_output = "temp_voiceover.mp3"
    success = generate_voiceover(text, temp_output)
    
    if success:
        # Check duration matching
        if reference_audio and os.path.exists(reference_audio):
            ref_duration = get_audio_duration(reference_audio)
            gen_duration = get_audio_duration(temp_output)
            
            if ref_duration and gen_duration:
                print(f"Reference duration: {ref_duration:.2f}s")
                print(f"Generated duration: {gen_duration:.2f}s")
                
                speed_factor = gen_duration / ref_duration
                print(f"Calculated speed factor: {speed_factor:.2f}")
                
                change_audio_speed(temp_output, output_file, speed_factor)
                
                # Cleanup temp
                if os.path.exists(temp_output):
                    os.remove(temp_output)
            else:
                print("Could not determine durations, using raw generated audio.")
                shutil.move(temp_output, output_file)
        else:
            print("No reference audio for duration matching. Using raw generated audio.")
            shutil.move(temp_output, output_file)
