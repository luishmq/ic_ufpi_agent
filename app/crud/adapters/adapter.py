import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent

from langchain_openai import ChatOpenAI
# from langchain_ollama import ChatOllama
# from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI
from langchain_deepseek import ChatDeepSeek
from utils.result import Result

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

class LangChainLLMAdapter:
    """
    Adaptador genérico para modelos compatíveis com LangChain.

    Esta classe encapsula a lógica de geração de respostas para diferentes
    modelos de linguagem como OpenAI, Anthropic, VertexAI, etc.

    Attributes:
        llm: Instância do modelo LangChain configurado.
        tools: Ferramentas disponíveis para o modelo utilizar.
    """

    def __init__(self, llm, tools):
        """
        Inicializa o adaptador com uma instância do modelo LangChain e um conjunto de ferramentas.

        Args:
            llm: Instância do modelo LangChain (ex.: ChatOpenAI, ChatOllama).
            tools: Instância de Tools (ou similar) que contenha as ferramentas necessárias.
        """
        self.llm = llm
        self.tools = tools

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
                    MessagesPlaceholder(variable_name='agent_scratchpad'),
                ]
            )

            agent = create_tool_calling_agent(llm=self.llm, tools=[self.tools.get_person_data_tool], prompt=prompt)

            agent_executor = AgentExecutor(agent=agent, tools=[self.tools.get_person_data_tool], verbose=True)

            response = agent_executor.invoke(
                {'input': input_text, 'chat_history': chat_history, 'data': context.get('date')}
            )

            if isinstance(self.llm, (ChatDeepSeek, ChatVertexAI, ChatOpenAI)):
                return Result.ok(data=response['output'])
            
            logger.info(f"Response from model: {response}")

            return Result.ok(data=response['output'][0]['text'])
        except Exception as e:
            return Result.fail(error_message=f'Erro ao gerar resposta: {str(e)}')
