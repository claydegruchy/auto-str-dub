from pydantic import BaseModel
from typing import Union, List, Optional


class TTSOptions(BaseModel):
    model_name: str
    speaker_wav: Union[str, List[str]]
    language_idx: str
    title: str
    text: Optional[str] = None  # Optional field
    out_path: Optional[str] = None  # Optional field
    emotion: Optional[str] = None  # Optional field

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"'{key}' not found in TTSOptions")

    class Config:
        # Ensures we can access attributes both as a dictionary and as object attributes
        extra = 'allow'


class TTSOptionsPublic(BaseModel):
    emotion: Optional[str] = "neutral"  # Optional field
    language_idx: str = "en"
    speaker_wav: Union[str, List[str]]
    title: str
