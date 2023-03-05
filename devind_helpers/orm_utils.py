"""Модуль со вспомогательными функциями для работы с Django ORM."""

from typing import Any, Protocol

from django.db.models import Manager, Model, QuerySet

from .exceptions import NotFound

__all__ = ('get_object_or_404', 'get_object_or_none')


def get_object_or_404(klass: type[Model] | Manager | QuerySet, *args: Any, **kwargs: Any) -> Model:
    """Получение объекта модели или ошибки 404, если объект не найден.

    :param klass: Model, Manager или QuerySet
    :param args: неименованные аргументы для получения объекта модели
    :param kwargs: именованные аргументы для получения объекта модели
    :return: объект модели
    """
    queryset = _get_queryset(klass)
    if not hasattr(queryset, 'get'):
        klass_name = klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        raise ValueError(
            f'Первый аргумент get_object_or_error() долен быть Model, Manager или Queryset, не {klass_name}',
        )
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        raise NotFound()


def get_object_or_none(klass: type[Model] | Manager | QuerySet, *args: Any, **kwargs: Any) -> Model | None:
    """Получение объекта модели или значения None, если объект не найден.

    :param klass: Model, Manager или QuerySet
    :param args: неименованные аргументы для получения объекта модели
    :param kwargs: именованные аргументы для получения объекта модели
    :return: объект модели или None
    """
    queryset = _get_queryset(klass)
    if not hasattr(queryset, 'get'):
        klass_name = klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        raise ValueError(
            f'Первый аргумент get_object_or_error() долен быть Model, Manager или Queryset, не {klass_name}',
        )
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None


class _WithDefaultManager(Protocol):
    """Класс c полем _default_manager."""

    _default_manager: Manager


def _get_queryset(klass: _WithDefaultManager | Manager) -> QuerySet | Manager:
    """Получение QuerySet или Manager.

    :param klass: объект c полем _default_manager или Manager
    :return: QuerySet или Manager
    """
    if hasattr(klass, '_default_manager'):
        return klass._default_manager.all()  # noqa
    return klass
