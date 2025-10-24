
class BaseCryptoException(Exception):
    def __init__(self, message: str, cause: str | None = None) -> None:
        self.cause = cause
        self.message = message


    def __str__(self) -> str:
        if self.cause:
            return f'{self.__class__.__name__}: {self.message} caused by {self.cause}'
        else:
            return f'{self.__class__.__name__}: {self.message}'


    def __cause__(self) -> Exception.__cause__:
        if self.cause:
            return self.cause
        return super().__cause__



class ConfigFileNotFound(BaseCryptoException):
    def __init__(self, message: str, cause: str | None = None) -> None:
        super().__init__(message, cause)


class DriverNotInstalled(BaseCryptoException):
    pass


class DataBaseConnectionError(BaseCryptoException):
    pass


class QueryExecutionError(BaseCryptoException):
    pass


class TransactionError(BaseCryptoException):
    pass

class APIURLNotFound(BaseCryptoException):
    pass