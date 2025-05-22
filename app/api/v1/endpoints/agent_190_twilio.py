import asyncio
import logging
from typing import Optional

import uuid
from fastapi import APIRouter, Request, Response, status, Depends, HTTPException
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from crud.agents.agent190_modeling import Agent190, RedisSessionManager
from crud.features.audio_transcript import (
    AudioDownloader,
    AudioConverter,
    AudioTranscriber,
    CloudUploader,
)
from crud.features.gemini_vision import GeminiVision
from crud.features.maps import geocode_reverse

from api.v1.dependencies import (
    get_twilio_client,
    get_agent,
    get_gemini_vision,
    get_cloud_uploader,
    get_session_manager,
    settings,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()]
)

router = APIRouter()


@router.post('/init_session', status_code=status.HTTP_200_OK)
async def init_session(session_manager: RedisSessionManager = Depends(get_session_manager)):
    """Rota de inicialização da sessão.

    Cria um novo ID de sessão e testa a conexão com o Redis.

    Args:
        session_manager (RedisSessionManager): Gerenciador de sessões do Redis.

    Returns:
        dict: Informações da sessão iniciada.

    Raises:
        HTTPException: Se não for possível conectar ao Redis.
    """
    conn_result = session_manager.test_connection()
    if not conn_result.success:
        raise HTTPException(
            status_code=503,
            detail=f'Erro ao conectar ao serviço de armazenamento de sessões: {conn_result.error_message}',
        )

    session_id = str(uuid.uuid4())
    return {'session_id': session_id}


async def send_twilio_message(to_number: str, body_text: str, client: Client = Depends(get_twilio_client)):
    """
    Envia mensagem para o usuário via Twilio API (outbound).

    Args:
        to_number (str): Número do destinatário no formato 'whatsapp:+55...'
        body_text (str): Texto da mensagem a ser enviada.
        client (Client): Cliente Twilio para envio da mensagem.
    """
    try:
        message = client.messages.create(body=body_text, from_=settings.twilio_whatsapp_number, to=to_number)
        logger.info(f'Mensagem enviada via Twilio: SID={message.sid}')
    except Exception as e:
        logger.exception(f'Falha ao enviar mensagem Twilio: {e}')


async def process_audio_in_background(
    ogg_path: str,
    from_number: str,
    session_id: str,
    send_message_func,
    agent: Agent190,
    cloud_uploader: CloudUploader,
):
    """
    Processa o áudio de forma assíncrona.

    Args:
        ogg_path (str): Caminho para o arquivo de áudio OGG baixado.
        from_number (str): Número do remetente no formato Twilio.
        session_id (str): ID da sessão para manter contexto da conversa.
        send_message_func: Função para enviar mensagens de resposta.
        agent (Agent190): Instância do agente para processar o texto transcrito.
        cloud_uploader (CloudUploader): Uploader para armazenar o arquivo na nuvem.
    """
    try:
        convert_result = await AudioConverter.convert_ogg_to_wav(ogg_path)
        if not convert_result.success:
            await send_message_func(from_number, convert_result.error_message)
            return

        wav_path = convert_result.data

        upload_result = await cloud_uploader.upload_to_cloud_storage(wav_path, folder='audios_wav')
        if not upload_result.success:
            await send_message_func(from_number, upload_result.error_message)
            return

        transcribe_result = await AudioTranscriber.transcribe_audio(wav_path)
        if not transcribe_result.success:
            await send_message_func(from_number, transcribe_result.error_message)
            return

        user_input = transcribe_result.data

        agent_result = await agent.generate_text_response(user_input, session_id)
        if not agent_result.success:
            await send_message_func(from_number, agent_result.error_message)
            return

        ai_response = agent_result.data
        logger.info(f'Enviando resposta de áudio processado para sessão {session_id}')
        await send_message_func(from_number, ai_response)

    except Exception as e:
        logger.exception(f'Erro ao processar áudio: {e}')
        await send_message_func(from_number, f'Erro ao processar áudio: {str(e)}')


