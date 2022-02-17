"""Модуль подставного django.http.HttpRequest."""


class Request:
    """Подставной django.http.HttpRequest для превращения запроса на мутацию в запрос http."""

    def __init__(self, uri, body, headers, meta, extra_credentials=None, http_method: str = 'POST'):
        self.uri = uri
        self.body = body
        self.META = meta
        self.headers = headers
        self.extra_credentials = extra_credentials
        self.http_method = http_method

    @property
    def method(self) -> str:
        return self.http_method

    def get_full_path(self):
        return self.uri

    @staticmethod
    def is_secure():
        return True
