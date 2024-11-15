import asyncio
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_504_GATEWAY_TIMEOUT

from api.v1.api import api_router
from schemas.healthcheck import HealthCheck

REQUEST_TIMEOUT_ERROR = 300

app = FastAPI(
    title='API ChatBot Gen AI - SSP',
    openapi_url='/api/v1/openapi.json',
    openapi_tags=[
        {'name': 'Healthcheck', 'description': 'Healthcheck Endpoint'},
        {'name': 'Agent Twilio 190', 'description': 'Agente Twilio para o serviço 190'},
    ],
)


@app.middleware('http')
async def timeout_middleware(request: Request, call_next):
    try:
        start_time = time.time()
        response = await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT_ERROR)
        return response
    except asyncio.TimeoutError:
        process_time = time.time() - start_time
        return JSONResponse(
            {'detail': f'Request processing time exceeded limit ({process_time})'},
            status_code=HTTP_504_GATEWAY_TIMEOUT,
        )


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