@router.post('/predict_twilio_190', status_code=status.HTTP_200_OK)
async def predict_twilio_190(
    request: Request,
    response: Response,
    twilio_client: Client = Depends(get_twilio_client),
    agent: Agent190 = Depends(get_agent),
    gemini_vision: GeminiVision = Depends(get_gemini_vision),
    cloud_uploader: CloudUploader = Depends(get_cloud_uploader),
):
    """
    Endpoint que recebe e processa mensagens do WhatsApp via Twilio.

    Args:
        request (Request): Objeto de requisição FastAPI.
        response (Response): Objeto de resposta FastAPI.
        twilio_client (Client): Cliente da API Twilio.
        agent (Agent190): Instância do agente de atendimento.
        gemini_vision (GeminiVision): Serviço de visão computacional.
        cloud_uploader (CloudUploader): Serviço de upload para nuvem.

    Returns:
        Response: Resposta TwiML formatada para o Twilio.

    Note:
        Suporta mensagens de texto, imagem, localização e áudio.
        Áudio é processado de forma assíncrona.
        Define `request.state.bq_data` para registrar no BigQuery via middleware.
    """
    form_data = await request.form()
    num_media = int(form_data.get('NumMedia', 0))
    from_number = form_data.get('From')
    session_id = from_number

    resp = MessagingResponse()
    msg = resp.message()

    latitude = form_data.get('Latitude')
    longitude = form_data.get('Longitude')
    user_input: Optional[str] = None
    agent_response: Optional[str] = None
    message_type = 'text'

    if latitude and longitude:
        message_type = 'location'
        geocode_result = await geocode_reverse(latitude, longitude)
        if not geocode_result.success:
            error = f'Erro ao obter endereço: {geocode_result.error_message}'
            msg.body(error)
            request.state.bq_data = {
                'session_id': session_id,
                'user_input': f'Lat:{latitude}, Lng:{longitude}',
                'response': error,
                'message_type': message_type,
            }
            return Response(content=str(resp), media_type='application/xml')

        user_input = f'Localização recebida:\nEndereço: {geocode_result.data}'
        agent_result = await agent.generate_text_response(user_input, session_id)
        if not agent_result.success:
            error = agent_result.error_message
            msg.body(error)
            request.state.bq_data = {
                'session_id': session_id,
                'user_input': user_input,
                'response': error,
                'message_type': message_type,
            }
            return Response(content=str(resp), media_type='application/xml')

        ai_response = agent_result.data
        agent_response = ai_response
        protocol_number = None

        msg.body(agent_response)

        request.state.bq_data = {
            'session_id': session_id,
            'user_input': user_input,
            'response': agent_response,
            'message_type': message_type,
            'protocol': protocol_number,
        }
        return Response(content=str(resp), media_type='application/xml')

    elif num_media > 0:
        media_url = form_data.get('MediaUrl0')
        media_content_type = form_data.get('MediaContentType0', '').lower()

        if 'audio' in media_content_type:
            message_type = 'audio'
            download_result = await AudioDownloader.download_audio(media_url)
            if not download_result.success:
                msg.body(download_result.error_message)
                request.state.bq_data = {
                    'session_id': session_id,
                    'user_input': 'Audio inbound - download error',
                    'response': download_result.error_message,
                    'message_type': message_type,
                }
                return Response(content=str(resp), media_type='application/xml')

            asyncio.create_task(
                process_audio_in_background(
                    ogg_path=download_result.data,
                    from_number=from_number,
                    session_id=session_id,
                    send_message_func=lambda to, text: send_twilio_message(to, text, twilio_client),
                    agent=agent,
                    cloud_uploader=cloud_uploader,
                )
            )

            user_input = 'Audio being processed offline'
            agent_response = 'N/A (will be generated async)'

            request.state.bq_data = {
                'session_id': session_id,
                'user_input': user_input,
                'response': agent_response,
                'message_type': message_type,
            }
            return Response(content=str(resp), media_type='application/xml')

        elif 'image' in media_content_type:
            message_type = 'image'
            img_result = await gemini_vision.fetch_image(media_url)
            if not img_result.success:
                msg.body(img_result.error_message)
                request.state.bq_data = {
                    'session_id': session_id,
                    'user_input': 'Image inbound - fetch error',
                    'response': img_result.error_message,
                    'message_type': message_type,
                }
                return Response(content=str(resp), media_type='application/xml')

            gemini_result = await gemini_vision.perform_gemini(img_result.data)
            if not gemini_result.success:
                msg.body(gemini_result.error_message)
                request.state.bq_data = {
                    'session_id': session_id,
                    'user_input': 'Image inbound - gemini error',
                    'response': gemini_result.error_message,
                    'message_type': message_type,
                }
                return Response(content=str(resp), media_type='application/xml')

            user_input = gemini_result.data
            agent_result = await agent.generate_text_response(user_input, session_id)
            if not agent_result.success:
                msg.body(agent_result.error_message)
                request.state.bq_data = {
                    'session_id': session_id,
                    'user_input': user_input,
                    'response': agent_result.error_message,
                    'message_type': message_type,
                }
                return Response(content=str(resp), media_type='application/xml')

            ai_response = agent_result.data
            agent_response = ai_response
            protocol_number = None

            msg.body(agent_response)
            request.state.bq_data = {
                'session_id': session_id,
                'user_input': user_input,
                'response': agent_response,
                'message_type': message_type,
                'protocol': protocol_number,
            }
            return Response(content=str(resp), media_type='application/xml')

        else:
            error = 'Tipo de mídia não suportado.'
            msg.body(error)
            request.state.bq_data = {
                'session_id': session_id,
                'user_input': 'Media inbound - not supported',
                'response': error,
                'message_type': 'unsupported',
            }
            return Response(content=str(resp), media_type='application/xml')

    else:
        message_type = 'text'
        user_input = form_data.get('Body', '')
        agent_result = await agent.generate_text_response(user_input, session_id)
        if not agent_result.success:
            error = agent_result.error_message
            msg.body(error)
            request.state.bq_data = {
                'session_id': session_id,
                'user_input': user_input,
                'response': error,
                'message_type': message_type,
            }
            return Response(content=str(resp), media_type='application/xml')

        ai_response = agent_result.data
        agent_response = ai_response
        protocol_number = None

        msg.body(agent_response)
        request.state.bq_data = {
            'session_id': session_id,
            'user_input': user_input,
            'response': agent_response,
            'message_type': message_type,
            'protocol': protocol_number,
        }
        return Response(content=str(resp), media_type='application/xml')
