"""Модуль со вспомогательными функциями."""

import pathlib
from os import path, walk
from typing import cast

from django.conf import settings
from django.db.models import FileField

__all__ = ('get_upload_to', 'get_existing_paths',)


def get_upload_to(file_field: FileField) -> str:
    """Получение значения upload_to поля файла.

    :param file_field: поле файла
    :return: значение upload_to поля файла
    """

    return file_field.upload_to(_Stub(), '').rstrip('/') if callable(file_field.upload_to) else file_field.upload_to


def get_existing_paths(file_field: FileField) -> set[str]:
    """Получение существующих путей относительно storage.

    :param file_field: поле файла
    :return: существующие пути относительно storage
    """

    existing_paths: set[str] = set()
    for dirpath, _, filenames in walk(path.join(settings.BASE_DIR, get_upload_to(file_field))):
        existing_paths.update(
            pathlib.PurePath(
                path.relpath(path.join(cast(str, dirpath), cast(str, fn)), settings.BASE_DIR)
            ).as_posix() for fn in filenames
        )
    return existing_paths


class _Stub:
    """Заглушка для получения пути, если upload_to является методом."""

    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __str__(self):
        return ''
