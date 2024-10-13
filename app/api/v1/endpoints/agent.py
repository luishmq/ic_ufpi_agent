from fastapi import APIRouter, HTTPException, Query, status
from google.cloud import storage
from crud.history_bq import store_response
from crud.agent_bo_modelling import AgentBO
from utils.globals import OPENAI_API_KEY, JSON_BUCKET

router = APIRouter()

agent = AgentBO(OPENAI_API_KEY)


@router.post('/predict', status_code=status.HTTP_200_OK)
async def predict(
    input: str = Query(..., description='Input do usuário.'),
    session_id: str = Query(..., description='ID da sessão.'),
) -> str:
    try:
        folder_name = f'BO_{session_id}'
        client = storage.Client()
        bucket = client.bucket(JSON_BUCKET)
        blobs = list(bucket.list_blobs(prefix=folder_name))
        file_index = len(blobs)

        json_response = await agent.generate_json_response(input, session_id)
        await agent.upload_to_gcs(JSON_BUCKET, json_response, folder_name, file_index)
        text_response = await agent.generate_text_response(json_response, session_id)
        await store_response('chat_history', 'history', session_id, input, text_response)

        return text_response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed: {str(e)}',
        ) from e
