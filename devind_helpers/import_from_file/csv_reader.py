"""Модуль считывателя из формата csv."""

import csv
from typing import Iterable

from .base_reader import BaseReader


class CsvReader(BaseReader):
    """Считыватель из формата csv."""

    def __init__(self, path: str):
        """Конструктор считывателя из формата csv.

        :param path: путь к файлу
        """
        super().__init__(path)
        self.reader = csv.DictReader(open(path))

    @property
    def items(self) -> Iterable:
        """Итерируемся по файлу."""
        for row in self.reader:
            yield self.tree_transform(row)
