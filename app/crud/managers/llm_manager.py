from crud.adapters.adapter import LangChainLLMAdapter
from crud.adapters.factory import LLMFactory
from utils.result import Result


class LLMManager:
    """
    Gerenciador de modelos LLM que implementa o padrão Strategy.
    """

    def __init__(self, llm_adapter: LangChainLLMAdapter = None):
        self.llm_adapter = llm_adapter
        self.current_model = None

    def set_adapter(self, llm_adapter: LangChainLLMAdapter):
        """
        Define o adaptador LLM a ser utilizado.

        Args:
            llm_adapter (LangChainLLMAdapter): Adaptador LLM a ser configurado.
        """
        self.llm_adapter = llm_adapter

    def create_adapter(self, model_type: str, tools, **config) -> Result:
        """
        Cria um novo adaptador usando a Factory e o configura como o adaptador atual.

        Args:
            model_type (str): Tipo do modelo ('openai', 'anthropic', 'ollama', 'vertexai')
            tools: Ferramentas a serem usadas pelo modelo
            **config: Configurações específicas do modelo

        Returns:
            Result: Resultado da operação
        """
        factory_result = LLMFactory.create_llm_adapter(model_type, tools, **config)

        if factory_result.success:
            self.llm_adapter = factory_result.data
            self.current_model = model_type
            return Result.ok(data=self.llm_adapter)

        return factory_result

    def generate_response(self, input_text: str, chat_history: list, context: dict) -> Result:
        """
        Gera uma resposta usando o adaptador atual.

        Args:
            input_text (str): Texto de entrada
            chat_history (list): Histórico da conversa
            context (dict): Contexto adicional

        Returns:
            Result: Resultado contendo a resposta ou mensagem de erro
        """
        if not self.llm_adapter:
            return Result.fail(error_message='Nenhum adaptador LLM configurado')

        return self.llm_adapter.generate_response(input_text, chat_history, context)
