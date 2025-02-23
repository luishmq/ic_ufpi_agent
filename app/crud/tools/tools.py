from crud.tools.get_person_data import get_person_data


class Tools:
    """
    Classe para agrupar e gerenciar as ferramentas (tools).
    """

    def __init__(self):
        self.get_person_data_tool = get_person_data
