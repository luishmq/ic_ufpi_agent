import tempfile
import uuid
from base64 import b64encode

import requests
import soundfile as sf
import speech_recognition as sr
from google.cloud import storage

from utils.globals import PASSWORD, USERAUDIO


async def transcript_audio(media_url: str, from_number: str) -> str:
    """Transcreve áudio para texto e armazena os áudios no Cloud Storage."""
    try:
        credentials = f'{USERAUDIO}:{PASSWORD}'
        encoded_credentials = b64encode(credentials.encode()).decode()
        headers = {'Authorization': f'Basic {encoded_credentials}'}

        response = requests.get(media_url, headers=headers)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as ogg_temp_file:
            ogg_temp_file.write(response.content)
            ogg_file_path = ogg_temp_file.name

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_temp_file:
            wav_file_path = wav_temp_file.name

        storage_client = storage.Client()
        bucket_name = 'audios_ssp'
        bucket = storage_client.bucket(bucket_name)

        ogg_blob = bucket.blob(f'audios_ogg/{uuid.uuid1()}.ogg')
        ogg_blob.upload_from_filename(ogg_file_path)

        audio_data, sample_rate = sf.read(ogg_file_path)
        sf.write(wav_file_path, audio_data, sample_rate)

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_file_path) as source:
            audio_text = recognizer.record(source)
            text = recognizer.recognize_google(audio_text, language='pt-BR')

        return text
    except Exception as e:
        print(e)
        return ''
