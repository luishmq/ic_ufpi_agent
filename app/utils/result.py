class Result:
    """
    Classe para encapsular resultados de operações com informações de sucesso/falha.

    Attributes:
        success (bool): Indica se a operação foi bem-sucedida.
        data: Dados retornados pela operação em caso de sucesso.
        error_message (str): Mensagem de erro em caso de falha.
    """

    def __init__(self, success: bool, data=None, error_message: str = ''):
        """
        Inicializa um objeto Result.

        Args:
            success (bool): Indica se a operação foi bem-sucedida.
            data: Dados a serem retornados em caso de sucesso.
            error_message (str): Mensagem de erro em caso de falha.
        """
        self.success = success
        self.data = data
        self.error_message = error_message

    @classmethod
    def ok(cls, data=None):
        """
        Cria um objeto Result para uma operação bem-sucedida.

        Args:
            data: Dados a serem retornados.

        Returns:
            Result: Objeto Result indicando sucesso.
        """
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error_message: str):
        """
        Cria um objeto Result para uma operação que falhou.

        Args:
            error_message (str): Mensagem descrevendo o erro ocorrido.

        Returns:
            Result: Objeto Result indicando falha.
        """
        return cls(success=False, error_message=error_message)
