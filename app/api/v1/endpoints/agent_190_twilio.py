import os

from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response, status
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from crud.agents.agent190_modeling import Agent190, SessionManager
from crud.features.audio_transcript import AudioDownloader, AudioConverter, AudioTranscriber, CloudUploader
from crud.features.history_bq import BigQueryStorage
from crud.features.vision_ocr import OCRProcessor
from crud.features.maps import geocode_reverse
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_google_vertexai import ChatVertexAI
from langchain_anthropic import ChatAnthropic
from crud.adapters.adapter import LangChainLLMAdapter


load_dotenv()

ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

router = APIRouter()

session_manager = SessionManager()

openai_llm = LangChainLLMAdapter(ChatOpenAI(model='gpt-4o-mini', temperature=0.2, api_key=OPENAI_API_KEY))
ollama_llm = LangChainLLMAdapter(ChatOllama(model='llama3.1', temperature=0.2))
vertexai_llm = LangChainLLMAdapter(ChatVertexAI(model='gemini-1.5-flash-001', temperature=0.2))
anthropic_llm = LangChainLLMAdapter(
    ChatAnthropic(model='claude-3-5-haiku-20241022', temperature=0.2, api_key=ANTHROPIC_API_KEY)
)
# xai_llm = LangChainLLMAdapter(ChatXAI(model='grok-beta', temperature=0.2))

agent = Agent190(session_manager=session_manager, llm_adapter=ollama_llm)
# agent.llm_manager.set_adapter(vertexai_llm)

cloud_uploader = CloudUploader(bucket_name='audios_ssp')
ocr_processor = OCRProcessor()
bq_storage = BigQueryStorage()

client = Client(ACCOUNT_SID, TWILIO_AUTH_TOKEN)


async def process_audio(media_url, msg, resp):
    """
    Processa um arquivo de áudio fornecido por uma URL, realizando o download,
    conversão para formato WAV, upload para o Cloud Storage e transcrição do conteúdo.

    Args:
        media_url (str): URL do arquivo de áudio.
        msg: Objeto de mensagem Twilio para manipulação de respostas.
        resp: Objeto de resposta Twilio.

    Returns:
        str: Texto transcrito do áudio, ou None em caso de erro.
    """
    download_result = await AudioDownloader.download_audio(media_url)
    if not download_result.success:
        msg.body(download_result.error_message)
        return None

    convert_result = await AudioConverter.convert_ogg_to_wav(download_result.data)
    if not convert_result.success:
        msg.body(convert_result.error_message)
        return None

    upload_result = await cloud_uploader.upload_to_cloud_storage(convert_result.data, folder='audios_wav')
    if not upload_result.success:
        msg.body(upload_result.error_message)
        return None

    transcribe_result = await AudioTranscriber.transcribe_audio(convert_result.data)
    if not transcribe_result.success:
        msg.body(transcribe_result.error_message)
        return None

    return transcribe_result.data


async def process_image(media_url, msg, resp):
    """
    Processa uma imagem fornecida por uma URL, realizando o download,
    análise OCR e extração de texto.

    Args:
        media_url (str): URL do arquivo de imagem.
        msg: Objeto de mensagem Twilio para manipulação de respostas.
        resp: Objeto de resposta Twilio.

    Returns:
        str: Texto extraído da imagem, ou None em caso de erro.
    """
    ocr_result = await ocr_processor.fetch_image(media_url)
    if not ocr_result.success:
        msg.body(ocr_result.error_message)
        return None

    ocr_text_result = await ocr_processor.perform_ocr(ocr_result.data)
    if not ocr_text_result.success:
        msg.body(ocr_text_result.error_message)
        return None

    return ocr_text_result.data


async def handle_response(user_input, session_id, msg, resp):
    """
    Gera uma resposta baseada no input do usuário, armazena o histórico no BigQuery
    e retorna a resposta para o usuário.

    Args:
        user_input (str): Input fornecido pelo usuário (texto, áudio transcrito, ou texto extraído).
        session_id (str): Identificador único da sessão do usuário.
        msg: Objeto de mensagem Twilio para manipulação de respostas.
        resp: Objeto de resposta Twilio.

    Returns:
        Response: Resposta HTTP em formato XML para o Twilio.
    """
    agent_result = await agent.generate_text_response(user_input, session_id)
    if not agent_result.success:
        msg.body(agent_result.error_message)
        return Response(content=str(resp), media_type='application/xml')

    bq_result = await bq_storage.store_response(
        dataset_id='history',
        table_id='chats',
        session_id=session_id,
        user_input=user_input,
        response=agent_result.data,
    )
    if not bq_result.success:
        msg.body(bq_result.error_message)
        return Response(content=str(resp), media_type='application/xml')

    msg.body(agent_result.data)
    return Response(content=str(resp), media_type='application/xml')


@router.post('/predict_twilio_190', status_code=status.HTTP_200_OK)
async def predict_twilio_190(request: Request):
    """
    Endpoint para processar mensagens de texto, áudio, imagem ou localização recebidas via Twilio.

    Args:
        request (Request): Requisição contendo os dados enviados pelo Twilio.

    Returns:
        Response: Resposta em formato XML para Twilio.
    """

    form_data = await request.form()
    num_media = int(form_data.get('NumMedia', 0))
    from_number = form_data.get('From')
    session_id = from_number

    resp = MessagingResponse()
    msg = resp.message()

    latitude = form_data.get('Latitude')
    longitude = form_data.get('Longitude')

    if latitude and longitude:
        geocode_result = await geocode_reverse(latitude, longitude)
        if not geocode_result.success:
            msg.body(f'Erro ao obter endereço: {geocode_result.error_message}')
            return Response(content=str(resp), media_type='application/xml')

        location_data = f'Localização recebida:\nEndereço: {geocode_result.data}'
        return await handle_response(location_data, session_id, msg, resp)

    elif num_media > 0:
        media_url = form_data.get('MediaUrl0')
        media_content_type = form_data.get('MediaContentType0')

        if 'audio' in media_content_type:
            user_input = await process_audio(media_url, msg, resp)
            if not user_input:
                return Response(content=str(resp), media_type='application/xml')
        elif 'image' in media_content_type:
            user_input = await process_image(media_url, msg, resp)
            if not user_input:
                return Response(content=str(resp), media_type='application/xml')
        else:
            msg.body('Tipo de mídia não suportado.')
            return Response(content=str(resp), media_type='application/xml')

        return await handle_response(user_input, session_id, msg, resp)

    else:
        incoming_msg = form_data.get('Body')
        return await handle_response(incoming_msg, session_id, msg, resp)
