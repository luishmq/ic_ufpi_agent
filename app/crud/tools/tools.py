from crud.tools.get_person_data import get_person_data


class Tools:
    """
    Classe para agrupar e gerenciar as ferramentas (tools) disponíveis para os modelos LLM.

    Attributes:
        get_person_data_tool: Ferramenta para obter dados de pessoas a partir do CPF.
    """

    def __init__(self):
        self.get_person_data_tool = get_person_data
