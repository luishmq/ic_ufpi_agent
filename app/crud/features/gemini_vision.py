import os
import requests
import vertexai
import base64

from dotenv import load_dotenv
from vertexai.generative_models import GenerativeModel, Part, SafetySetting

from utils.result import Result
from utils.prompts import PROMPT_GEMINI_VISION


load_dotenv()

ACCOUNT_SID = os.getenv('ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')


class GeminiVision:
    """
    Classe para interpretar imagens usando a API Gemini do Vertex AI.
    """

    _gemini_initialized = False
    _gemini_model = None

    _generation_config = {
        'max_output_tokens': 8192,
        'temperature': 1,
        'top_p': 0.95,
    }
    _safety_settings = [
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=SafetySetting.HarmBlockThreshold.OFF,
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=SafetySetting.HarmBlockThreshold.OFF,
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=SafetySetting.HarmBlockThreshold.OFF,
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
    ]

    def __init__(self):
        """
        Se precisar de algo no construtor, coloque aqui.
        Não há necessidade de invocar a inicialização do Gemini em cada instância
        - usaremos um método de classe para isso.
        """
        pass

    @classmethod
    def _init_gemini_once(cls):
        """
        Método de classe para inicializar o Vertex AI e carregar o modelo Gemini apenas uma vez.
        """
        if not cls._gemini_initialized:
            vertexai.init(
                project='annular-weaver-428312-s3',
                location='us-central1',
                api_endpoint='us-central1-aiplatform.googleapis.com',
            )
            cls._gemini_model = GenerativeModel('gemini-1.5-flash-002')
            cls._gemini_initialized = True

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
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers = {'Authorization': f'Basic {encoded_credentials}'}

            response = requests.get(media_url, headers=headers)
            response.raise_for_status()
            return Result.ok(data=response.content)
        except requests.RequestException as e:
            return Result.fail(error_message=f'Erro ao baixar a imagem: {e}')

    async def perform_gemini(self, image_content: bytes) -> Result:
        """
        Interpreta a imagem usando o modelo Gemini do Vertex AI.

        Args:
            image_content (bytes): Conteúdo da imagem em bytes.

        Returns:
            Result: Objeto contendo sucesso/falha e o texto (ou conteúdo) extraído da imagem.
        """
        try:
            self._init_gemini_once()

            mime_type = 'image/png'

            image_part = Part.from_data(mime_type=mime_type, data=image_content)

            response = self._gemini_model.generate_content(
                [image_part, PROMPT_GEMINI_VISION],
                generation_config=self._generation_config,
                safety_settings=self._safety_settings,
                stream=False,
            )

            return Result.ok(data=response.text)

        except Exception as e:
            return Result.fail(error_message=f'Erro ao interpretar a imagem com Gemini: {e}')

    async def perform_gemini_local(self, image_path: str) -> Result:
        """
        Interpreta uma imagem local usando o modelo Gemini do Vertex AI.

        Args:
            image_path (str): Caminho para o arquivo de imagem local.

        Returns:
            Result: Objeto contendo sucesso/falha e o texto extraído da imagem.
        """
        try:
            self._init_gemini_once()

            if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
                mime_type = 'image/jpeg'
            elif image_path.lower().endswith('.png'):
                mime_type = 'image/png'
            else:
                mime_type = 'image/jpeg'

            with open(image_path, 'rb') as f:
                image_content = f.read()

            image_part = Part.from_data(mime_type=mime_type, data=image_content)

            response = self._gemini_model.generate_content(
                [image_part, PROMPT_GEMINI_VISION],
                generation_config=self._generation_config,
                safety_settings=self._safety_settings,
                stream=False,
            )

            return Result.ok(data=response.text)

        except Exception as e:
            return Result.fail(error_message=f'Erro ao interpretar a imagem local com Gemini: {e}')
