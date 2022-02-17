"""Модуль с базовыми разрешениями"""
from functools import partial
from typing import Type, Optional, Callable, Any

import graphene
from django.db import models
from graphql import ResolveInfo


class BasePermission:
    """Базовый класс разрешения на действие с моделью"""

    @staticmethod
    def has_permission(context):
        """Возвращает True если есть права, False в противном случае.

        :param context: контекст
        :return: если ли права
        """

        return True

    @staticmethod
    def has_object_permission(context, obj):
        """Возвращает True если есть права, False в противном случае.

        :param context: контекст
        :param obj: объект для проверки
        :return: есть ли права
        """

        return True

    @classmethod
    def reduce_context(cls, context) -> Callable[[Any], bool]:
        """Убирает зависимость функции has_object_permission от контекста.

        :param context: контекст
        :return: функция has_object_permission без параметра context
        """

        return partial(cls.has_object_permission, context)


class ModelPermission(type):
    """Пропускает пользователей с разрешением на действие с моделью"""

    def __new__(mcs, perm: str) -> Type[BasePermission]:
        """Создание класса разрешения.

        :param perm: строка разрешения на действие с моделью. Например, core.add_user
        :return: класс разрешения
        """

        class Permission(BasePermission):
            @staticmethod
            def has_permission(context):
                return context.user.has_perm(perm)
        return Permission


class PermissionsInterface(graphene.Interface):
    """Интерфейс разрешений на действия с объектом модели"""

    can_change = graphene.Boolean(required=True, description='Есть ли права на изменение объекта модели')
    can_delete = graphene.Boolean(required=True, description='Есть ли права на удаление объекта модели')


class PermissionsType(type):
    """Метакласс для создания типа разрешений на действия с объектом модели"""

    def __new__(
            mcs,
            model: Type[models.Model],
            can_change: Optional[Type[BasePermission]] = None,
            can_delete: Optional[Type[BasePermission]] = None):
        """Создание типа разрешений на действия с объектом модели.

        :param model: модель
        :param can_change: класс разрешения на изменение
        :param can_delete: класс разрешения на удаление
        :return: тип разрешений на действия с объектом модели
        """

        class ConstructedPermissionsType(graphene.ObjectType):
            class Meta:
                name = f'{model.__name__}PermissionsType'
                interfaces = (PermissionsInterface,)

            @staticmethod
            def resolve_can_change(obj: models.Model, info: ResolveInfo):
                return can_change.has_permission(info.context) and can_change.has_object_permission(info.context, obj) \
                    if can_change \
                    else True

            @staticmethod
            def resolve_can_delete(obj: models.Model, info: ResolveInfo):
                return can_delete.has_permission(info.context) and can_delete.has_object_permission(info.context, obj) \
                    if can_delete \
                    else True

        return ConstructedPermissionsType


class PermissionsWrapperType(type):
    """Метакласс для создания обертки типа разрешений на действия с объектом модели"""

    def __new__(mcs, permissions_type: Type[graphene.ObjectType]) -> Type[graphene.ObjectType]:
        """Создание обертки типа разрешений на действия с объектом модели.

        :param permissions_type: тип разрешений на действия с объектом модели
        :return: обертка типа разрешений на действия с объектом модели
        """

        class ConstructedPermissionsWrapperType(graphene.ObjectType):
            permissions = graphene.Field(
                permissions_type,
                required=True,
                description='Разрешения на действия с объектом модели'
            )

            class Meta:
                abstract = True

            @staticmethod
            def resolve_permissions(obj: models.Model, info: ResolveInfo):
                return obj

        return ConstructedPermissionsWrapperType
