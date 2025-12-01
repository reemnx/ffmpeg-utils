import os
import sys
import argparse
from extract_audio import extract_audio
from remove_subs import process_video as remove_subtitles
from transcribe_audio import process_audio as transcribe_and_translate
from embed_subtitles import embed_subtitles

def main():
    parser = argparse.ArgumentParser(description="Video Processing Pipeline Wrapper")
    parser.add_argument("--input_video", default="input_video.mp4", help="Path to input video file")
    parser.add_argument("--mask_image", default="mask_image.png", help="Path to mask image for subtitle removal")
    parser.add_argument("--watermark", default="water_mark.png", help="Path to watermark image")
    parser.add_argument("--output_video", default="final_video.mp4", help="Path to final output video")
    parser.add_argument("--model", default="large-v3", help="Whisper model name")
    
    args = parser.parse_args()

    # Derived filenames
    base_name = os.path.splitext(args.input_video)[0]
    extracted_audio = f"{base_name}_audio.mp3"
    clean_video = f"clean_{os.path.basename(args.input_video)}"
    # transcribe_audio.py generates srt based on input filename
    # it strips extension and adds .srt
    # so if input is "input_video_audio.mp3", it generates "input_video_audio.srt"
    audio_base_name = os.path.splitext(extracted_audio)[0]
    generated_srt = f"{audio_base_name}.srt"

    print("=== Step 1: Extract Audio ===")
    extract_audio(args.input_video, extracted_audio)
    
    print("\n=== Step 2: Remove Old Subtitles ===")
    remove_subtitles(args.input_video, args.mask_image, clean_video)
    
    print("\n=== Step 3: Transcribe and Generate Subtitles ===")
    # process_audio takes input path and model name
    transcribe_and_translate(extracted_audio, args.model)
    
    print("\n=== Step 4: Embed New Subtitles ===")
    if not os.path.exists(generated_srt):
        print(f"Error: Expected SRT file '{generated_srt}' was not found.")
        sys.exit(1)
        
    embed_subtitles(clean_video, extracted_audio, generated_srt, args.output_video, args.watermark)
    
    print(f"\n=== Processing Complete! ===")
    print(f"Final video saved to: {args.output_video}")

if __name__ == "__main__":
    main()
