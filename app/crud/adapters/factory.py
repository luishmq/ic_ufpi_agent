from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI
from langchain_deepseek import ChatDeepSeek
from langchain_community.chat_models import ChatMaritalk
from utils.result import Result
from crud.adapters.adapter import LangChainLLMAdapter


class LLMFactory:
    """
    Factory para criar e gerenciar diferentes adaptadores de modelos LLM.
    Implementa o padrão Factory Method para criar instâncias dos adaptadores.
    """

    @staticmethod
    def create_llm_adapter(model_type: str, tools, **config) -> Result:
        """
        Cria um adaptador para o modelo especificado com base no tipo e configuração fornecidos.

        Args:
            model_type (str): Tipo de modelo a ser criado ('openai', 'anthropic', 'ollama', 'vertexai')
            tools: Instância de ferramentas a serem utilizadas pelo modelo
            **config: Configurações específicas para o modelo (como api_key, model_name, temperature, etc.)

        Returns:
            Result: Objeto Result contendo o adaptador criado ou uma mensagem de erro
        """
        try:
            if model_type.lower() == 'openai':
                model_name = config.get('model_name', 'gpt-4o')
                temperature = config.get('temperature', 0.7)
                api_key = config.get('api_key')

                llm = ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)
                adapter = LangChainLLMAdapter(llm=llm, tools=tools)
                return Result.ok(data=adapter)

            elif model_type.lower() == 'anthropic':
                model_name = config.get('model_name', 'claude-3-5-haiku-20241022')
                temperature = config.get('temperature', 0.7)
                api_key = config.get('api_key')

                llm = ChatAnthropic(model=model_name, temperature=temperature, api_key=api_key)
                adapter = LangChainLLMAdapter(llm=llm, tools=tools)
                return Result.ok(data=adapter)

            elif model_type.lower() == 'ollama':
                model_name = config.get('model_name', 'llama3.1')
                temperature = config.get('temperature', 0.7)

                llm = ChatOllama(model=model_name, temperature=temperature)
                adapter = LangChainLLMAdapter(llm=llm, tools=tools)
                return Result.ok(data=adapter)

            elif model_type.lower() == 'vertexai':
                model_name = config.get('model_name', 'gemini-2.0-flash')
                temperature = config.get('temperature', 0.7)
                project = config.get('project')

                llm = ChatVertexAI(model=model_name, temperature=temperature, project=project)
                adapter = LangChainLLMAdapter(llm=llm, tools=tools)
                return Result.ok(data=adapter)
            elif model_type.lower() == 'deepseek':
                model_name = config.get('model_name', 'deepseek-chat')
                temperature = config.get('temperature', 0.7)
                api_key = config.get('api_key')

                llm = ChatDeepSeek(model=model_name, temperature=temperature, api_key=api_key)
                adapter = LangChainLLMAdapter(llm=llm, tools=tools)
                return Result.ok(data=adapter)
            elif model_type.lower() == 'maritalk':
                model_name = config.get('model_name', 'sabia-2-medium')
                temperature = config.get('temperature', 0.7)
                api_key = config.get('api_key')

                llm = ChatMaritalk(model=model_name, temperature=temperature, api_key=api_key)
                adapter = LangChainLLMAdapter(llm=llm, tools=tools)
                return Result.ok(data=adapter)
            else:
                return Result.fail(error_message=f"Tipo de modelo '{model_type}' não suportado")

        except Exception as e:
            return Result.fail(error_message=f'Erro ao criar adaptador LLM: {str(e)}')
