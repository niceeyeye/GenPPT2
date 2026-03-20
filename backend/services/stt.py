import os
import uuid
import torch
import shutil
import imageio_ffmpeg

# Define a custom model cache directory within our project
# to avoid [WinError 5] Access is denied on C:/Users/Admin/.modelscope
custom_cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model_cache")
os.makedirs(custom_cache_dir, exist_ok=True)
os.environ["MODELSCOPE_CACHE"] = custom_cache_dir
ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.join(custom_cache_dir, "ffmpeg_bin")
os.makedirs(ffmpeg_dir, exist_ok=True)
ffmpeg_cmd = os.path.join(ffmpeg_dir, "ffmpeg.exe")
if not os.path.exists(ffmpeg_cmd):
    shutil.copyfile(ffmpeg_bin, ffmpeg_cmd)
if ffmpeg_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
from funasr import AutoModel

# Initialize the model
# We use the locally downloaded SenseVoiceSmall model
model_id = r"F:\BaiduNetdiskDownload\GenPPT\SenseVoiceSmall"

# Global model instance
_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading SenseVoiceSmall model from local path: {model_id}...")
        _model = AutoModel(
            model=model_id,
            trust_remote_code=False,
            device="cuda" if torch.cuda.is_available() else "cpu",
            disable_update=True # Prevent it from trying to check for updates
        )
    return _model

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribes the given audio file using SenseVoiceSmall.
    """
    model = get_model()
    
    # SenseVoiceSmall supports multilingual and rich transcription (emotions, events)
    # For PPT topic, we mainly need the text.
    res = model.generate(
        input=audio_path,
        cache={},
        language="auto",  # auto-detect language
        use_itn=True,     # use inverse text normalization
        batch_size_s=60,
        merge_vad=False,
    )
    
    if res and len(res) > 0:
        print(f"STT Raw result: {res}")
        # res is a list of results, each having a 'text' field
        # SenseVoice results might contain tags like <|zh|>, <|HAPPY|>, etc.
        # We should clean them up for the user input.
        text = res[0].get('text', '')
        # Simple cleanup: remove tags like <|...|>
        import re
        clean_text = re.sub(r'<\|.*?\|>', '', text).strip()
        print(f"STT Cleaned text: {clean_text}")
        return clean_text
    
    return ""

def save_and_transcribe(audio_bytes: bytes, extension: str = "wav") -> str:
    """
    Saves the audio bytes to a temporary file and transcribes it.
    """
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    temp_path = os.path.join(temp_dir, f"{file_id}.{extension}")
    
    try:
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)
        
        text = transcribe_audio(temp_path)
        return text
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
