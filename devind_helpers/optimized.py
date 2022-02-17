from graphene_django import DjangoObjectType
from graphene_django_optimizer import query


class OptimizedDjangoObjectType(DjangoObjectType):
    """
    Оптимизирует запросы переопределяя метод get_queryset
    Является рабочей копией OptimizedDjangoObjectType из graphene_django_optimizer
    """

    class Meta:
        abstract = True

    @classmethod
    def get_queryset(cls, queryset, info):
        queryset = super(OptimizedDjangoObjectType, cls).get_queryset(queryset, info)
        queryset = query(queryset, info)
        return queryset
