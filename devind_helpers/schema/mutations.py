"""Вспомогательные мутации."""
from typing import Any, Coroutine

import graphene
from django.core.exceptions import ValidationError
from graphene import relay
from graphene.utils.thenables import Promise, maybe_thenable
from graphql import ResolveInfo

from devind_helpers.schema.types import ErrorFieldType


class BaseMutation(relay.ClientIDMutation):
    """Базовая мутация."""

    class Meta:
        abstract = True

    success = graphene.Boolean(required=True, description='Успех мутации')
    errors = graphene.List(graphene.NonNull(ErrorFieldType), required=True, description='Ошибки мутации')

    def __init__(self, *args, **kwargs):
        super(BaseMutation, self).__init__(*args, **kwargs)
        if self.success is None:
            self.success = True
        if self.errors is None:
            self.errors = []

    @classmethod
    def mutate(cls, root: Any, info: ResolveInfo, input: dict) -> Coroutine | Promise:
        """Переопределение базового метода для обработки ошибок."""
        def on_resolve(payload):
            try:
                payload.client_mutation_id = input.get('client_mutation_id')
            except Exception:
                raise Exception(
                    f'Cannot set client_mutation_id in the payload object {repr(payload)}'
                )
            return payload

        try:
            return super().mutate(root, info, input)
        except ValidationError as error:
            return maybe_thenable(
                cls(success=False, errors=ErrorFieldType.from_messages_dict(error.message_dict)),
                on_resolve
            )

    def add_error(self, field: str, messages: list[str]) -> None:
        """Добавление ошибки.
        :param field: поле ошибки
        :param messages: сообщения ошибки
        """
        self.errors.append(ErrorFieldType(field=field, messages=messages))
