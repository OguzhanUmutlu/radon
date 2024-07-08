class UniversalStrMixin:
    def __str__(self):
        attributes = [
            f"{key}={list(map(str,value)) if isinstance(value, list) else value}"
            for key, value in filter(lambda x: x[0] != "code", self.__dict__.items())
        ]
        return f"{self.__class__.__name__}({', '.join(attributes)})"
