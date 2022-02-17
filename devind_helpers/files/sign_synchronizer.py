"""Модуль для синхронизации между файлами и их электронными подписями."""
from dataclasses import dataclass
from os import path
from typing import Type, Callable, Iterable, Optional

from django.db.models import Model
from django.db.models.fields.files import FieldFile

from .utils import get_existing_paths


@dataclass(frozen=True)
class SynchronizeModelFilesInfo:
    """Информация о файлах модели для синхронизации."""

    model: Type[Model]    # Модель
    file_field_name: str  # Название поля файла
    sign_field_name: str  # Название поля электронной подписи


@dataclass(frozen=True)
class SynchronizedFilesInfo:
    """Информация о синхронизированных файлах."""

    files_info: SynchronizeModelFilesInfo  # Информация о файлах модели для синхронизации
    file_path: tuple[str, bool]            # (Путь к файлу, был ли файл добавлен)
    sign_path: tuple[str, bool]            # (Путь к файлу электронной подписи, был ли файл добавлен)


Callback = Callable[[SynchronizedFilesInfo], None]


def synchronize_sign(files_info: Iterable[SynchronizeModelFilesInfo], callback: Optional[Callback] = None) -> None:
    """Синхронизация между файлами и их электронными подписями.

    :param files_info: информация о файлах моделей
    :param callback: функция обратного вызова для получения информации об синхронизированных файлах
    """

    for info in files_info:
        existing_file_paths = get_existing_paths(info.model._meta.get_field(info.file_field_name))
        existing_sign_paths = get_existing_paths(info.model._meta.get_field(info.sign_field_name))
        for obj in info.model.objects.all():
            file: FieldFile = getattr(obj, info.file_field_name)
            sign: FieldFile = getattr(obj, info.sign_field_name)
            if bool(file.name) ^ bool(sign.name):
                if bool(file.name):
                    sign_path = f'{path.splitext(file.name)[0]}.sgn0'
                    if sign_path in existing_sign_paths:
                        setattr(obj, info.sign_field_name, sign_path)
                        obj.save(update_fields=(info.sign_field_name,))
                        if callback:
                            callback(SynchronizedFilesInfo(
                                files_info=info,
                                file_path=(file.name, False),
                                sign_path=(sign_path, True)
                            ))
                else:
                    file_path = next(
                        (fp for fp in existing_file_paths if fp.startswith(f'{path.splitext(sign.name)[0]}.')),
                        None
                    )
                    if file_path is not None:
                        setattr(obj, info.file_field_name, file_path)
                        obj.save(update_fields=(info.file_field_name,))
                        if callback:
                            callback(SynchronizedFilesInfo(
                                files_info=info,
                                file_path=(file_path, True),
                                sign_path=(sign.name, False)
                            ))
