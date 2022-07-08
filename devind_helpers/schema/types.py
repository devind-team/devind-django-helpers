import enum
from strawberry_django_plus import gql

from flatten_dict import flatten


from devind_helpers.import_from_file import ImportFromFile


@gql.type
class RowFieldErrorType:
    """Ошибка в строке."""

    row: int = gql.field(description='Номер строки с ошибкой')
    errors: list[gql.OperationMessage] = gql.field(description='Ошибки, возникающие в строке')


@gql.type
class TableCellType:
    """Ячейка документа."""

    header: str = gql.field(description='Заголовок ячейки')
    value: str = gql.field(default='-', description='Значение ячейки')
    align: str = gql.field(default='left', description='Выравнивание')
    type: str = gql.field(default='string', description='Тип ячейки')


@gql.type
class TableRowType:
    """Строка документа."""

    index: int = gql.field(description='Индекс строки')
    cells: list[TableCellType] = gql.field(description='Строка документа')


@gql.type
class TableType:
    """Документ, представлющий собой таблицу."""

    headers: list[str] = gql.field(description='Заголовки документа')
    rows: list[TableRowType] = gql.field(description='Строки документа')

    @classmethod
    def from_iff(cls, iff: ImportFromFile):
        """Получение из класса импорта данных из файла.

        :param iff: класс импорта данных из файла
        """

        rows: list[TableRowType] = []
        for index, item in enumerate(iff.initial_items):
            r = flatten(item, reducer='dot')
            rows.append(TableRowType(index=index, cells=[TableCellType(header=k, value=v) for k, v in r.items()]))
        return cls(headers=iff.all_keys, rows=rows)


@gql.input
class SetSettingsInputType:
    """Настройка для установки."""

    key: str = gql.field(description='Ключ настройки')
    value: str = gql.field(description='Значение настройки')
    user_id: gql.ID = gql.field(description='Пользователь к которому применяется настройка')


@gql.enum
class ActionRelationShip(enum.Enum):
    """Типы измнения связей между записями в базе данных
        - ADD - Добавление
        - DELETE - Удаление
    """

    ADD = 1
    DELETE = 2


@gql.enum
class ConsumerActionType(enum.Enum):
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
