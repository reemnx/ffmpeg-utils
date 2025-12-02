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
FONT_SIZE = 130

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

def get_video_width(video_path):
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width", "-of", "csv=s=x:p=0", video_path
    ]
    try:
        output = subprocess.check_output(cmd).decode("utf-8").strip()
        return int(output)
    except Exception as e:
        print(f"Error probing video width: {e}")
        return 1920 # Fallback

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

def group_words_by_width(words_data, max_width, font_path, font_size):
    """
    Groups words. Modified to strictly return one word per group for the requested effect.
    """
    groups = []
    for w in words_data:
        groups.append({
            'text': w['text'],
            'words': [w],
            'start': w['start'],
            'end': w['end']
        })
    return groups

def time_to_ass(seconds):
    """Converts seconds to ASS timestamp format H:MM:SS.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds * 100) % 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"

def is_hebrew(text):
    return any("\u0590" <= c <= "\u05EA" for c in text)

def generate_ass_file(groups, video_width, video_height, font_path, output_ass_path):
    """
    Generates an ASS subtitle file with:
    1. One word at a time.
    2. No background.
    3. Growing animation (scale 100% -> 115%).
    """
    
    # ASS Header
    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {video_width}",
        f"PlayResY: {video_height}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        # Style definition: Suez One, 32pt, Teal text (&HB6BE5F), Black border
        # Alignment 5 = Center
        # Outline changed from 2 to 5 for thicker stroke
        f"Style: Default,Suez One,{FONT_SIZE},&H00B6BE5F,&H000000FF,&HFFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,5,0,5,10,10,10,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]
    
    # Position at center
    # We want the text to be roughly in the center-bottom area where it was before, or just center?
    # The previous code had a box centered vertically.
    # Let's put it at the same vertical position as the previous text center.
    # Previous text_y was video_height // 2.
    
    box_height = 180
    box_y_top = (video_height - box_height) // 2
    box_y_bottom = box_y_top + box_height
    
    text_y = video_height // 2 
    text_x = video_width // 2
    
    for g in groups:
        g_start_ass = time_to_ass(g['start'])
        g_end_ass = time_to_ass(g['end'])
        
        # 1. Background Box (Layer 0)
        # 85% width, centered
        box_width = int(video_width * 0.85)
        box_x_left = (video_width - box_width) // 2
        box_x_right = box_x_left + box_width
        
        # Draw black box with opacity (Alpha 0.55 -> ~140 -> 8C)
        # Using vector drawing. IMPORTANT: Add \pos(0,0) to force absolute coordinates.
        # Add \an7 (Top-Left) alignment to ensure (0,0) is the top-left corner.
        rect_draw = f"m {box_x_left} {box_y_top} l {box_x_right} {box_y_top} l {box_x_right} {box_y_bottom} l {box_x_left} {box_y_bottom}"
        ass_lines.append(
            f"Dialogue: 0,{g_start_ass},{g_end_ass},Default,,0,0,0,,{{\\an7\\pos(0,0)\\bord0\\shad0\\1c&H000000&\\1a&H8C&\\p1}}{rect_draw}{{\\p0}}"
        )
        
        text = g['text']
        
        # Animation:
        # \an5: Alignment 5 (Center)
        # \pos(x,y): Position
        # \fscx100\fscy100: Initial scale 100%
        # \t(\fscx115\fscy115): Animate to scale 115% over the duration
        
        ass_line = (
            f"Dialogue: 1,{g_start_ass},{g_end_ass},Default,,0,0,0,,{{\\an5\\pos({text_x},{text_y})\\fscx100\\fscy100\\t(\\fscx115\\fscy115)}}{text}"
        )
        ass_lines.append(ass_line)

    with open(output_ass_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(ass_lines))
    
    return output_ass_path

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
    
    # Get video width to calculate max text width
    video_width = get_video_width(video_path)
    print(f"Video width: {video_width}")
    
    # Calculate max width for text (85% of video width, minus some padding maybe?)
    # The box is 85%, so text should be slightly less to fit comfortably.
    # Let's say 80% for text to be safe inside 85% box.
    max_text_width = int(video_width * 0.80)
    
    groups = group_words_by_width(words_data, max_text_width, FONT_PATH, FONT_SIZE)
    print(f"Grouped into {len(groups)} subtitle lines.")
    
    # Generate ASS file
    ass_path = output_path.replace('.mp4', '.ass')
    generate_ass_file(groups, video_width, 640, FONT_PATH, ass_path) # Assuming 640 height if probing failed, but we should probe height too.
    
    # Probe height
    try:
        cmd_h = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height", "-of", "csv=s=x:p=0", video_path]
        video_height = int(subprocess.check_output(cmd_h).decode("utf-8").strip())
    except:
        video_height = 640
        
    generate_ass_file(groups, video_width, video_height, FONT_PATH, ass_path)
    print(f"Generated ASS file: {ass_path}")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", audio_path,
    ]

    has_watermark = watermark_path and os.path.exists(watermark_path)
    
    # Prepare ASS filter
    # We need to point to the font directory so ASS can find 'Suez One'
    font_dir = os.path.dirname(FONT_PATH)
    ass_filter = f"ass={ass_path}:fontsdir={font_dir}"
    
    if has_watermark:
        print(f"Adding watermark from '{watermark_path}'...")
        cmd.extend(["-i", watermark_path])
        
        filter_complex = (
            f"[2:v]scale=100:-1[wm];"
            f"[0:v][wm]overlay=(W-w)/2:H-h-50:format=auto[v_wm];"
            f"[v_wm]{ass_filter}[outv]"
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
            "-vf", ass_filter
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
