"""Тесты вспомогательных мутаций."""

from collections import OrderedDict
from typing import Any

import graphene
from django.core.exceptions import ValidationError
from django.test import TestCase
from graphql import ResolveInfo

from devind_helpers.schema import BaseMutation  # noqa


class TestMutation(BaseMutation):
    """Мутация для тестирования."""

    class Input:
        i = graphene.String(required=True)

    digit = graphene.Int()

    @staticmethod
    def mutate_and_get_payload(root: Any, info: ResolveInfo, i: str) -> 'TestMutation':  # noqa
        if i.isdigit():
            return TestMutation(digit=int(i))
        raise ValidationError(
            message={
                'i': ['Ожидалась строка с числом'],
            },
        )


class TestMutations(graphene.ObjectType):
    """Мутации для тестирования."""

    test_mutation = TestMutation.Field(required=True)


class BaseMutationTestCase(TestCase):
    """Тесты класса `BaseMutation`."""

    def setUp(self) -> None:
        """Создание данных для тестирования."""
        self.schema = graphene.Schema(mutation=TestMutations)

    def test_mutate(self) -> None:
        """Тестирование метода `mutate` без ошибок."""
        result = self.schema.execute(self._create_test_mutation_query('5'))
        expected_data = OrderedDict()
        expected_data['testMutation'] = {
            'digit': 5,
            'success': True,
            'errors': [],
        }
        self.assertEqual(expected_data, result.data)

    def test_mutate_validation_error(self) -> None:
        """Тестирование метода `mutate` с ошибкой `ValidationError`."""
        result = self.schema.execute(self._create_test_mutation_query('x'))
        expected_data = OrderedDict()
        expected_data['testMutation'] = {
            'digit': None,
            'success': False,
            'errors': [{
                'field': 'i',
                'messages': ['Ожидалась строка с числом'],
            }],
        }
        self.assertEqual(expected_data, result.data)

    @staticmethod
    def _create_test_mutation_query(i: str) -> str:
        """Создание запроса для тестовой мутации."""
        return f"""
            mutation {{
                testMutation(input: {{ i: "{i}" }}) {{
                    digit
                    success
                    errors {{
                        field
                        messages
                    }}
                }}
            }}
        """
