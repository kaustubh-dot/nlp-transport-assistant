"""Hindi Speech Recognition module using local open-source Whisper.

Provides zero-cost, local voice input for Hindi and Hinglish queries
using OpenAI's Whisper (openai/whisper-base) running on GPU/CPU.
"""

import os
from typing import Optional, Union, BinaryIO


class HindiSpeechRecognizer:
    """Local Speech-to-Text recognizer for Hindi / Indian English transit questions."""

    def __init__(self, model_id: str = "openai/whisper-base", lazy_load: bool = True):
        self.model_id = model_id
        self.pipe = None
        self._lazy_load = lazy_load
        if not self._lazy_load:
            self._load_model()

    def _load_model(self):
        """Loads Hugging Face ASR pipeline."""
        if self.pipe is None:
            try:
                import torch
                from transformers import pipeline

                device = 0 if torch.cuda.is_available() else -1
                torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
                self.pipe = pipeline(
                    "automatic-speech-recognition",
                    model=self.model_id,
                    torch_dtype=torch_dtype,
                    device=device
                )
            except Exception as e:
                print(f"Warning: Could not load Whisper model ({e}).")
                self.pipe = None

    def transcribe(self, audio_input: Union[str, bytes, BinaryIO]) -> str:
        """Transcribes Hindi audio into Hindi/Hinglish text.

        Args:
            audio_input: Path to audio file, or audio bytes/stream.

        Returns:
            Transcribed text string.
        """
        if not audio_input:
            return ""

        if self.pipe is None:
            self._load_model()

        if self.pipe is not None:
            import tempfile
            temp_file = None
            try:
                target = audio_input
                if isinstance(audio_input, (bytes, bytearray)):
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        f.write(audio_input)
                        temp_file = f.name
                    target = temp_file
                elif hasattr(audio_input, "read"):
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        f.write(audio_input.read())
                        temp_file = f.name
                    target = temp_file

                result = self.pipe(
                    target,
                    generate_kwargs={"language": "hindi", "task": "transcribe"}
                )
                return result.get("text", "").strip()
            except Exception as e:
                print(f"ASR transcription error: {e}")
            finally:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except OSError:
                        pass

        # Fallback if audio cannot be processed or model not loaded
        return ""
