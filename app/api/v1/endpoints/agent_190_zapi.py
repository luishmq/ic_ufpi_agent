# import os
# import json
# import tempfile

# from dotenv import load_dotenv
# from fastapi import APIRouter, Request, Response, status, HTTPException
# import httpx

# from crud.agents.agent190_modeling import Agent190, SessionManager
# from crud.features.audio_transcript import AudioDownloader, AudioConverter, AudioTranscriber, CloudUploader
# from crud.features.history_bq import BigQueryStorage
# from crud.features.gemini_vision import GeminiVision
# from crud.features.maps import geocode_reverse
# from langchain_openai import ChatOpenAI
# from langchain_ollama import ChatOllama
# from langchain_anthropic import ChatAnthropic

# from crud.adapters.factory import LLMFactory
# from crud.managers.llm_manager import LLMManager
# from crud.tools.tools import Tools

# load_dotenv()

# ZAPI_API_KEY = os.getenv('ZAPI_API_KEY')
# ZAPI_BASE_URL = os.getenv('ZAPI_BASE_URL', 'https://api.z-api.io/instances')
# ZAPI_INSTANCE_ID = os.getenv('ZAPI_INSTANCE_ID')
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# router = APIRouter()

# session_manager = SessionManager()
# tools_instance = Tools()

# # Usando o LLMManager para criar e gerenciar adaptadores LLM
# llm_manager = LLMManager()
# factory_result = llm_manager.create_adapter(
#     model_type='anthropic',
#     tools=tools_instance,
#     api_key=ANTHROPIC_API_KEY,
#     model_name='claude-3-5-haiku-20241022',
#     temperature=0.2
# )

# if not factory_result.success:
#     # Tratamento de erro caso a factory falhe
#     raise Exception(f"Erro ao criar adaptador LLM: {factory_result.error_message}")

# agent = Agent190(session_manager=session_manager, llm_adapter=factory_result.data)
# cloud_uploader = CloudUploader(bucket_name='audios_ssp')
# gemini_vision = GeminiVision()
# bq_storage = BigQueryStorage()


# class ZAPIClient:
#     """Cliente para interagir com a API do ZAPI."""

#     def __init__(self, instance_id, api_key, base_url):
#         self.instance_id = instance_id
#         self.api_key = api_key
#         self.base_url = base_url
#         self.url = f"{base_url}/{instance_id}"
#         self.headers = {"Content-Type": "application/json", "Client-Token": api_key}

#     async def download_media(self, media_url):
#         """Download de mídia usando o ZAPI."""
#         try:
#             async with httpx.AsyncClient() as client:
#                 response = await client.get(
#                     media_url,
#                     headers=self.headers,
#                     timeout=30
#                 )
#                 response.raise_for_status()
#                 return response.content
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=500, detail=f"Erro ao baixar mídia: {str(e)}")

#     async def send_message(self, to, message):
#         """Envia uma mensagem de texto via ZAPI."""
#         url = f"{self.url}/messages/text"
#         payload = {
#             "phone": to,
#             "message": message
#         }
#         try:
#             async with httpx.AsyncClient() as client:
#                 response = await client.post(
#                     url,
#                     headers=self.headers,
#                     json=payload,
#                     timeout=30
#                 )
#                 response.raise_for_status()
#                 return response.json()
#         except httpx.HTTPError as e:
#             raise HTTPException(status_code=500, detail=f"Erro ao enviar mensagem: {str(e)}")


# zapi_client = ZAPIClient(ZAPI_INSTANCE_ID, ZAPI_API_KEY, ZAPI_BASE_URL)


# async def process_audio(media_content, content_type):
#     """
#     Processa um arquivo de áudio, realizando a conversão para formato WAV,
#     upload para o Cloud Storage e transcrição do conteúdo.
#     """
#     with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
#         temp_file.write(media_content)
#         audio_path = temp_file.name

#     convert_result = await AudioConverter.convert_ogg_to_wav(audio_path)
#     if not convert_result.success:
#         return None, convert_result.error_message

