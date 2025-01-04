from datetime import datetime
from google.cloud import bigquery
from utils.result import Result


class BigQueryStorage:
    """
    Classe responsável por interagir com o BigQuery para armazenamento de dados.
    """

    def __init__(self):
        self.client = bigquery.Client()

    async def store_response(
        self, dataset_id: str, table_id: str, session_id: str, user_input: str, response: str
    ) -> Result:
        """
        Salva a resposta do agente no BigQuery.

        Args:
            dataset_id (str): ID do dataset no BigQuery.
            table_id (str): ID da tabela no BigQuery.
            session_id (str): ID da sessão do usuário.
            user_input (str): Texto de entrada fornecido pelo usuário.
            response (str): Resposta gerada pelo agente.

        Returns:
            Result: Objeto Result contendo sucesso ou erro.
        """
        try:
            dataset_ref = f'{self.client.project}.{dataset_id}'
            table_ref = f'{dataset_ref}.{table_id}'

            table = self.client.get_table(table_ref)

            rows_to_insert = [
                {
                    'session_id': session_id,
                    'input': user_input,
                    'timestamp': datetime.utcnow().isoformat(),
                    'response': response,
                }
            ]

            errors = self.client.insert_rows_json(table, rows_to_insert)
            if errors:
                return Result.fail(error_message=f'Erro ao inserir linhas no BigQuery: {errors}')

            return Result.ok(data='Dados inseridos com sucesso.')

        except Exception as e:
            return Result.fail(error_message=f'Erro ao armazenar resposta no BigQuery: {e}')
