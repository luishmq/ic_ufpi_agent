from crud.adapters.adapter import LangChainLLMAdapter
from utils.result import Result


class LLMManager:
    def __init__(self, llm_adapter: LangChainLLMAdapter):
        self.llm_adapter = llm_adapter

    def set_adapter(self, llm_adapter: LangChainLLMAdapter):
        self.llm_adapter = llm_adapter

    def generate_response(self, input_text: str, chat_history: list, context: dict) -> Result:
        return self.llm_adapter.generate_response(input_text, chat_history, context)
