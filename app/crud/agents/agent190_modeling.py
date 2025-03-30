from datetime import date
from langchain_core.messages import HumanMessage, AIMessage
from utils.prompts import PROMPT_190
from utils.result import Result
from crud.adapters.adapter import LangChainLLMAdapter
from crud.managers.llm_manager import LLMManager


class SessionManager:
    """
    Classe responsável pelo gerenciamento do histórico de sessões.

    Attributes:
        store (dict): Dicionário para armazenar os históricos das sessões.
    """

    def __init__(self):
        self.store = {}

    def get_session_history(self, session_id: str) -> Result:
        """
        Retorna o histórico de uma sessão ou cria uma nova sessão se não existir.

        Args:
            session_id (str): ID da sessão.

        Returns:
            Result: Objeto Result contendo sucesso e o histórico da sessão.
        """
        if session_id not in self.store:
            self.store[session_id] = []
        return Result.ok(data=self.store[session_id])

    def update_session_history(self, session_id: str, message) -> Result:
        """
        Atualiza o histórico da sessão com uma nova mensagem.

        Args:
            session_id (str): ID da sessão.
            message: Mensagem a ser adicionada.

        Returns:
            Result: Objeto Result indicando sucesso ou erro.
        """
        history_result = self.get_session_history(session_id)
        if not history_result.success:
            return Result.fail(error_message='Erro ao obter histórico da sessão')

        history = history_result.data
        history.append(message)
        return Result.ok()


class Agent190:
    def __init__(self, session_manager: SessionManager, llm_adapter: LangChainLLMAdapter):
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
