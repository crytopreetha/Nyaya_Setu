"""
Loads a faster-whisper model once and reuses it across requests. First call
downloads model weights from Hugging Face (needs network that one time);
after that it runs fully offline/CPU. Model size is configurable via
WHISPER_MODEL_SIZE (tiny/base/small — tiny is fastest, small is most accurate).
"""
from functools import lru_cache


@lru_cache(maxsize=1)
def get_whisper_model(model_size: str = "tiny"):
    from faster_whisper import WhisperModel

    return WhisperModel(model_size, device="cpu", compute_type="int8")
