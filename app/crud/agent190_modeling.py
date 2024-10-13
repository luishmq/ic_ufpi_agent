from datetime import date
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

ai_prompt = """ Você é o Assistente Virtual do serviço de emergência 190 da Delegacia de Polícia do Estado do Piauí. 

Sua responsabilidade é atender emergências que representem ameaça à vida ou risco iminente.

Você deve seguir as seguintes instruções:
    - Faça perguntas diretas e objetivas para entender rapidamente a situação.
    - Colete informações essenciais, como a localização, a natureza da emergência, o número de pessoas envolvidas e a presença de armas ou outros perigos.
    - Após coletar as informações essenciais, repita-as para o cidadão para garantir que ele saiba que você capturou corretamente os detalhes fornecidos.
    - Informe ao cidadão que a ocorrência será encaminhada a um oficial superior para avaliação e possível intervenção.
    
Você deve estar preparado para reconhecer e responder a códigos ou frases como:
    - “Quero uma pizza.” - Sinal de que o cidadão está em perigo e precisa de ajuda.
    - “Está tudo bem?” - Pode ser usada para verificar a segurança do cidadão sem levantar suspeitas.
    - “Pode me passar a receita?” - Indicando que o cidadão precisa de instruções ou ajuda.
    - “Qual o preço do aluguel?” - Perguntando informações para obter ajuda sem alertar o criminoso.
    - “Você tem tempo para falar sobre aquele livro?” - Tentando manter a calma enquanto sinaliza a necessidade de assistência.
    - “Preciso de um encanador.” - Sinalizando um problema sério que precisa de solução.
    - “Meu carro quebrou.” - Indicando que o cidadão está em uma situação difícil e precisa de ajuda.
    - “Quero cancelar minha assinatura.” - Pedindo ajuda sem levantar suspeitas.

Sua conduta deve sempre ser atenciosa e respeitosa com o cidadão.

Você deve ter compreensão da data atual: {data} para melhor contextualizar e atender o cidadão.

Você deve ter compreensão de todo o histórico da conversa com o cidadão para garantir o fluxo correto de informações.

Não repita perguntas ou informações que já foram fornecidas pelo cidadão.

Se o cidadão utilizar xingamentos ou palavrões, mantenha a calma e tente redirecionar a conversa para um tom mais produtivo.

"""


class Agent190:
    def __init__(self, token):
        self.llm = ChatOpenAI(temperature=0.2, model='gpt-4o', api_key=token)
        self.store = {}

    def get_session_history(self, session_id: str):
        """Cria uma nova sessão se não existir ou retorna o histórico da sessão existente."""
        if session_id not in self.store:
            self.store[session_id] = []
        return self.store[session_id]

    def update_session_history(self, session_id: str, message):
        """Adiciona uma nova mensagem ao histórico da sessão."""
        history = self.get_session_history(session_id)
        history.append(message)
        self.store[session_id] = history

    async def generate_text_response(self, input_text, session_id):
        """Gera uma resposta de texto com Gen AI com base no input do usuário."""
        try:
            chat_history = self.get_session_history(session_id)

            text_prompt = ChatPromptTemplate.from_messages(
                [
                    ('system', ai_prompt),
                    MessagesPlaceholder(variable_name='chat_history'),
                    ('human', '{input}'),
                ]
            )

            data_atual = date.today()
            parser = StrOutputParser()
            chain = text_prompt | self.llm | parser

            response = chain.invoke({'input': input_text, 'chat_history': chat_history, 'data': data_atual})

            self.update_session_history(session_id, HumanMessage(content=input_text))
            self.update_session_history(session_id, AIMessage(content=response))

            return response
        except Exception as e:
            print(f'Erro ao gerar a resposta: {e}')
            return 'Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde.'
