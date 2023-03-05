"""Тесты вспомогательных типов."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from devind_helpers.schema.types import ErrorFieldType  # noqa
from devind_helpers.validator import Validator  # noqa


class ErrorFieldTypeTestCase(TestCase):
    """Тесты класса `ErrorFieldType`."""

    class TestValidator(Validator):
        """Тестовый валидатор."""

        field = 'required'

        message = {
            'field': {
                'required': 'message',
            },
        }

    def test_from_validator(self) -> None:
        """Тестирование метода `from_validator`."""
        validator = ErrorFieldTypeTestCase.TestValidator({})
        validator.validate()
        self.assertEqual(
            [ErrorFieldType(field='field', messages=['message'])],
            ErrorFieldType.from_validator(validator.get_message()),
        )

    def test_from_messages_dict(self) -> None:
        """Тестирование метода `from_messages_dict`."""
        validation_error = ValidationError(
            message={
                'field': ['message1', 'message2'],
            },
        )
        self.assertEqual(
            [ErrorFieldType(field='field', messages=['message1', 'message2'])],
            ErrorFieldType.from_messages_dict(validation_error.message_dict),
        )
