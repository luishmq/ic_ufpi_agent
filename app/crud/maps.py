import httpx
from utils.globals import GOOGLE_MAPS_API_KEY
from utils.result import Result


async def geocode_reverse(latitude, longitude):
    """
    Realiza geocodificação reversa para obter o endereço a partir das coordenadas.

    Args:
        latitude (str): Latitude da localização.
        longitude (str): Longitude da localização.

    Returns:
        Result: Objeto contendo sucesso/falha e o endereço ou mensagem de erro.
    """
    try:
        url = (
            f'https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={GOOGLE_MAPS_API_KEY}'
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        if data['status'] == 'OK' and data['results']:
            address = data['results'][0]['formatted_address']
            return Result.ok(data=address)
        else:
            return Result.fail(error_message='Endereço não encontrado para as coordenadas fornecidas.')
    except Exception as e:
        return Result.fail(error_message=f'Erro inesperado ao buscar o endereço: {e}')
