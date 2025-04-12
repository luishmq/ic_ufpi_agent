from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from twilio.rest import Client

from crud.agents.agent190_modeling import Agent190, RedisSessionManager
from crud.features.audio_transcript import CloudUploader
from crud.features.gemini_vision import GeminiVision
from crud.features.protocol_generator import ProtocolDetector, ProtocolGenerator
from crud.managers.llm_manager import LLMManager
from crud.tools.tools import Tools

load_dotenv()


class Settings(BaseSettings):
    project_id: str
    location: str
    langsmith_endpoint: str
    langsmith_project: str
    langsmith_tracing: bool
    langsmith_api_key: str
    account_sid: str
    twilio_auth_token: str
    openai_api_key: str
    anthropic_api_key: str
    deepseek_api_key: str
    xai_api_key: str
    bucket_name: str = 'audios_ssp'
    twilio_whatsapp_number: str = 'whatsapp:+14155238886'
    useraudio: str
    password: str
    google_maps_api_key: str
    base_url: str
    lupa_api_key: str
    redis_host: str
    redis_port: int = 6379
    redis_password: str
    redis_ssl: bool = True
    redis_key_prefix: str = 'session_history:'
    redis_expiry_seconds: int = 86400

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='allow',
    )


settings = Settings()


def get_twilio_client() -> Client:
    """
    Cria e retorna um cliente da API Twilio.

    Returns:
        Client: Cliente Twilio inicializado com as credenciais configuradas.
    """
    return Client(settings.account_sid, settings.twilio_auth_token)


def get_session_manager() -> RedisSessionManager:
    """
    Cria e retorna um gerenciador de sessões Redis.

    Utiliza as configurações de conexão definidas nas variáveis de ambiente
    para estabelecer uma conexão segura com o Redis.

    Returns:
        RedisSessionManager: Instância do gerenciador de sessões configurada.
    """
    return RedisSessionManager(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        ssl=settings.redis_ssl,
        key_prefix=settings.redis_key_prefix,
        expiry_seconds=settings.redis_expiry_seconds,
    )


def get_tools() -> Tools:
    """
    Cria e retorna um conjunto de ferramentas para uso pelos modelos LLM.

    Returns:
        Tools: Instância contendo as ferramentas disponíveis.
    """
    return Tools()


def get_llm_adapter(tools: Tools = Depends(get_tools)):
    """
    Cria e retorna um adaptador LLM usando a API Anthropic Claude.

    Args:
        tools (Tools): Conjunto de ferramentas a serem disponibilizadas para o modelo.

    Returns:
        LangChainLLMAdapter: Adaptador configurado para o modelo Claude.

    Raises:
        Exception: Se ocorrer um erro na criação do adaptador.
    """
    llm_manager = LLMManager()
    factory_result = llm_manager.create_adapter(
        model_type='vertexai',
        tools=tools,
        project=settings.project_id,
        model_name='gemini-2.0-flash',
        temperature=0.5,
    )
    if not factory_result.success:
        raise Exception(f'Erro ao criar adaptador LLM: {factory_result.error_message}')
    return factory_result.data


def get_agent(
    session_manager: RedisSessionManager = Depends(get_session_manager), llm_adapter=Depends(get_llm_adapter)
) -> Agent190:
    """
    Cria e retorna uma instância do agente de atendimento 190.

    Args:
        session_manager (SessionManager): Gerenciador de sessões para manter histórico.
        llm_adapter: Adaptador para o modelo de linguagem a ser utilizado.

    Returns:
        Agent190: Instância do agente configurada e pronta para uso.
    """
    return Agent190(session_manager=session_manager, llm_adapter=llm_adapter)


def get_cloud_uploader() -> CloudUploader:
    """
    Cria e retorna um uploader para o Google Cloud Storage.

    Returns:
        CloudUploader: Uploader configurado com o bucket especificado nas configurações.
    """
    return CloudUploader(bucket_name=settings.bucket_name)


def get_gemini_vision() -> GeminiVision:
    """
    Cria e retorna uma instância do serviço de visão computacional Gemini.

    Returns:
        GeminiVision: Instância do serviço Gemini Vision inicializada.
    """
    return GeminiVision()


def get_protocol_detector() -> ProtocolDetector:
    """
    Cria e retorna um detector de fim de atendimento.

    Returns:
        ProtocolDetector: Instância do detector configurada.
    """
    return ProtocolDetector(api_key=settings.openai_api_key)


def get_protocol_generator(protocol_detector: ProtocolDetector = Depends(get_protocol_detector)) -> ProtocolGenerator:
    """
    Cria e retorna um gerador de protocolos de atendimento.

    Args:
        protocol_detector (ProtocolDetector): Detector de finalização de atendimento.

    Returns:
        ProtocolGenerator: Instância do gerador de protocolos configurada.
    """
    return ProtocolGenerator(protocol_detector=protocol_detector)
