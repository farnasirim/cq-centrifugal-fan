class WrappingException(Exception):
    def __init__(self, message, exception=None, *args: object, **kwargs) -> None:
        super().__init__(message, *args, **kwargs)
        self.exception = exception

    def __str__(self) -> str:
        message = super().__str__()
        if self.exception:
            message += ":\n" + self.exception.__str__().replace("\n", "\n\t")
        return message


class Exception(WrappingException):
    pass


class NotImplementedError(Exception, NotImplementedError):
    pass


class RuntimeError(Exception, RuntimeError):
    pass


class DependencyError(RuntimeError):
    pass
