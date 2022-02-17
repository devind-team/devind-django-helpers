"""Модуль для удаления лишних файлов, на которые нет ссылающихся записей в БД."""

from dataclasses import dataclass
from functools import reduce
from os import path, remove
from typing import cast, Type, Callable, Iterable, Optional

from django.apps import apps, AppConfig
from django.conf import settings
from django.db.models import Model, Field, FileField

from .utils import get_existing_paths


@dataclass(frozen=True)
class DeleteModelFilesInfo:
    """Информация о файлах модели для удаления"""

    app: AppConfig      # Приложение
    model: Type[Model]  # Модель
    field: Field        # Поле модели
    delete_count: int   # Количество удаляемых файлов


@dataclass(frozen=True)
class DeletedFileInfo:
    """Информация об удаленном файле"""

    files_info: DeleteModelFilesInfo  # Информация о файлах модели для удаления
    path: str                         # Путь к файлу
    index: int                        # Индекс файла


Callback = Callable[[DeletedFileInfo], None]


def clear_model_field_files(model: Type[Model], field_name: str, callback: Optional[Callback] = None) -> None:
    """Удаление лишних файлов поля модели.

    :param model: модель
    :param field_name: название поля модели
    :param callback: функция обратного вызова для получения информации об удаляемых файлах
    """

    field = model._meta.get_field(field_name)
    if not isinstance(field, FileField):
        raise ValueError(f'Поле {field} не является экземпляром {FileField.__name__}')
    file_fields = [f for f in model._meta.get_fields() if isinstance(f, FileField)]
    _clear_model_field_files(model._meta.app_config, model, file_fields, field, callback)


def clear_models_files(models: Iterable[Type[Model]], callback: Optional[Callback] = None) -> None:
    """Удаление лишних файлов моделей.
    
    :param models: модели
    :param callback: функция обратного вызова для получения информации об удаляемых файлах
    """

    for model in models:
        _clear_model_files(model._meta.app_config, model, callback)


def clear_apps_files(app_labels: Iterable[str], callback: Optional[Callback] = None) -> None:
    """Удаление лишних файлов приложений.

    :param app_labels: названия приложений, в которых необходимо удалить файлы
    :param callback: функция обратного вызова для получения информации об удаляемых файлах
    """

    for app_name in app_labels:
        app: AppConfig = apps.get_app_config(app_name)
        for model in cast(Iterable[Type[Model]], app.get_models()):
            _clear_model_files(app, model, callback)


def _clear_model_files(app: AppConfig, model: Type[Model], callback: Optional[Callback] = None) -> None:
    """Удаление лишних файлов модели.

    :param app: приложение
    :param model: модель
    :param callback: функция обратного вызова для получения информации об удаляемых файлах
    """

    file_fields = [f for f in model._meta.get_fields() if isinstance(f, FileField)]
    for field in file_fields:
        _clear_model_field_files(app, model, file_fields, field, callback)


def _clear_model_field_files(
        app: AppConfig,
        model: Type[Model],
        file_fields: list[FileField],
        file_field: FileField,
        callback: Optional[Callback] = None) -> None:
    """Удаление лишних файлов поля модели.

    :param app: приложение
    :param model: модель
    :param file_fields: файловые поля модели
    :param file_field: файловое поле модели для удаления
    :param callback: функция обратного вызова для получения информации об удаляемых файлах
    """

    existing_paths = get_existing_paths(file_field)
    db_paths = reduce(
        lambda acc, field: acc | set(model.objects.values_list(field.name, flat=True)),
        file_fields,
        set()
    )
    paths_to_delete = existing_paths - db_paths
    model_files_info = DeleteModelFilesInfo(app, model, file_field, len(paths_to_delete))
    for i, path_to_delete in enumerate(paths_to_delete):
        remove(path.join(settings.BASE_DIR, path_to_delete))
        if callback:
            callback(DeletedFileInfo(model_files_info, path_to_delete, i))
