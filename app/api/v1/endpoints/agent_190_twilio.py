import os

from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response, status
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from crud.agents.agent190_modeling import Agent190, SessionManager
from crud.features.audio_transcript import AudioDownloader, AudioConverter, AudioTranscriber, CloudUploader
from crud.features.history_bq import BigQueryStorage
from crud.features.gemini_vision import GeminiVision
from crud.features.maps import geocode_reverse
from crud.managers.llm_manager import LLMManager
from crud.tools.tools import Tools

load_dotenv()

ACCOUNT_SID = os.getenv('ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

router = APIRouter()

session_manager = SessionManager()
tools_instance = Tools()

llm_manager = LLMManager()
factory_result = llm_manager.create_adapter(
    model_type='anthropic',
    tools=tools_instance,
    api_key=ANTHROPIC_API_KEY,
    model_name='claude-3-5-haiku-20241022',
    temperature=0.5,
)

if not factory_result.success:
    raise Exception(f'Erro ao criar adaptador LLM: {factory_result.error_message}')

agent = Agent190(session_manager=session_manager, llm_adapter=factory_result.data)

# llm_manager.create_adapter('openai', tools_instance, api_key=OPENAI_API_KEY, model_name='gpt-4o-mini')
# agent.llm_manager.set_adapter(llm_manager.llm_adapter)

cloud_uploader = CloudUploader(bucket_name='audios_ssp')
gemini_vision = GeminiVision()
bq_storage = BigQueryStorage()

client = Client(ACCOUNT_SID, TWILIO_AUTH_TOKEN)


async def process_audio(media_url, msg, resp):
    """
    Processa um arquivo de áudio fornecido por uma URL, realizando o download,
    conversão para formato WAV, upload para o Cloud Storage e transcrição do conteúdo.
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
    Processa uma imagem fornecida por uma URL, realizando o download, interpretação com Gemini e retorno do resultado.
    """
    img_result = await gemini_vision.fetch_image(media_url)
    if not img_result.success:
        msg.body(img_result.error_message)
        return None

    gemini_result = await gemini_vision.perform_gemini(img_result.data)
    if not gemini_result.success:
        msg.body(gemini_result.error_message)
        return None

    return gemini_result.data


@router.post('/predict_twilio_190', status_code=status.HTTP_200_OK)
async def predict_twilio_190(request: Request):
    """
    Endpoint para processar mensagens de texto, áudio, imagem ou localização recebidas via Twilio.
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
        user_input = location_data

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
    else:
        user_input = form_data.get('Body')

    agent_result = await agent.generate_text_response(user_input, session_id)
    if not agent_result.success:
        msg.body(agent_result.error_message)
        return Response(content=str(resp), media_type='application/xml')

    message_type = 'text'

    if latitude and longitude:
        message_type = 'location'
    elif num_media > 0:
        media_content_type = form_data.get('MediaContentType0', '')
        if 'audio' in media_content_type:
            message_type = 'audio'
        elif 'image' in media_content_type:
            message_type = 'image'

    request.state.bq_data = {
        'session_id': session_id,
        'user_input': user_input,
        'response': agent_result.data,
        'message_type': message_type,
    }

    msg.body(agent_result.data)
    return Response(content=str(resp), media_type='application/xml')
