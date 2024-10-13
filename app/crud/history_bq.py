import datetime

from google.cloud import bigquery


async def store_response(dataset_id, table_id, session_id, input, response):
    """Salva a resposta do agente no BigQuery."""

    client = bigquery.Client()
    dataset_ref = f'{client.project}.{dataset_id}'
    table_ref = f'{dataset_ref}.{table_id}'
    table = client.get_table(table_ref)

    rows_to_insert = [
        {
            'session_id': session_id,
            'input': input,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'response': response,
        }
    ]

    errors = client.insert_rows_json(table, rows_to_insert)
    if errors:
        raise Exception(f'Failed to insert rows into BigQuery: {errors}')
