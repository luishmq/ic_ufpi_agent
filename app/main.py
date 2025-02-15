import asyncio
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_504_GATEWAY_TIMEOUT

from api.v1.api import api_router
from schemas.healthcheck import HealthCheck
from crud.features.history_bq import BigQueryStorage

REQUEST_TIMEOUT_ERROR = 300

bq_storage = BigQueryStorage()

app = FastAPI(
    title='API ChatBot Gen AI - SSP',
    openapi_url='/api/v1/openapi.json',
    openapi_tags=[
        {'name': 'Healthcheck', 'description': 'Healthcheck Endpoint'},
        {'name': 'Agent Twilio 190', 'description': 'Agente Twilio para o serviço 190'},
    ],
)


@app.middleware('http')
async def process_time_and_timeout_middleware(request: Request, call_next):
    start_time = time.time()
    request.state.response_time = None
    try:
        response = await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT_ERROR)
    except asyncio.TimeoutError:
        process_time = time.time() - start_time
        return JSONResponse(
            {'detail': f'Request processing time exceeded limit ({process_time:.3f} seconds)'},
            status_code=HTTP_504_GATEWAY_TIMEOUT,
        )
    process_time = time.time() - start_time

    print(f'Tempo de resposta: {process_time:.3f} segundos')

    if hasattr(request.state, 'bq_data'):
        bq_data = request.state.bq_data  
        bq_data['response_time'] = process_time

        await bq_storage.store_response(
            dataset_id='history',
            table_id='chats',
            session_id=bq_data['session_id'],
            user_input=bq_data['user_input'],
            response=bq_data['response'],
            response_time=bq_data['response_time']
        )

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/', response_model=HealthCheck, tags=['Healthcheck'])
async def healthcheck(request: Request):
    return {'message': 'OK'}


app.include_router(api_router, prefix='/api/v1')
