import tempfile
import uuid
import os
from dotenv import load_dotenv
from base64 import b64encode
import requests
import soundfile as sf
import speech_recognition as sr
from google.cloud import storage
from utils.result import Result


load_dotenv()

ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')


class AudioDownloader:
    """Classe responsável por baixar áudio de uma URL protegida por autenticação."""

    @staticmethod
    async def download_audio(media_url: str) -> Result:
        """
        Faz o download do áudio de uma URL protegida.

        Args:
            media_url (str): URL do arquivo de mídia.

        Returns:
            Result: Objeto contendo sucesso/falha e o caminho do arquivo baixado.
        """
        try:
            credentials = f'{ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}'
            encoded_credentials = b64encode(credentials.encode()).decode()
            headers = {'Authorization': f'Basic {encoded_credentials}'}

            response = requests.get(media_url, headers=headers)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_file.write(response.content)
                return Result.ok(data=temp_file.name)
        except requests.RequestException as e:
            return Result.fail(error_message=f'Erro ao fazer download do áudio: {e}')


class AudioConverter:
    """Classe responsável pela conversão de formatos de áudio."""

    @staticmethod
    async def convert_ogg_to_wav(ogg_path: str) -> Result:
        """
        Converte um arquivo OGG para WAV.

        Args:
            ogg_path (str): Caminho do arquivo OGG.

        Returns:
            Result: Objeto contendo sucesso/falha e o caminho do arquivo WAV convertido.
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_temp_file:
                wav_path = wav_temp_file.name
                audio_data, sample_rate = sf.read(ogg_path)
                sf.write(wav_path, audio_data, sample_rate)
                return Result.ok(data=wav_path)
        except Exception as e:
            return Result.fail(error_message=f'Erro ao converter OGG para WAV: {e}')


class CloudUploader:
    """Classe responsável pelo upload de arquivos para o Google Cloud Storage."""

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()

    async def upload_to_cloud_storage(self, file_path: str, folder: str) -> Result:
        """
        Faz o upload de um arquivo para o Google Cloud Storage.

        Args:
            file_path (str): Caminho do arquivo local.
            folder (str): Pasta no bucket onde o arquivo será armazenado.

        Returns:
            Result: Objeto contendo sucesso/falha e o nome do arquivo armazenado.
        """
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f'{folder}/{uuid.uuid1()}')
            blob.upload_from_filename(file_path)
            return Result.ok(data=blob.name)
        except Exception as e:
            return Result.fail(error_message=f'Erro ao enviar arquivo para o Cloud Storage: {e}')


class AudioTranscriber:
    """Classe responsável pela transcrição de áudio de arquivos WAV."""

    @staticmethod
    async def transcribe_audio(wav_path: str) -> Result:
        """
        Transcreve áudio de um arquivo WAV.

        Args:
            wav_path (str): Caminho do arquivo WAV.

        Returns:
            Result: Objeto contendo sucesso/falha e o texto transcrito.
        """
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_text = recognizer.record(source)
                text = recognizer.recognize_google(audio_text, language='pt-BR')
                return Result.ok(data=text)
        except sr.UnknownValueError:
            return Result.fail(error_message='Não foi possível reconhecer o áudio.')
        except sr.RequestError as e:
            return Result.fail(error_message=f'Erro ao usar o serviço de reconhecimento de fala: {e}')
