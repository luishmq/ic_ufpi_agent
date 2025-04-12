import redis
import json

from datetime import date
from langchain_core.messages import HumanMessage, AIMessage
from utils.prompts import PROMPT_190
from utils.result import Result
from crud.adapters.adapter import LangChainLLMAdapter
from crud.managers.llm_manager import LLMManager


class RedisSessionManager:
    """
    Gerenciador de sessões utilizando Redis como armazenamento.

    Esta classe fornece métodos para persistir e recuperar históricos de conversas
    entre sessões, utilizando o Redis como backend de armazenamento.

    Attributes:
        client (redis.Redis): Cliente Redis para interação com o servidor.
        key_prefix (str): Prefixo utilizado nas chaves Redis para organização.
        expiry_seconds (int): Tempo de expiração em segundos para as sessões.
    """

    def __init__(
        self,
        host: str,
        port: int,
        password: str,
        ssl: bool = True,
        key_prefix: str = 'session_history:',
        expiry_seconds: int = 86400,
    ):
        """
        Inicializa o gerenciador de sessões Redis.

        Args:
            host (str): Endereço do servidor Redis.
            port (int): Porta do servidor Redis.
            password (str): Senha para autenticação no Redis.
            ssl (bool, opcional): Se deve usar SSL na conexão. Padrão é True.
            key_prefix (str, opcional): Prefixo para as chaves no Redis. Padrão é 'session_history:'.
            expiry_seconds (int, opcional): Tempo de vida dos dados em segundos. Padrão é 86400 (24 horas).
        """
        self.client = redis.Redis(host=host, port=port, password=password, ssl=ssl)
        self.key_prefix = key_prefix
        self.expiry_seconds = expiry_seconds

    def test_connection(self) -> Result:
        """
        Testa a conexão com o servidor Redis.

        Returns:
            Result: Objeto indicando sucesso ou falha na conexão.
        """
        try:
            self.client.ping()
            return Result.ok()
        except Exception as e:
            return Result.fail(error_message=f'Erro ao conectar ao Redis: {str(e)}')

    def get_session_history(self, session_id: str) -> Result:
        """
        Recupera o histórico de uma sessão pelo ID.

        Args:
            session_id (str): Identificador único da sessão.

        Returns:
            Result: Objeto contendo o histórico da sessão ou erro.
        """
        if not session_id:
            return Result.fail(error_message='ID de sessão inválido')

        key = f'{self.key_prefix}{session_id}'
        try:
            data = self.client.get(key)
            if data is None:
                history = []
            else:
                history = json.loads(data)
            return Result.ok(data=history)
        except json.JSONDecodeError as e:
            return Result.fail(error_message=f'Erro ao decodificar histórico: {str(e)}')
        except Exception as e:
            return Result.fail(error_message=f'Erro ao recuperar histórico: {str(e)}')

    def update_session_history(self, session_id: str, message) -> Result:
        """
        Atualiza o histórico de uma sessão adicionando uma nova mensagem.

        Args:
            session_id (str): Identificador único da sessão.
            message: A mensagem a ser adicionada ao histórico.

        Returns:
            Result: Objeto indicando sucesso ou falha na operação.
        """
        if not session_id:
            return Result.fail(error_message='ID de sessão inválido')

        key = f'{self.key_prefix}{session_id}'
        history_result = self.get_session_history(session_id)
        if not history_result.success:
            return Result.fail(error_message='Erro ao obter histórico da sessão')

        history = history_result.data
        message_data = message.dict() if hasattr(message, 'dict') else str(message)
        history.append(message_data)

        try:
            self.client.set(key, json.dumps(history), ex=self.expiry_seconds)
            return Result.ok()
        except Exception as e:
            return Result.fail(error_message=f'Erro ao atualizar histórico: {str(e)}')


class Agent190:
    def __init__(self, session_manager: RedisSessionManager, llm_adapter: LangChainLLMAdapter):
        """
        Inicializa uma instância do agente de atendimento 190.

        Args:
            session_manager (SessionManager): Gerenciador para manter o histórico das sessões.
            llm_adapter (LangChainLLMAdapter): Adaptador para o modelo de linguagem.
        """
        self.session_manager = session_manager
        self.llm_manager = LLMManager(llm_adapter)

    async def generate_text_response(self, input_text: str, session_id: str) -> Result:
        """
        Gera uma resposta de texto com base na entrada do usuário e no histórico da sessão.

        Args:
            input_text (str): Texto de entrada do usuário.
            session_id (str): Identificador da sessão.

        Returns:
            Result: Objeto contendo sucesso/falha e a resposta gerada.
        """
        if not input_text or not session_id:
            return Result.fail(error_message='Input inválido.')

        try:
            history_result = self.session_manager.get_session_history(session_id)
            if not history_result.success:
                return Result.fail(error_message='Erro ao obter histórico da sessão')

            chat_history = history_result.data

            context = {
                'date': date.today(),
                'system_prompt': PROMPT_190,
            }

            response_result = self.llm_manager.generate_response(input_text, chat_history, context)
            if not response_result.success:
                return Result.fail(error_message=response_result.error_message)

            user_update_result = self.session_manager.update_session_history(
                session_id, HumanMessage(content=input_text)
            )
            if not user_update_result.success:
                return Result.fail(error_message='Erro ao atualizar histórico com a mensagem do usuário')

            ai_update_result = self.session_manager.update_session_history(
                session_id, AIMessage(content=response_result.data)
            )
            if not ai_update_result.success:
                return Result.fail(error_message='Erro ao atualizar histórico com a resposta da IA')

            return Result.ok(data=response_result.data)

        except Exception as e:
            return Result.fail(error_message=f'Ocorreu um erro: {str(e)}')
