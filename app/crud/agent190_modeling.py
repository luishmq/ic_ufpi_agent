from datetime import date
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from utils.prompts import PROMPT_190
from utils.result import Result


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
    """
    Classe para interagir com o modelo de linguagem Anthropic.

    Attributes:
        llm: Instância do modelo de linguagem.
        session_manager (SessionManager): Gerenciador de histórico de sessões.
    """

    def __init__(self, token: str, session_manager: SessionManager):
        self.llm = ChatOpenAI(temperature=0.2, model='gpt-4o-mini', api_key=token)
        self.session_manager = session_manager

    async def generate_text_response(self, input_text: str, session_id: str) -> Result:
        """
        Gera uma resposta de texto com base no input do usuário.

        Args:
            input_text (str): Texto de entrada do usuário.
            session_id (str): ID da sessão.

        Returns:
            Result: Objeto Result contendo sucesso ou erro e a resposta gerada.
        """
        if not input_text or not session_id:
            return Result.fail(error_message='Input inválido. Tente novamente com um texto válido.')

        try:
            history_result = self.session_manager.get_session_history(session_id)
            if not history_result.success:
                return Result.fail(error_message='Erro ao obter histórico da sessão')

            chat_history = history_result.data

            text_prompt = ChatPromptTemplate.from_messages(
                [
                    ('system', PROMPT_190),
                    MessagesPlaceholder(variable_name='chat_history'),
                    ('human', '{input}'),
                ]
            )

            data_atual = date.today()
            parser = StrOutputParser()
            chain = text_prompt | self.llm | parser

            response = chain.invoke({'input': input_text, 'chat_history': chat_history, 'data': data_atual})

            update_user_result = self.session_manager.update_session_history(
                session_id, HumanMessage(content=input_text)
            )
            if not update_user_result.success:
                return Result.fail(error_message='Erro ao atualizar histórico com a mensagem do usuário')

            update_ai_result = self.session_manager.update_session_history(session_id, AIMessage(content=response))
            if not update_ai_result.success:
                return Result.fail(error_message='Erro ao atualizar histórico com a resposta da IA')

            return Result.ok(data=response)

        except Exception:
            return Result.fail(
                error_message='Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde.'
            )
