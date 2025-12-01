import os
import sys

def extract_audio(video_path, output_audio_path):
    """
    Extracts audio from a video file and saves it as an MP3.
    """
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at '{video_path}'")
        return

    try:
        # Try importing from moviepy directly (v2+)
        from moviepy import VideoFileClip
    except ImportError:
        try:
            # Fallback for older versions
            from moviepy.editor import VideoFileClip
        except ImportError as e:
            print(f"Error: 'moviepy' library could not be imported: {e}")
            print("Please ensure it is installed in the current environment.")
            sys.exit(1)

    print(f"Processing '{video_path}'...")
    
    try:
        # Load the video clip
        video_clip = VideoFileClip(video_path)
        
        # Check if the video has audio
        if video_clip.audio is None:
            print("Error: The video file does not contain any audio track.")
            video_clip.close()
            return

        # Write the audio to the output file
        print(f"Extracting audio to '{output_audio_path}'...")
        video_clip.audio.write_audiofile(output_audio_path)
        
        # Close the clip to release resources
        video_clip.close()
        print("Done!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Define input and output filenames
    # The user requested "input_video" (assumed to be a file path, adding extension if needed or generic matching)
    # but typically this means "input_video.mp4" based on the directory listing.
    # I'll default to "input_video.mp4" but check for extensions if not found.
    
    input_video_name = "input_video.mp4"
    output_audio_name = "input_audio.mp3"

    # Allow command line arguments for flexibility
    if len(sys.argv) > 1:
        input_video_name = sys.argv[1]
    if len(sys.argv) > 2:
        output_audio_name = sys.argv[2]

    extract_audio(input_video_name, output_audio_name)

