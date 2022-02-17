"""Модуль с исключениями."""

from graphql import GraphQLError as BaseGraphQLError


class GraphQLError(BaseGraphQLError):
    """Ошибка GraphQL."""

    status: int = 404
    message: str = 'Произошла ошибка'

    def __init__(self, message=None, status=None, *args, **kwargs):
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
    """Ошибка отсуствия прав."""

    status: int = '403'
    message: str = 'У Вас недостаточно прав для совершения данного действия'
    
    def __init__(self, *args, **kwargs):
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
