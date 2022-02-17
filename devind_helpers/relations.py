"""Модуль со вспомогательными функциями для получения отношений между моделями."""

from functools import reduce
from typing import Type, Iterable, Protocol, Union

from django.db import models

__all__ = ('get_children', 'get_parents',)


def get_children(model: Type[models.Model], primary_keys: Iterable) -> list:
    """Получение идентификаторов дочерних элементов, включая себя.

    :param model: модель
    :param primary_keys: первичные ключи
    :return: идентификаторы дочерних элементов, включая себя
    """

    return reduce(
        lambda a, c: a + [c, *get_children(model, model.objects.filter(parent_id=c).values_list('pk', flat=True))],
        primary_keys,
        []
    )


class _WithParent(Protocol):
    """Модель с родителем."""

    parent: models.Model


def get_parents(obj: Union[models.Model, _WithParent]) -> list:
    """Получение идентификаторов родительских элементов, включая себя.

    :param obj: запись модели
    :return: идентификаторы родительских элементов, включая себя
    """

    if obj.parent is None:
        return [obj.pk]
    return [obj.pk, *get_parents(obj.parent)]
