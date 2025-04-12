import datetime
import random
import string
import logging

from langchain_openai import ChatOpenAI
from utils.result import Result

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

class ProtocolDetector:
    """
    Classe responsável por detectar o fim de atendimento e gerar protocolos.

    Utiliza um modelo LLM menor (como GPT-4o-mini) para analisar a última mensagem
    da LLM principal e determinar se o atendimento está sendo finalizado.

    Attributes:
        model (ChatOpenAI): Modelo de linguagem para detecção de fim de atendimento.
        api_key (str): Chave da API para o modelo.
    """

    def __init__(self, api_key: str, model_name: str = 'gpt-4o-mini'):
        """
        Inicializa o detector de protocolos com um modelo pequeno.

        Args:
            api_key (str): Chave da API do modelo.
            model_name (str): Nome do modelo a ser utilizado.
        """
        self.api_key = api_key
        self.model_name = model_name
        self.model = ChatOpenAI(model=self.model_name, api_key=self.api_key, temperature=0)

    async def detect_end_of_conversation(self, ai_response: str) -> Result:
        """
        Detecta se a mensagem do agente indica fim de atendimento.

        Args:
            ai_response (str): A resposta da LLM principal para analisar.

        Returns:
            Result: Objeto com informação se é fim de atendimento.
        """
        try:
            prompt = f"""
                Sua tarefa é analisar se esta mensagem de um atendente virtual de emergência 190 
                indica que o atendimento está sendo FINALIZADO. Responda APENAS com "sim" ou "não".
                
                Mensagem: {ai_response}
                
                Indícios de finalização:
                - Despedida final
                - Resumo do atendimento
                - Indicação de que as medidas necessárias foram tomadas (viatura a caminho, etc.)
                - Encerramento explícito do diálogo
                - Orientações finais
                
                Responda apenas "sim" se a mensagem indica claramente o fim do atendimento,
                ou "não" caso contrário.
            """

            response = await self.model.ainvoke(prompt)
            result = response.content.lower().strip()

            is_end = 'sim' in result
            return Result.ok(data=is_end)

        except Exception as e:
            logger.error(f'Erro na detecção de fim de atendimento: {str(e)}')
            return Result.fail(error_message=f'Erro na detecção: {str(e)}')


class ProtocolGenerator:
    """
    Classe responsável por gerar protocolos de atendimento.

    Gera números de protocolo para atendimentos finalizados e
    formata a mensagem final incluindo o protocolo.

    Attributes:
        protocol_detector (ProtocolDetector): Detector de fim de atendimento.
    """

    def __init__(self, protocol_detector: ProtocolDetector):
        """
        Inicializa o gerador de protocolos.

        Args:
            protocol_detector (ProtocolDetector): Detector de fim de atendimento.
        """
        self.protocol_detector = protocol_detector

    def _generate_protocol_number(self) -> str:
        """
        Gera um número de protocolo único baseado na data e hora atual.

        Returns:
            str: Número de protocolo gerado.
        """
        now = datetime.datetime.now()
        date_part = now.strftime('%Y%m%d-%H%M%S')

        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

        return f'190-{date_part}-{random_chars}'

    async def process_response(self, ai_response: str, session_id: str) -> Result:
        """
        Processa a resposta do agente e adiciona protocolo se for fim de atendimento.

        Args:
            ai_response (str): Resposta original do agente.
            session_id (str): ID da sessão do atendimento.

        Returns:
            Result: Objeto com a resposta final, possivelmente com protocolo adicionado.
        """
        try:
            detect_result = await self.protocol_detector.detect_end_of_conversation(ai_response)
            if not detect_result.success:
                return Result.fail(error_message=detect_result.error_message)

            is_end_of_conversation = detect_result.data

            if not is_end_of_conversation:
                return Result.ok(data=(ai_response, None))

            protocol_number = self._generate_protocol_number()

            final_message = (
                f'{ai_response}\n\n'
                f'PROTOCOLO DE ATENDIMENTO: {protocol_number}\n'
                f'Guarde este número para referência futura.'
            )

            return Result.ok(data=(final_message, protocol_number))

        except Exception as e:
            logger.error(f'Erro ao processar protocolo: {str(e)}')
            return Result.fail(error_message=f'Erro ao processar protocolo: {str(e)}')
