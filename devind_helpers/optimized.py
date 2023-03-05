"""Модуль с оптимизатором."""

from typing import Any

from django.db.models import QuerySet
from graphene_django import DjangoObjectType
from graphene_django_optimizer import query


class OptimizedDjangoObjectType(DjangoObjectType):
    """Оптимизирует запросы переопределяя метод get_queryset.

    Является рабочей копией OptimizedDjangoObjectType из graphene_django_optimizer
    """

    class Meta:
        abstract = True

    @classmethod
    def get_queryset(cls, queryset: QuerySet, info: Any) -> QuerySet:
        """Получение `QuerySet`."""
        queryset = super(OptimizedDjangoObjectType, cls).get_queryset(queryset, info)
        queryset = query(queryset, info)
        return queryset
