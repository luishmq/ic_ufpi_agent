from fastapi import APIRouter

from api.v1.endpoints import agent, agent_190_twilio

api_router = APIRouter()
api_router.include_router(agent.router, prefix='/agent', tags=['Agent'])
api_router.include_router(agent_190_twilio.router, prefix='/agent_twilio_190', tags=['Agent Twilio 190'])
