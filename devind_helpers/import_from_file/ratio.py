"""Модуль отображения полей."""

from typing import Type

from django.db import models


class Ratio:
    """Отображения полей типа email|user_id.

    Ищем запись с get(email=value) -> user_id."""

    def __init__(self, mapping: dict[str, Type[models.Model]]):
        """Конструктор отображения полей.

        :param mapping: словарь отображения
        """

        self.mapping = mapping

    def map(self, data: dict) -> dict:
        """Отображение полей.

        :param data: данные для отображения
        :return: результат отображения
        """

        result: dict = {}
        for k, v in data.items():
            if k in self.mapping:
                fields = k.split('|')
                if len(fields) == 2:
                    try:
                        # Если преобразование удалось
                        result[fields[1]] = self.mapping[k].objects.values('id').get(**{fields[0]: v})['id']
                    except self.mapping[k].DoesNotExist:
                        # Если преобразование не удалось
                        result[k] = v
            else:
                result[k] = v
        return result
