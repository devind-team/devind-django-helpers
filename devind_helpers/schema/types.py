from typing import Dict, List

import graphene
from flatten_dict import flatten
from graphene import ObjectType

from devind_helpers.import_from_file import ImportFromFile


class ErrorFieldType(ObjectType):
    """Ошибка в поле формы"""

    field = graphene.String(required=True, description='Поле формы')
    messages = graphene.List(graphene.NonNull(graphene.String), required=True, description='Ошибки')

    @classmethod
    def from_validator(cls, messages: Dict[str, Dict[str, str]]) -> List['ErrorFieldType']:
        """Получение ошибок из валидатора."""

        return [cls(field=field, messages=msg.values()) for field, msg in messages.items()]

    @classmethod
    def from_messages_dict(cls, message_dict: Dict[str, List[str]]) -> List['ErrorFieldType']:
        """Получение ошибок из словаря сообщений ValidationError."""

        return [cls(field=field, messages=values) for field, values in message_dict.items()]


class RowFieldErrorType(ObjectType):
    """Ошибка в строке."""

    row = graphene.Int(required=True, description='Номер строки с ошибкой')
    errors = graphene.List(ErrorFieldType, required=True, description='Ошибки, возникающие в строке')


class TableCellType(ObjectType):
    """Ячейка документа."""

    header = graphene.String(required=True, description='Заголовок ячейки')
    value = graphene.String(default_value='-', description='Значение ячейки')
    align = graphene.String(default_value='left', description='Выравнивание')
    type = graphene.String(default_value='string', description='Тип ячейки')


class TableRowType(ObjectType):
    """Строка документа."""

    index = graphene.Int(required=True, description='Индекс строки')
    cells = graphene.List(TableCellType, required=True, description='Строка документа')


class TableType(ObjectType):
    """Документ, представлющий собой таблицу."""

    headers = graphene.List(graphene.String, required=True, description='Заголовки документа')
    rows = graphene.List(TableRowType, required=True, description='Строки документа')

    @classmethod
    def from_iff(cls, iff: ImportFromFile):
        """Получение из класса импорта данных из файла.

        :param iff: класс импорта данных из файла
        """

        rows: List[TableRowType] = []
        for index, item in enumerate(iff.initial_items):
            r = flatten(item, reducer='dot')
            rows.append(TableRowType(index=index, cells=[TableCellType(header=k, value=v) for k, v in r.items()]))
        return cls(headers=iff.all_keys, rows=rows)


class SetSettingsInputType(graphene.InputObjectType):
    """Настройка для установки."""

    key = graphene.String(required=True, description='Ключ настройки')
    value = graphene.String(required=True, description='Значение настройки')
    user_id = graphene.ID(description='Пользователь к которому применяется настройка')


class ActionRelationShip(graphene.Enum):
    """Типы измнения связей между записями в базе данных
        - ADD - Добавление
        - DELETE - Удаление
    """

    ADD = 1
    DELETE = 2


class ConsumerActionType(graphene.Enum):
    """Типы уведомления пользователей
        - CONNECT - Присоединился
        - DISCONNECT - Отсоединился
        - ADD - Пользователь добавил данные (по умолчанию)
        - CHANGE - Пользователь изменил данные
        - DELETE - Удаление объекта
        - ERROR - Ошибка ввода данных
        - TYPING - Печатет, готовиться отправить сообщение
        - TYPING_FINISH - Закончил печатать
        - EXCEPTION - Пользователь исключен из потока уведомлений
    """

    CONNECT = 1
    DISCONNECT = 2
    ADD = 3
    CHANGE = 4
    DELETE = 5
    ERROR = 6
    TYPING = 7
    TYPING_FINISH = 8
    EXCEPTION = 9