"""Модуль с исключениями."""

from typing import Any

from graphql import GraphQLError as BaseGraphQLError


class GraphQLError(BaseGraphQLError):
    """Ошибка GraphQL."""

    status: int = 404
    message: str = 'Произошла ошибка'

    def __init__(self, message: str | None = None, status: int | None = None, *args: Any, **kwargs: Any) -> None:
        """Конструктор ошибки GraphQL.

        :param message: сообщение
        :param status: код состояния
        """
        if message is None:
            message = self.message
        if status is None:
            status = self.status
        super().__init__(message, status, *args, **kwargs)


class PermissionDenied(GraphQLError):
    """Ошибка отсутствия прав."""

    status: int = '403'
    message: str = 'У Вас недостаточно прав для совершения данного действия'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Конструктор ошибки отсутствия прав."""
        super(PermissionDenied, self).__init__(*args, **kwargs)


class NotFound(GraphQLError):
    """Ошибка, возникающая при отсутствии записи в БД."""

    status: int = 404
    message: str = 'Запрашиваемая запись не найдена'


class NotFoundMultiple(GraphQLError):
    """Ошибка, возникающая при отсутствии нескольких записей в БД."""

    status: int = 404
    message: str = 'Запрашиваемые записи не найдены'
