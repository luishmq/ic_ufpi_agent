import os
import requests

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

LUPA_API_KEY = os.getenv('LUPA_API_KEY')
BASE_URL = os.getenv('BASE_URL')


@tool
def get_person_data(cpf: str):
    """Retorna os dados do cidadão a partir do CPF fornecido."""
    try:
        response = requests.get(
            f'{BASE_URL}/ibioseg/pessoa',
            params={'cpf': cpf},
            headers={'Authorization': f'Api-Key {LUPA_API_KEY}'},
            verify=False,
        )
        response.raise_for_status()
        person_data = response.json()
    except requests.exceptions.RequestException as e:
        return 'Erro ao buscar dados da pessoa: ' + str(e)

    return person_data
