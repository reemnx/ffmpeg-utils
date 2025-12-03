import os
import argparse
from instagrapi import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Monkeypatch instagrapi to fix validation error
from instagrapi.types import ClipsOriginalSoundInfo
from typing import List, Optional, Any
from pydantic import Field

# Update the field to allow None
if 'audio_filter_infos' in ClipsOriginalSoundInfo.model_fields:
    ClipsOriginalSoundInfo.model_fields['audio_filter_infos'].default = None
    ClipsOriginalSoundInfo.model_fields['audio_filter_infos'].annotation = Optional[List[Any]]
    ClipsOriginalSoundInfo.model_rebuild(force=True)


def upload_reel(video_path, title, description, thumbnail_path=None):
    """
    Uploads a video to Instagram as a Reel.
    """
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")

    if not username or not password:
        print("Error: INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD must be set in .env file.")
        return

    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    if thumbnail_path and not os.path.exists(thumbnail_path):
        print(f"Error: Thumbnail file not found at {thumbnail_path}")
        return

    cl = Client()
    
    print(f"Logging in as {username}...")
    try:
        cl.login(username, password)
    except Exception as e:
        print(f"Failed to login: {e}")
        return

    caption = """היי, אנחנו BrainSnacks!
בערוץ שלנו תמצאו מדי יום את התכנים הכי ויראליים, המפתיעים והכיפיים
לפני שהם מתפוצצים ברחבי הרשת.
לחצו לייק והירשמו לערוץ כדי שלא תפספסו אף עדכון חם!

shortreels #shortsvideos #facts💯 #VIRALSHORTS #viralvídeo#"""
    
    print(f"Uploading {video_path} as Reel...")
    try:
        media = cl.clip_upload(
            video_path,
            caption=caption,
            thumbnail=thumbnail_path
        )
        print(f"Successfully uploaded Reel! Media PK: {media.pk}")
        print(f"Link: https://www.instagram.com/reel/{media.code}/")
    except Exception as e:
        print(f"Failed to upload Reel: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a video to Instagram as a Reel.")
    parser.add_argument("--file", required=True, help="Path to the video file (mp4)")
    parser.add_argument("--title", required=False, help="Title of the Reel")
    parser.add_argument("--description", required=False, help="Description/Caption for the Reel")
    parser.add_argument("--thumbnail", help="Path to the thumbnail image (optional)")

    args = parser.parse_args()

    upload_reel(args.file, args.title, args.description, args.thumbnail)
