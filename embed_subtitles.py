import subprocess
import sys
import os
import re
import json

# Try to import Pillow for text measurement
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow library not found. Please install it with 'pip install Pillow'")
    sys.exit(1)

# Try to import bidi for RTL support
try:
    from bidi.algorithm import get_display
except ImportError:
    print("Warning: python-bidi not found. Hebrew text will be mirrored (reversed). Install it with 'pip install python-bidi'")
    def get_display(text):
        return text

FONT_PATH = "/Users/reem/Desktop/masking-test/SuezOne-Regular.ttf"
FONT_SIZE = 32

def measure_text_width(text, font_path, font_size):
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        # Fallback to default if font not found
        print(f"Warning: Font '{font_path}' not found, using default.")
        font = ImageFont.load_default()
    
    # Get bounding box
    bbox = font.getbbox(text)
    if bbox:
        return bbox[2] - bbox[0]
    return 0

def parse_srt(srt_path):
    """
    Parse SRT file and return list of subtitle entries with timestamps and text.
    Used as fallback if JSON is missing.
    """
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = re.split(r'\n\s*\n', content.strip())
    subtitles = []
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            timestamp_line = lines[1]
            times = re.findall(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', timestamp_line)
            if len(times) >= 2:
                start_time = times[0]
                end_time = times[1]
                
                start_sec = int(start_time[0]) * 3600 + int(start_time[1]) * 60 + int(start_time[2]) + int(start_time[3]) / 1000
                end_sec = int(end_time[0]) * 3600 + int(end_time[1]) * 60 + int(end_time[2]) + int(end_time[3]) / 1000
                
                text = ' '.join(lines[2:])
                subtitles.append({
                    'start': start_sec,
                    'end': end_sec,
                    'text': text
                })
    return subtitles

def generate_single_words(words_data):
    """
    Returns a list of dicts representing the display state for each word.
    """
    states = []
    for w in words_data:
        states.append({
            'word': w['text'],
            'start': w['start'],
            'end': w['end']
        })
    return states

def create_drawtext_filter(word_states):
    filters = []
    
    # Background box for the whole strip
    all_intervals = []
    for state in word_states:
        all_intervals.append(f"between(t,{state['start']},{state['end']})")
    
    enable_all = "+".join(all_intervals) if all_intervals else "0"
    
    # Fixed height box centered
    box_filter = f"drawbox=x=(iw-w)/2:y=(ih-h)/2:width=iw*0.70:height=50:color=black@0.70:t=fill" # :enable='{enable_all}'
    filters.append(box_filter)

    for state in word_states:
        word_text = state['word']
        start = state['start']
        end = state['end']
        
        display_text = get_display(word_text)
        display_text = display_text.replace("'", "'\\\\\\''").replace(":", "\\:")
        
        # White text, no background box for the word itself
        font_color = "#5FBEB6"
        
        text_filter = (
            f"drawtext=text='{display_text}':"
            f"fontfile={FONT_PATH}:"
            f"fontsize={FONT_SIZE}:"
            f"fontcolor={font_color}:"
            f"borderw=2:"
            f"bordercolor=white:"
            f"x=(w-text_w)/2:"
            f"y=(h-text_h)/2:"
            f"enable='between(t,{start},{end})'"
        )
        filters.append(text_filter)
            
    return ','.join(filters)

def embed_subtitles(video_path, audio_path, srt_path, output_path, watermark_path='water_mark.png'):
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        return
    if not os.path.exists(audio_path):
        print(f"Error: Audio file '{audio_path}' not found.")
        return
    if not os.path.exists(srt_path):
        print(f"Error: SRT file '{srt_path}' not found.")
        return

    # Try to load JSON first
    json_path = srt_path.replace('.srt', '.json')
    words_data = []
    
    if os.path.exists(json_path):
        print(f"Found JSON file '{json_path}', using it for precise word timing.")
        with open(json_path, 'r', encoding='utf-8') as f:
            words_data = json.load(f)
    else:
        print("JSON file not found, falling back to SRT parsing.")
        subtitles = parse_srt(srt_path)
        # Convert sentence-level SRT to pseudo word-level
        for sub in subtitles:
            w_list = sub['text'].split()
            if not w_list: continue
            duration = sub['end'] - sub['start']
            w_dur = duration / len(w_list)
            for i, w in enumerate(w_list):
                words_data.append({
                    'text': w,
                    'start': sub['start'] + i*w_dur,
                    'end': sub['start'] + (i+1)*w_dur
                })

    print(f"Processing {len(words_data)} words...")
    word_states = generate_single_words(words_data)
    print(f"Generated {len(word_states)} display states.")
    
    subtitle_filters = create_drawtext_filter(word_states)
    
    # Check if filter string is too long for command line
    # If so, we might need to write to a script file, but for now let's try direct.
    # macOS arg limit is high, but ffmpeg might complain.
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", audio_path,
    ]

    has_watermark = watermark_path and os.path.exists(watermark_path)
    if has_watermark:
        print(f"Adding watermark from '{watermark_path}'...")
        cmd.extend(["-i", watermark_path])
        
        filter_complex = (
            f"[2:v]scale=100:-1[wm];"
            f"[0:v][wm]overlay=(W-w)/2:H-h-50:format=auto,"
            f"{subtitle_filters}[outv]"
        )
        
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "1:a"
        ])
    else:
        cmd.extend([
            "-map", "0:v",
            "-map", "1:a",
            "-vf", subtitle_filters
        ])

    cmd.extend([
        "-c:v", "libx264",
        "-c:a", "aac",
        output_path
    ])
    
    print(f"Running ffmpeg...")
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully created '{output_path}'")
    except subprocess.CalledProcessError as e:
        print(f"Error running ffmpeg: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python embed_subtitles.py <video_file> <audio_file> <srt_file> <output_file> [watermark_file]")
        sys.exit(1)
        
    video = sys.argv[1]
    audio = sys.argv[2]
    srt = sys.argv[3]
    output = sys.argv[4]
    watermark = sys.argv[5] if len(sys.argv) > 5 else "water_mark.png"
    
    embed_subtitles(video, audio, srt, output, watermark)
