import requests
from base64 import b64encode
from google.cloud import vision
from utils.result import Result
from utils.globals import ACCOUNT_SID, TWILIO_AUTH_TOKEN


class OCRProcessor:
    """
    Classe para realizar OCR usando a API Google Cloud Vision.
    """

    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    async def fetch_image(self, media_url: str) -> Result:
        """
        Faz o download da imagem a partir de uma URL.

        Args:
            media_url (str): URL do arquivo de mídia.

        Returns:
            Result: Objeto contendo sucesso/falha e o conteúdo da imagem em bytes.
        """
        try:
            credentials = f'{ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}'
            encoded_credentials = b64encode(credentials.encode()).decode()
            headers = {'Authorization': f'Basic {encoded_credentials}'}

            response = requests.get(media_url, headers=headers)
            response.raise_for_status()
            return Result.ok(data=response.content)
        except requests.RequestException as e:
            return Result.fail(error_message=f'Erro ao baixar a imagem: {e}')

    async def perform_ocr(self, image_content: bytes) -> Result:
        """
        Realiza OCR em uma imagem usando a API Google Cloud Vision.

        Args:
            image_content (bytes): Conteúdo da imagem em bytes.

        Returns:
            Result: Objeto contendo sucesso/falha e o texto extraído da imagem.
        """
        try:
            image = vision.Image(content=image_content)
            response = self.client.text_detection(image=image)
            texts = response.text_annotations

            if texts:
                extracted_text = texts[0].description
                return Result.ok(data=extracted_text)
            else:
                return Result.fail(error_message='Nenhum texto detectado na imagem.')
        except Exception as e:
            return Result.fail(error_message=f'Erro ao realizar OCR: {e}')
