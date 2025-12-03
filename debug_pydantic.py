from instagrapi.types import ClipsOriginalSoundInfo
from typing import List, Optional, Any
from pydantic import Field

print("Original annotation:", ClipsOriginalSoundInfo.model_fields['audio_filter_infos'].annotation)
print("Original required:", ClipsOriginalSoundInfo.model_fields['audio_filter_infos'].is_required())

# Attempt fix
if 'audio_filter_infos' in ClipsOriginalSoundInfo.model_fields:
    # Set default to None to make it optional
    ClipsOriginalSoundInfo.model_fields['audio_filter_infos'].default = None
    ClipsOriginalSoundInfo.model_fields['audio_filter_infos'].annotation = Optional[List[Any]]
    
    # Rebuild model
    ClipsOriginalSoundInfo.model_rebuild(force=True)

print("New annotation:", ClipsOriginalSoundInfo.model_fields['audio_filter_infos'].annotation)
print("New required:", ClipsOriginalSoundInfo.model_fields['audio_filter_infos'].is_required())

# Verify instantiation with None
try:
    instance = ClipsOriginalSoundInfo(audio_filter_infos=None, audio_asset_id="123", music_canonical_id="123", progressive_download_url="http://example.com", dash_manifest="xml", ig_artist=None, should_mute_audio=False, original_media_id="123", hide_remixing=False, duration_in_ms=1000, time_created=123, original_audio_title="test", consumed_media_gap=0)
    print("Instantiation successful!")
except Exception as e:
    print(f"Instantiation failed: {e}")
