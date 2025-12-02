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
        'format': 'bestvideo[protocol^=m3u8]+bestaudio/best[protocol^=m3u8]/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_filename,
        'quiet': False,
        'no_warnings': True,
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
