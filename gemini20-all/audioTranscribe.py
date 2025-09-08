import base64
import os
import queue
import struct

import google.generativeai as genai
import numpy as np
import speech_recognition as sr
import whisper
from vosk import Model, KaldiRecognizer, SetLogLevel


# def transcribe_whisper(base64_audio, duration=0):
#     model = whisper.load_model("tiny")
#
#     wav_data = process_pem_to_wav(base64_audio)
#
#     result = model.transcribe(wav_data)
#     print(f"Whisper data {result["text"]} ")
#     return result["text"]


# def transcribe_vosk(base64_audio, duration=0):
# # vosk_model = Model(r"D:\Prashantak\ai_ml\AI\vosk-model-en-us-0.22")
# vosk_model = Model(lang="en-us")
#     sample_rate = 16000
#     rec = KaldiRecognizer(vosk_model, sample_rate)
#     SetLogLevel(-1)
#
#     rec.SetWords(True)
#     rec.SetPartialWords(True)
#
#     wav_data = process_pem_to_wav(base64_audio)
#
#     rec.AcceptWaveform(wav_data)
#
#     transcription = rec.FinalResult();
#     print(transcription)
#     return transcription


def generate_wav_header(sample_rate, channels=1, sample_width=2, data_size=0):
    """Generates a WAV header."""
    riff_tag = b'RIFF'
    file_size = 36 + data_size  # Calculate file size (36 is size of header - 8)
    wav_tag = b'WAVE'
    fmt_tag = b'fmt '
    fmt_chunk_size = 16
    audio_format = 1  # PCM
    num_channels = channels
    sample_rate_bytes = struct.pack('<I', sample_rate)  # Little-endian unsigned int
    byte_rate = sample_rate * channels * sample_width
    byte_rate_bytes = struct.pack('<I', byte_rate)
    block_align = channels * sample_width
    block_align_bytes = struct.pack('<H', block_align)  # Little-endian unsigned short
    bits_per_sample = sample_width * 8
    bits_per_sample_bytes = struct.pack('<H', bits_per_sample)
    data_tag = b'data'

    # Prepare the chunk headers as bytes
    riff_header = riff_tag + struct.pack('<I',
                                         file_size - 8)  #file_size - 8 because riff chunk doesn't include riff_tag or file_size.
    fmt_header = fmt_tag + struct.pack('<I', fmt_chunk_size)
    data_header = data_tag + struct.pack('<I', data_size)

    # Assemble the entire fmt chunk
    fmt_chunk = (fmt_header + struct.pack('<H', audio_format) +
                 struct.pack('<H', num_channels) +
                 sample_rate_bytes + byte_rate_bytes +
                 block_align_bytes + bits_per_sample_bytes)

    # Assemble the entire data chunk
    data_chunk = data_header + struct.pack('<I', data_size)

    # Assemble the entire header
    header = riff_header + wav_tag + fmt_chunk + data_chunk

    return header


def process_pem_to_wav(base64_audio):
    """Converts a base64-encoded audio (assumed PCM data) to a WAV file."""
    try:
        audio_bytes = base64.b64decode(base64_audio)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        pcm_data = audio_array.tobytes()
        sample_rate = 16000
        wav_header = generate_wav_header(sample_rate, channels=1, sample_width=2, data_size=len(pcm_data))

        wav_data = wav_header + pcm_data
        return wav_data

    except Exception as e:
        print(f"Error during processing: {e}")
        return None


def call_gemini_transcribe(encoded_audio, audio_mime_type="audio/wav"):
    # Replace with your actual Gemini API key
    GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    wav_data = process_pem_to_wav(encoded_audio)
    # Configure Gemini Pro *BEFORE* using it
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')  # or 'gemini-pro' or  'gemini-1.5-flash-latest'
    contents = [
        {
            "parts": [
                {"text": "Please transcribe the spoken language in this audio accurately. Ignore any background noise "
                         "or non-speech sounds."},
                {
                    "inline_data": {
                        "mime_type": audio_mime_type,
                        "data": wav_data,
                    }
                },
            ]
        }
    ]

    response = model.generate_content(contents)
    transcription = response.text

    return transcription
