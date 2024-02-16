class WrappingException(Exception):
    def __init__(self, message, exceptions=None, *args: object, **kwargs) -> None:
        super().__init__(message, *args, **kwargs)
        if not isinstance(exceptions, list):
            exceptions = [exceptions]
        self.exceptions = exceptions

    def __str__(self) -> str:
        message = super().__str__()
        for exception in self.exceptions:
            message += "\n" + exception.__str__().replace("\n", "\n\t")
        return message


class CompositeException(WrappingException):
    def __init__(self, message, exceptions, *args: object, **kwargs) -> None:
        super().__init__(message, *args, **kwargs)
        self.exceptions = exceptions


class Exception(WrappingException):
    pass


class NotImplementedError(Exception, NotImplementedError):
    pass


class RuntimeError(Exception, RuntimeError):
    pass


class DependencyError(Exception, NameError):
    pass
