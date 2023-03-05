"""Модуль подставного `django.http.HttpRequest`."""

from typing import Any


class Request:
    """Подставной `django.http.HttpRequest` для превращения запроса на мутацию в запрос http."""

    def __init__(
        self,
        uri: str,
        body: dict,
        headers: dict,
        meta: dict,
        extra_credentials: Any = None,
        http_method: str = 'POST',
    ) -> None:
        """Инициализатор подставного `django.http.HttpRequest`."""
        self.uri = uri
        self.body = body
        self.META = meta
        self.headers = headers
        self.extra_credentials = extra_credentials
        self.http_method = http_method

    @property
    def method(self) -> str:
        """Получение http метода."""
        return self.http_method

    def get_full_path(self) -> str:
        """Получение uri."""
        return self.uri

    @staticmethod
    def is_secure() -> bool:
        """Запрос является безопасным."""
        return True
