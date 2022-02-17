"""Модуль базового считывателя."""
from abc import ABC, abstractmethod
from typing import Union, Iterable

from flatten_dict.flatten_dict import unflatten


class BaseReader(ABC):
    """Базовый считыватель."""

    def __init__(self, path: str):
        """Конструктор базового считывателя.

        :param path: путь к файлу
        """
        self.path = path

    @property
    @abstractmethod
    def items(self) -> Iterable:
        """Считанные элементы."""
        ...

    @staticmethod
    def tree_transform(row: dict[str, Union[str, dict]]) -> dict:
        """Преобразование элементов."""
        return unflatten(row, splitter='dot')
