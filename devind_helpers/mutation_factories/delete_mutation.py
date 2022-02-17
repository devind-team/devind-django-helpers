from dataclasses import dataclass
from typing import Type, Protocol, Any, Optional, Iterable, Callable, cast

import graphene
from django.db import models
from graphql import ResolveInfo
from graphql_relay import from_global_id
from inflection import underscore

from devind_helpers.decorators import permission_classes
from devind_helpers.exceptions import NotFoundMultiple
from devind_helpers.orm_utils import get_object_or_404
from devind_helpers.permissions import BasePermission, ModelPermission
from devind_helpers.permissions import IsAuthenticated
from devind_helpers.schema.mutations import BaseMutation

__all__ = ('CheckPermissions', 'DeleteMutation',)


class CheckPermissions(Protocol):
    def __call__(self, context: Any, obj: models.Model) -> None:
        """Особая проверка разрешений.

        :param context: контекст
        :param obj: удаляемый объект
        """

        ...


class AdditionalActions(Protocol):
    def __call__(self, obj: models.Model) -> None:
        """Дополнительные действия.

        :param obj: удаляемый объект
        """

        ...


class DeleteMutation(type):
    """Метакласс для создания мутации удаления."""

    def __new__(
            mcs,
            model: Type[models.Model],
            permissions: Optional[Iterable[Type[BasePermission]]] = None,
            is_global_id: bool = False,
            is_multiple: bool = False,
            key: Optional[str] = None,
            doc: Optional[str] = None,
            description: Optional[str] = None,
            check_permissions: Optional[CheckPermissions] = None,
            additional_actions: Optional[AdditionalActions] = None) -> Type[BaseMutation]:
        """Создание мутации удаления.

        :param model: модель, в которой необходимо осуществить удаление
        :param permissions: классы разрешений
        :param is_global_id: являются ли идентификаторы глобальными
        :param is_multiple: удалять ли несколько записей
        :param key: ключ поля идентификатора
        (по умолчанию model_name_id для удаление одной записи и model_name_ids для нескольких)
        :param doc: документирование класса мутации
        :param description: описание поля идентификатора
        :param check_permissions: особая проверка разрешений
        :param additional_actions: дополнительные действия
        :return: мутация удаления
        """

        class_name = f'Delete{model.__name__}sMutation' if is_multiple else f'Delete{model.__name__}Mutation'
        computed_key = mcs._get_key(model, key, is_multiple)
        mutation_class_container = _MutationClassContainer()
        mutate_function_factory = mcs._create_multiple_mutate_and_get_payload \
            if is_multiple \
            else mcs._create_single_mutate_and_get_payload
        mutation_class_container.mutation_class = cast(Type[BaseMutation], type(class_name, (BaseMutation,), {
            '__doc__': mcs._get_doc(model, doc, is_multiple),
            'Input': mcs._create_input_class(model, is_multiple, computed_key, description),
            'mutate_and_get_payload': mutate_function_factory(
                model,
                computed_key,
                is_global_id,
                mcs._get_permissions(model, permissions),
                check_permissions,
                additional_actions,
                mutation_class_container,
            )
        }))
        return mutation_class_container.mutation_class

    @staticmethod
    def _get_key(model: Type[models.Model], key: Optional[str], is_multiple: bool) -> str:
        """Получение ключа поля идентификатора.

        :param model: модель, в которой необходимо осуществить удаление
        :param key: возможно отсутствующий ключ поля идентификатора
        :param is_multiple: удалять ли несколько записей
        :return: ключ поля идентификатора
        """

        if key:
            return key
        underscore_name = underscore(model.__name__)
        return f'{underscore_name}_ids' if is_multiple else f'{underscore_name}_id'

    @staticmethod
    def _get_doc(model: Type[models.Model], doc: Optional[str], is_multiple: bool) -> str:
        """Получение документирования класса мутации.

        :param model: модель, в которой необходимо осуществить удаление
        :param doc: возможно отсутствующее документирование класса мутации
        :param is_multiple: удалять ли несколько записей
        :return: документирование класса мутации
        """

        if doc:
            return doc
        return f'Удаление записей модели "{model.__name__}"' \
            if is_multiple \
            else f'Удаление записи модели "{model.__name__}"'

    @staticmethod
    def _get_permissions(
            model: Type[models.Model],
            permissions: Optional[Iterable[Type[BasePermission]]]) -> Iterable[Type[BasePermission]]:
        """Получение классов разрешений.

        :param model: модель, в которой необходимо осуществить удаление
        :param permissions: возможно отсутствующие классы разрешений
        :return: классы разрешений
        """

        if permissions:
            return permissions
        return IsAuthenticated, ModelPermission(f'{model._meta.app_label}.delete_{model._meta.model_name.lower()}')

    @staticmethod
    def _create_input_class(
            model: Type[models.Model],
            is_multiple: bool,
            key: str,
            description: Optional[str]) -> type:
        """Создание класса Input.

        :param model: модель, в которой необходимо осуществить удаление
        :param is_multiple: удалять ли несколько записей
        :param key: ключ поля идентификатора
        :param description: описание поля идентификатора
        :return: класс Input
        """

        if key:
            computed_key = key
        else:
            underscore_name = underscore(model.__name__)
            computed_key = f'{underscore_name}_ids' if is_multiple else f'{underscore_name}_id'
        if description:
            computed_description = description
        else:
            computed_description = f'Идентификаторы модели "{model.__doc__}"' \
                if is_multiple \
                else f'Идентификатор модели "{model.__doc__}"'
        field = graphene.List(graphene.NonNull(graphene.ID), required=True, description=computed_description) \
            if is_multiple \
            else graphene.ID(required=True, description=computed_description)
        return type('Input', (), {
            computed_key: field
        })

    @staticmethod
    def _create_single_mutate_and_get_payload(
            model: Type[models.Model],
            key: str,
            is_global_id: bool,
            permissions: Iterable[Type[BasePermission]],
            check_permissions: Optional[CheckPermissions],
            additional_actions: Optional[AdditionalActions],
            mutation_class_container: '_MutationClassContainer') -> Callable:
        """Создание метода для удаления одной записи.

        :param model: модель, в которой необходимо осуществить удаление
        :param key: ключ поля идентификатора
        :param is_global_id: является ли идентификатор глобальным
        :param permissions: классы разрешений
        :param check_permissions: особая проверка разрешений
        :param additional_actions: дополнительные действия
        :param mutation_class_container: контейнер класса мутации
        :return: метод для удаление одной записи
        """

        @permission_classes(permissions)
        def mutate_and_get_payload(root, info: ResolveInfo, **kwargs):
            obj = get_object_or_404(model, pk=from_global_id(kwargs[key])[1] if is_global_id else kwargs[key])
            if check_permissions:
                check_permissions(info.context, obj)
            else:
                info.context.check_object_permissions(info.context, obj)
            if additional_actions:
                additional_actions(obj)
            return mutation_class_container.mutation_class(
                success=cast(models.Model, super(model, obj)).delete()[0] > 0
            )

        return mutate_and_get_payload

    @staticmethod
    def _create_multiple_mutate_and_get_payload(
            model: Type[models.Model],
            key: str,
            is_global_id: bool,
            permissions: Iterable[Type[BasePermission]],
            check_permissions: Optional[CheckPermissions],
            additional_actions: Optional[AdditionalActions],
            mutation_class_container: '_MutationClassContainer') -> Callable:
        """Создание метода для удаления нескольких записей.

        :param model: модель, в которой необходимо осуществить удаление
        :param key: ключ поля идентификатора
        :param is_global_id: являются ли идентификаторы глобальными
        :param permissions: классы разрешений
        :param check_permissions: особая проверка разрешений
        :param additional_actions: дополнительные действия
        :param mutation_class_container: контейнер класса мутации
        :return: метод для удаление нескольких записей
        """

        @permission_classes(permissions)
        def mutate_and_get_payload(root, info: ResolveInfo, **kwargs):
            ids: list[str] = [from_global_id(global_id)[1] for global_id in kwargs[key]] if is_global_id else kwargs[
                key]
            qs = model.objects.filter(pk__in=ids)
            if len(ids) != qs.count():
                raise NotFoundMultiple()
            if check_permissions or hasattr(info.context, 'check_object_permissions'):
                for obj in qs.all():
                    if check_permissions:
                        check_permissions(info.context, obj)
                    elif hasattr(info.context, 'check_object_permissions'):
                        info.context.check_object_permissions(info.context, obj)
            if additional_actions:
                for obj in qs.all():
                    additional_actions(obj)
            return mutation_class_container.mutation_class(success=qs.delete()[0] > 0)

        return mutate_and_get_payload


@dataclass
class _MutationClassContainer:
    """Контейнер класса мутации

    Служит для передачи ссылки по ссылке и построения замыкания.
    """

    mutation_class: Optional[Type[BaseMutation]] = None
