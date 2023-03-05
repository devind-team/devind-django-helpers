"""Модуль со вспомогательными функциями."""

import re
from argparse import ArgumentTypeError
from random import choice
from string import ascii_letters

from graphql_relay import from_global_id


def gid2int(gid: str | int) -> int | None:
    """Преобразование к обычному идентификатору."""
    try:
        return int(gid)
    except ValueError:
        try:
            return int(from_global_id(gid)[1])
        except TypeError:
            return None


def from_gid_or_none(global_id: str | None) -> tuple[str | None, int | None]:
    """Возвращает None в случае ошибки разбора."""
    if not global_id:
        return None, None
    try:
        return from_global_id(global_id)
    except TypeError:
        return None, None


def random_string(count: int) -> str:
    """Генерация случайной строки из count."""
    return ''.join(choice(ascii_letters) for _ in range(count))


def convert_str_to_bool(value: str) -> bool:
    """Преобразование строки в флаг."""
    if isinstance(value, bool):
        return value
    if value.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ArgumentTypeError('Ожидался флаг (true/false)')


def convert_str_to_int(value: str | bytes | None) -> int | None:
    """Преобразование строки в целое число."""
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode('utf-8')
    try:
        return int(value)
    except ValueError:
        return None


def is_template(text: str) -> bool:
    """Поиск шаблона в строке."""
    return bool(re.findall('{{ .*? }}', text))
