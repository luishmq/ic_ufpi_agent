from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder
from utils.result import Result


class LangChainLLMAdapter:
    """
    Adaptador genérico para modelos compatíveis com LangChain (OpenAI, Ollama, VertexAI, etc.).
    """

    def __init__(self, llm):
        """
        Inicializa o adaptador com uma instância do modelo LangChain.

        Args:
            llm: Instância do modelo LangChain (ex.: ChatOpenAI, ChatOllama).
        """
        self.llm = llm

    def generate_response(self, input_text: str, chat_history: list, context: dict) -> Result:
        """
        Gera uma resposta do modelo.

        Args:
            input_text (str): Texto de entrada do usuário.
            chat_history (list): Histórico do chat.
            context (dict): Contexto adicional, como prompts ou data.

        Returns:
            Result: Resultado contendo sucesso ou falha e a resposta gerada.
        """
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ('system', context.get('system_prompt', '')),
                    MessagesPlaceholder(variable_name='chat_history'),
                    ('human', '{input}'),
                ]
            )

            parser = StrOutputParser()
            chain = prompt | self.llm | parser

            response = chain.invoke({'input': input_text, 'chat_history': chat_history, 'data': context.get('date')})

            return Result.ok(data=response)
        except Exception as e:
            return Result.fail(error_message=f'Erro ao gerar resposta: {str(e)}')
