"""Модуль с исключениями."""

from .import_from_file import ItemError


class HookError(Exception):
    """Исключение, выбрасываемое из хука."""

    pass


class HookItemError(Exception):
    """Исключение, выбрасываемое из хука, если ошибки можно отобразить в таблице."""

    def __init__(self, error: ItemError) -> None:
        """Инициализатор исключения."""
        self.error = error


class ItemsError(Exception):
    """Исключение, выбрасываемое из метода run и собирающее ошибки из HookItemException."""

    def __init__(self, errors: list[ItemError]) -> None:
        """Инициализатор исключения."""
        self.errors = errors
