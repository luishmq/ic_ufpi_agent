from fastapi import APIRouter, Request, Response, status
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from crud.agent190_modeling import Agent190
from crud.audio_transcript import transcript_audio
from crud.history_bq import store_response
from utils.globals import (
    ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    OPENAI_API_KEY,
)

router = APIRouter()

agent = Agent190(OPENAI_API_KEY)

client = Client(ACCOUNT_SID, TWILIO_AUTH_TOKEN)


@router.post('/predict_twilio_190', status_code=status.HTTP_200_OK)
async def predict_twilio_190(request: Request):
    form_data = await request.form()
    num_media = form_data.get('NumMedia')
    from_number = form_data.get('From')
    session_id = from_number

    if int(num_media) > 0:
        media_url = form_data.get('MediaUrl0')

        resp = MessagingResponse()
        msg = resp.message()

        result = await transcript_audio(media_url, from_number)
        response = await agent.generate_text_response(result, session_id)
        await store_response('chat_history', 'history', session_id, result, response)
        msg.body(response)
        return Response(content=str(resp), media_type='application/xml')
    else:
        incoming_msg = form_data.get('Body')

        resp = MessagingResponse()
        msg = resp.message()

        response = await agent.generate_text_response(incoming_msg, session_id)
        await store_response('chat_history', 'history', session_id, incoming_msg, response)
        msg.body(response)
        return Response(content=str(resp), media_type='application/xml')
