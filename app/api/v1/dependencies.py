from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from twilio.rest import Client

from crud.agents.agent190_modeling import Agent190, SessionManager
from crud.features.audio_transcript import CloudUploader
from crud.features.gemini_vision import GeminiVision
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


def get_session_manager() -> SessionManager:
    """
    Cria e retorna um gerenciador de sessão.

    Returns:
        SessionManager: Instância do gerenciador de sessões.
    """
    return SessionManager()


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
        model_type='anthropic',
        tools=tools,
        api_key=settings.anthropic_api_key,
        model_name='claude-3-5-haiku-20241022',
        temperature=0.5,
    )
    if not factory_result.success:
        raise Exception(f'Erro ao criar adaptador LLM: {factory_result.error_message}')
    return factory_result.data


def get_agent(
    session_manager: SessionManager = Depends(get_session_manager), llm_adapter=Depends(get_llm_adapter)
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
