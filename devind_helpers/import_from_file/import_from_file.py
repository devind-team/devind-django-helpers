"""Модуль импорта данных из файла."""
from os.path import splitext
from typing import TypeVar, Generic, Optional, Type, Protocol, Iterable, Union, Any

from django.db import models, transaction
from flatten_dict.flatten_dict import flatten

from .csv_reader import CsvReader
from .excel_reader import ExcelReader
from .json_reader import JsonReader
from .ratio import Ratio
from ..validator import Validator

Errors = dict[str, dict[str, str]]
ItemError = tuple[int, Errors]
Relative = tuple[Type[Validator], Type[models.Model]]


Model = TypeVar('Model', bound=models.Model)


class BeforeCreate(Protocol):
    def __call__(
            self,
            mdl: Type[Model],
            data: dict,
            separated_data: Optional[dict],
            index: int) -> Optional[tuple[dict, dict]]:
        """Хук, вызываемый перед созданием объекта.

        :param mdl: модель
        :param data: данные, которые будут использованны для создания объекта
        :param separated_data: отделенные данные
        :param index: индекс создаваемого объекта
        :return: (данные, которые будут использованны для создания объекта; отделенные данные)
        """
        ...


class Created(Protocol):
    def __call__(self, obj: Model, data: dict, separated_data: Optional[dict], index: int) -> Any:
        """Хук, вызываемый после создания объекта.

        :param obj: созданный объект
        :param data: данные, использованные для создания объекта
        :param separated_data: отделенные данные
        :param index: индекс созданного объекта
        :return: объект, добавляемый в коллекцию, возвращаемую из run
        """
        ...


