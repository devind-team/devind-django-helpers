"""Модуль с разрешением данных для создания модели."""

import binascii

from graphql_relay import from_global_id


class ResolveModel:
    """Разрешение данных для создания модели."""

    resolve_fields: list[str] = []

    @classmethod
    def resolve_global(cls, data: dict) -> dict:
        """Разрешение глобальных идентификаторов и очистка данные от лишних элементов со значениями None."""
        data = {k: v for k, v in data.items() if v is not None or '_id' in k}
        for field in cls.resolve_fields:
            if field in data:
                if data[field] is None:
                    continue
                try:
                    data[field] = int(data[field])
                except ValueError:
                    try:
                        data[field] = int(from_global_id(data[field])[1])
                    except binascii.Error:
                        data[field] = None
        return data
