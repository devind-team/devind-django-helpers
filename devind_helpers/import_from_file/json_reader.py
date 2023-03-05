"""Модуль считывателя из формата json."""

import json
from typing import Iterable

from .base_reader import BaseReader


class JsonReader(BaseReader):
    """Считыватель из формата json."""

    def __init__(self, path: str) -> None:
        """Конструктор считывателя из формата json.

        :param path: путь к файлу
        """
        super().__init__(path)

    @property
    def items(self) -> Iterable:
        """Перебираем строки."""
        with open(self.path, encoding='utf-8') as f:
            yield from json.load(f)
