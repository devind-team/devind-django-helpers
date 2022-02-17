"""Модуль с исключениями."""

from .import_from_file import ItemError


class HookException(Exception):
    """Исключение, выбрасываемое из хука."""

    pass


class HookItemException(Exception):
    """Исключение, выбрасываемое из хука, если ошибки можно отобразить в таблице."""

    def __init__(self, error: ItemError):
        self.error = error


class ItemsException(Exception):
    """Исключение, выбрасываемое из метода run и собирающее ошибки из HookItemException."""

    def __init__(self, errors: list[ItemError]):
        self.errors = errors