#     upload_result = await cloud_uploader.upload_to_cloud_storage(convert_result.data, folder='audios_wav')
#     if not upload_result.success:
#         return None, upload_result.error_message

#     transcribe_result = await AudioTranscriber.transcribe_audio(convert_result.data)
#     if not transcribe_result.success:
#         return None, transcribe_result.error_message

#     return transcribe_result.data, None


# async def process_image(media_content):
#     """
#     Processa uma imagem, realizando a interpretação com Gemini e retorno do resultado.
#     """
#     with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
#         temp_file.write(media_content)
#         img_path = temp_file.name

#     gemini_result = await gemini_vision.perform_gemini_local(img_path)
#     if not gemini_result.success:
#         return None, gemini_result.error_message

#     return gemini_result.data, None


# @router.post('/webhook_zapi', status_code=status.HTTP_200_OK)
# async def webhook_zapi(request: Request):
#     """
#     Endpoint para processar webhooks do ZAPI.

#     Este endpoint recebe mensagens de texto, áudio, imagens ou localização via ZAPI,
#     processa esses dados e envia respostas de volta para o usuário.
#     """
#     try:
#         data = await request.json()

#         # Verificação de desafio para confirmar webhook
#         if "challenge" in data:
#             return {"challenge": data["challenge"]}

#         # Ignorar mensagens que não são de chat
#         if "event" not in data or data["event"] != "message":
#             return {"status": "ignored", "reason": "Not a message event"}

#         message = data.get("message", {})
#         from_number = message.get("from", "").replace("@c.us", "")
#         session_id = from_number

#         # Extrair tipo de mensagem e conteúdo
#         message_type = message.get("type", "")

#         if message_type == "location":
#             # Processamento de localização
#             location = message.get("location", {})
#             latitude = location.get("latitude")
#             longitude = location.get("longitude")

#             geocode_result = await geocode_reverse(latitude, longitude)
#             if not geocode_result.success:
#                 await zapi_client.send_message(
#                     from_number,
#                     f'Erro ao obter endereço: {geocode_result.error_message}'
#                 )
#                 return {"status": "error", "message": geocode_result.error_message}

#             user_input = f'Localização recebida:\nEndereço: {geocode_result.data}'

#         elif message_type == "audio":
#             # Processamento de áudio
#             media_url = message.get("mediaUrl")
#             media_content = await zapi_client.download_media(media_url)

#             user_input, error = await process_audio(media_content, message.get("mimetype"))
#             if error:
#                 await zapi_client.send_message(from_number, f'Erro ao processar áudio: {error}')
#                 return {"status": "error", "message": error}

#         elif message_type == "image":
#             # Processamento de imagem
#             media_url = message.get("mediaUrl")
#             media_content = await zapi_client.download_media(media_url)

#             user_input, error = await process_image(media_content)
#             if error:
#                 await zapi_client.send_message(from_number, f'Erro ao processar imagem: {error}')
#                 return {"status": "error", "message": error}

#         elif message_type == "text":
#             # Processamento de texto simples
#             user_input = message.get("body", "")

#         else:
#             # Tipo de mensagem não suportado
#             await zapi_client.send_message(from_number, 'Tipo de mensagem não suportado.')
#             return {"status": "error", "message": "Unsupported message type"}

#         # Gerar resposta usando o agente
#         agent_result = await agent.generate_text_response(user_input, session_id)

#         if not agent_result.success:
#             await zapi_client.send_message(from_number, agent_result.error_message)
#             return {"status": "error", "message": agent_result.error_message}

#         # Armazenar dados na BigQuery
#         request.state.bq_data = {
#             'session_id': session_id,
#             'user_input': user_input,
#             'response': agent_result.data,
#             'message_type': message_type,  # Já contém o tipo correto (text, audio, image, location)
#         }

#         # Enviar resposta
#         await zapi_client.send_message(from_number, agent_result.data)

#         return {"status": "success"}

#     except Exception as e:
#         return {"status": "error", "message": str(e)}
