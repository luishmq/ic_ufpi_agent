from fastapi import APIRouter, Request, Response, status
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from crud.agent190_modeling import Agent190, SessionManager
from crud.audio_transcript import AudioDownloader, AudioConverter, AudioTranscriber, CloudUploader
from crud.history_bq import BigQueryStorage
from crud.vision_ocr import OCRProcessor
from utils.globals import (
    ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY
)

router = APIRouter()

session_manager = SessionManager()
agent = Agent190(OPENAI_API_KEY, session_manager)
cloud_uploader = CloudUploader(bucket_name='audios_ssp')
ocr_processor = OCRProcessor()
bq_storage = BigQueryStorage()

client = Client(ACCOUNT_SID, TWILIO_AUTH_TOKEN)

async def process_audio(media_url, msg, resp):
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
    Endpoint para processar mensagens de texto ou áudio recebidas via Twilio.

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

    if num_media > 0:
        media_url = form_data.get('MediaUrl0')

        user_input = await process_audio(media_url, msg, resp)
        if not user_input:  
            return Response(content=str(resp), media_type='application/xml')

        if user_input is None:
            user_input = await process_image(media_url, msg, resp)
            if not user_input:  
                return Response(content=str(resp), media_type='application/xml')

        return await handle_response(user_input, session_id, msg, resp)

    else:
        incoming_msg = form_data.get('Body')
        return await handle_response(incoming_msg, session_id, msg, resp)