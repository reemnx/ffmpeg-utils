import yt_dlp
import sys
import os

def download_video(url, output_filename="input_video.mp4"):
    """
    Downloads a video from a YouTube URL using yt-dlp.
    """
    print(f"Downloading video from {url}...")
    
    # Remove existing file if it exists to avoid conflicts
    if os.path.exists(output_filename):
        os.remove(output_filename)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_filename,
        'quiet': False,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Successfully downloaded to {output_filename}")
        return True
    except Exception as e:
        print(f"Error downloading video: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_video.py <youtube_url> [output_filename]")
        sys.exit(1)
        
    url = sys.argv[1]
    output = "input_video.mp4"
    if len(sys.argv) > 2:
        output = sys.argv[2]
        
    download_video(url, output)