class ImportFromFile(Generic[Model]):
    """Класс импорта данных из файла."""

    _readers = {
        '.xlsx': ExcelReader,
        '.csv': CsvReader,
        '.json': JsonReader
    }

    def __init__(
            self,
            model: Type[Model],
            path: str,
            validator: Optional[Type[Validator]] = None,
            relative: Optional[dict[str, Relative]] = None,
            introduction: Optional[dict] = None,
            ratio: Ratio = None,
            required_keys: Optional[list[str]] = None):
        """Конструктор импорта данных из файла.

        :param model: модель
        :param path: путь к файлу
        :param validator: валидатор
        :param relative: данные связанного элемента
        :param introduction: дополнительные данные
        :param ratio: отображение полей
        :param required_keys: обязательные ключи для формирования таблицы
        """
        self.model = model
        self.initial_items: list[dict] = [*self._readers[splitext(path)[1]](path).items]
        self.validator = validator
        self.relative = relative
        self.introduction = introduction
        self.ratio = ratio
        self.required_keys = required_keys
        self.separated_keys: Optional[list[str]] = None
        self.separated_ratio: Optional[Ratio] = None
        self.separated_validator: Optional[Type[Validator]] = None

    @property
    def items(self) -> list[dict]:
        """Элементы."""
        if self.separated_keys:
            result: list[dict] = []
            for item in self.initial_items:
                result.append({k: v for k, v in item.items() if k not in self.separated_keys})
            return result
        return self.initial_items

    @property
    def separated_items(self) -> Optional[list[dict]]:
        """Отделенные элементы."""
        if self.separated_keys:
            result: list[dict] = []
            for item in self.initial_items:
                result.append({k: v for k, v in item.items() if k in self.separated_keys})
            return result
        return None

    @property
    def all_keys(self) -> list[str]:
        """Все ключи для формирования таблицы."""
        keys_set: set[str] = set(self.required_keys) if self.required_keys else set()
        for item in self.initial_items:
            flat = flatten(item, reducer='dot')
            keys_set |= set(flat.keys())
        if self.ratio is not None:
            keys_set |= set(self.ratio.mapping.keys())
        if self.separated_ratio is not None:
            keys_set |= set(self.separated_ratio.mapping.keys())
        for key in [k.split('|')[1] for k in keys_set if '|' in k]:
            keys_set.add(key)
        keys: list[str] = []
        for key in [k for k in keys_set if '|' not in k]:
            keys.append(key)
            keys.extend(k for k in keys_set if '|' in k and k.endswith(key))
        return keys

    def separate(self,
                 keys: Iterable[str],
                 ratio: Optional[Ratio] = None,
                 validator: Optional[Type[Validator]] = None) -> None:
        """Отоделение некоторых полей для специфической записи в базу данных.

        :param keys: ключи, которые необходимо отделить
        :param ratio: отображение полей
        :param validator: валидатор для проверки отделенных данных
        """

        self.separated_keys = keys
        self.separated_ratio = ratio
        self.separated_validator = validator

    def validate(self) -> tuple[bool, Optional[list[ItemError]]]:
        """Валидация элементов.

        :return: (успех валидации, список ошибок валидации элементов)
        """

        status = True
        errors: list[ItemError] = []
        if self.validator:
            for i, item in enumerate(self.items):
                data = self._modify_item(item)
                validator = self.validator(data)
                status = validator.validate()
                related_status, related_errors = self._validate_related(
                    {k: v for k, v in item.items() if isinstance(v, dict)}
                )
                if not (status and related_status):
                    errors.append((i, {**validator.get_message(), **related_errors},))
                    status = False
        if self.separated_items and self.separated_validator:
            for i, separated_item in enumerate(self.separated_items):
                separated_data = self._modify_separated_item(separated_item)
                separated_validator = self.separated_validator(separated_data)
                if not separated_validator.validate():
                    errors.append((i, separated_validator.get_message()))
                    status = False
        return status, errors

    @transaction.atomic
    def run(
            self,
            before_create: Optional[BeforeCreate] = None,
            created: Optional[Created] = None) -> list[Union[Model, Any]]:
        """Запуск процедуры заполнения базы данных.

        :param before_create: хук, вызываемый перед созданием объекта
        :param created: хук, вызываемый после создания объекта
        :return: созданные записи
        """

        from .exceptions import HookItemException, ItemsException

        result: list[Union[Model, Any]] = []
        errors: list[ItemError] = []
        for i, item in enumerate(self.items):
            try:
                data = self._modify_item(item)
                separated_data = self._modify_separated_item(self.separated_items[i]) if self.separated_items else None
                if before_create is not None:
                    before_create_result = before_create(mdl=self.model, data=data, separated_data=separated_data, index=i)
                    if before_create_result is not None:
                        data, separated_data = before_create_result
                obj = self.model.objects.create(**data)
                self._create_related({k: v for k, v in item.items() if isinstance(v, dict)}, obj)
                if created is not None:
                    created_result = created(obj=obj, data=data, separated_data=separated_data, index=i)
                    if created_result is not None:
                        result.append(created_result)
                    else:
                        result.append(obj)
                else:
                    result.append(obj)
            except HookItemException as ex:
                errors.append(ex.error)
        if len(errors):
            raise ItemsException(errors)
        return result

    def _modify_item(self, item: dict) -> dict:
        """Модификация полей элемента с помощью инъекции и отображения для полей вида email|user_id.

        :param item: элемент для модификации
        :return: модифицированный элемент
        """

        data = {k: v for k, v in item.items() if bool(v) and not isinstance(v, dict)}
        if self.introduction is not None:
            data = {**data, **self.introduction}
        if hasattr(self.model, 'resolve_global'):
            data = self.model.resolve_global(data)
        if self.ratio is None:
            return data
        return self.ratio.map(data)

    def _modify_separated_item(self, separated_item: dict) -> dict:
        """Модификация полей отделенного элемента с помощью отображения для полей вида email|user_id.

        :param separated_item: элемент для модификации
        :return: модифицированный элемент
        """

        data = {k: v for k, v in separated_item.items() if bool(v)}
        if self.separated_ratio is None:
            return data
        return self.separated_ratio.map(data)

    def _validate_related(self, related: dict, parent: str = '') -> tuple[bool, Optional[Errors]]:
        """Валидация связанного элемента.

        :param related: связанного элемент
        :param parent: родительский путь
        :return: (успех валидации, список ошибок валидации элемента)
        """

        if related and self.relative is None:
            raise ValueError(f'Отсутствует meta_validators для проверки вложенности: {related}')
        status = True
        errors: Errors = {}
        for field, values in related.items():
            if field not in self.relative:
                raise ValueError(f'В meta_validators отсутствует валидатор для поля {field}')
            validator = self.relative[field][0]({k: v for k, v in values.items() if not isinstance(v, dict)})
            status = validator.validate()
            related_status, related_errors = self._validate_related({
                k: v for k, v in values.items() if isinstance(v, dict)
            }, f'{field}.')
            if not (status and related_status):
                errors = {**{f'{parent}{field}.{k}': v for k, v in validator.get_message().items()}, **related_errors}
                status = False
        return status, errors

    def _create_related(self, related_data: dict, parent: Model):
        """Создание связанных элементов.

        :param related_data: данные связанных элементов
        :param parent: родительский объект модели
        """

        for field, values in related_data.items():
            obj = self.relative[field][1].objects.create(
                **{'pk': parent.pk, **{k: v for k, v in values.items() if not isinstance(v, dict)}}
            )
            self._create_related({k: v for k, v in values.items() if isinstance(v, dict)}, obj)
