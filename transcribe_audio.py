import whisper
import os
import sys
import datetime
from openai import OpenAI
from dotenv import load_dotenv

def format_timestamp(seconds):
    """Converts seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    td = datetime.timedelta(seconds=seconds)
    # Total seconds to hours, minutes, seconds, microseconds
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def translate_batch(client, texts):
    """
    Translates a list of sentences to Hebrew using GPT-4o, maintaining line-by-line correspondence.
    """
    print("Translating batch...")
    
    # Prepare the prompt
    joined_text = "\n".join(texts)
    system_prompt = (
        "You are a translator. Translate the input text to Hebrew. "
        "Use a Millennial/Gen Z style (casual, slang). "
        "CRITICAL: Do NOT use any punctuation marks. Do NOT use Nikud (vowel points). "
        "The input contains multiple lines. Return the translation as a list of lines, "
        "where each output line corresponds exactly to one input line. "
        "Do not merge or split lines."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": joined_text}
            ],
            temperature=0.7,
        )
        translated_block = response.choices[0].message.content.strip()
        translated_lines = translated_block.split('\n')
        
        # Basic validation
        if len(translated_lines) != len(texts):
            print(f"Warning: Mismatch in translation lines (Input: {len(texts)}, Output: {len(translated_lines)}). attempting to align...")
            # If slight mismatch, we might just return what we have or pad/truncate. 
            # Ideally, we want strict 1:1. 
            # For now, if mismatch, we might fallback or just proceed. 
            # Let's just return what we got, but padded if short.
            if len(translated_lines) < len(texts):
                translated_lines.extend([""] * (len(texts) - len(translated_lines)))
            else:
                translated_lines = translated_lines[:len(texts)]
                
        return translated_lines

    except Exception as e:
        print(f"Translation error: {e}")
        return texts  # Fallback to original English if translation fails

def generate_interpolated_srt(segments, translated_sentences, srt_path):
    """
    Generates an SRT file with word-level synchronization by linearly interpolating 
    the translated sentence duration.
    """
    print(f"Writing interpolated SRT to '{srt_path}'...")
    
    with open(srt_path, "w", encoding="utf-8") as f:
        srt_index = 1
        
        for segment, hebrew_text in zip(segments, translated_sentences):
            start_time = segment["start"]
            end_time = segment["end"]
            duration = end_time - start_time
            
            # Split Hebrew text into words
            words = hebrew_text.strip().split()
            if not words:
                continue
            
            # Calculate duration per word
            word_duration = duration / len(words)
            
            for i, word in enumerate(words):
                # Interpolate timestamps
                w_start = start_time + (i * word_duration)
                w_end = start_time + ((i + 1) * word_duration)
                
                # Format timestamps
                start_str = format_timestamp(w_start)
                end_str = format_timestamp(w_end)
                
                f.write(f"{srt_index}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{word}\n\n")
                srt_index += 1

def process_audio(input_path, model_name="large-v3"):
    """
    Main processing function: Transcribe -> Translate -> Generate SRT.
    """
    # Load environment variables
    load_dotenv()
    
    # Check for OpenAI API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return

    client = OpenAI(api_key=api_key)
    
    print(f"Loading Whisper model '{model_name}'...")
    try:
        model = whisper.load_model(model_name)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print(f"Transcribing '{input_path}'...")
    try:
        # Enable word timestamps to get accurate segment boundaries
        result = model.transcribe(input_path, word_timestamps=True)
    except Exception as e:
        print(f"Error during transcription: {e}")
        return

    segments = result["segments"]
    english_sentences = [seg["text"].strip() for seg in segments]
    
    # Write original transcript for reference
    base_name = os.path.splitext(input_path)[0]
    txt_path = f"{base_name}.txt"
    print(f"Writing original script to '{txt_path}'...")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(result["text"].strip())

    # Translate
    hebrew_sentences = translate_batch(client, english_sentences)
    
    # Generate SRT
    srt_path = f"{base_name}.srt"
    generate_interpolated_srt(segments, hebrew_sentences, srt_path)
    
    print("Done!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe_audio.py <input_file> [model_name]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    model = "base"
    if len(sys.argv) > 2:
        model = sys.argv[2]
        
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
        
    process_audio(input_file, model)
