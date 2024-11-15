class Result:
    def __init__(self, success: bool, data=None, error_message: str = ''):
        self.success = success
        self.data = data
        self.error_message = error_message

    @classmethod
    def ok(cls, data=None):
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error_message: str):
        return cls(success=False, error_message=error_message)
