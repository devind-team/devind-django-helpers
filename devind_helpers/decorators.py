"""Модуль с декораторами."""

from functools import wraps
from typing import Type, Callable, Iterable, Union, Optional, Any

from django.core.files.uploadedfile import TemporaryUploadedFile
from graphql import ResolveInfo

from devind_helpers.exceptions import PermissionDenied
from devind_helpers.permissions import BasePermission
from devind_helpers.redis_client import redis
from devind_helpers.resolve_model import ResolveModel
from devind_helpers.utils import convert_str_to_int
from devind_helpers.validator import Validator

__all__ = (
    'permission_classes',
    'resolve_classes',
    'ValidationError',
    'validation_classes',
    'register_users',
)


def permission_classes(permissions: Iterable[Type[BasePermission]]) -> Callable[[Callable], Callable]:
    """Применение классов разрешений к мутации.

    :param permissions: классы разрешений
    """

    def wrapped_decorator(func: Callable) -> Callable:
        @wraps(func)
        def inner(*args, **kwargs):
            def check_object_perms(context, obj):
                if not _check_object_permissions(permissions, context, obj):
                    raise PermissionDenied('Ошибка доступа')
            info: ResolveInfo = _get_resolve_info(*args)
            if _check_permissions(permissions, info.context):
                info.context.check_object_permissions = check_object_perms
                return func(*args, **kwargs)
            raise PermissionDenied('Ошибка доступа')
        return inner
    return wrapped_decorator


def resolve_classes(resolve_models: Optional[Iterable[Type[ResolveModel]]]) -> Callable[[Callable], Callable]:
    """Применение классов разрешения данных к мутации.

    :param resolve_models: классы, разрешающие данные
    """

    def wrapped_decorator(func: Callable) -> Callable:
        @wraps(func)
        def inner(*args, **kwargs):
            for resolve_model in resolve_models:
                kwargs = resolve_model.resolve_global(kwargs)
            return func(*args, **kwargs)
        return inner
    return wrapped_decorator


class ValidationError(Exception):
    """Ошибка валидации"""

    def __init__(self, errors: list):
        self.errors = errors


def validation_classes(
        validators: Iterable[Union[Type[Validator], tuple[Type[Validator], Callable[[str], bool]]]],
        additional_data: Optional[dict] = None,
        deferred: bool = False) -> Callable[[Callable], Callable]:
    """Применение классов валидаторов к мутации.

    :param validators: классы валидаторов опционально с функциями,
    определяющими включать ли соответствующий ключ в валидацию
    :param additional_data: дополнительные данные, передаваемые в мутацию
    :param deferred: является ли применение валидации отложенным
    """

    from devind_helpers.schema.types import ErrorFieldType

    def wrapped_decorator(func: Callable) -> Callable:
        @wraps(func)
        def inner(cls, root, info: ResolveInfo, *args, **kwargs):
            def get_errors(validation_data: Optional[dict] = None) -> list[ErrorFieldType]:
                data: dict = validation_data or _validation_filter(kwargs)
                errors: list[ErrorFieldType] = []
                for validator in validators:
                    if issubclass(validator, Validator):
                        v = validator(data)
                    else:
                        v = validator[0]({k: v for k, v in data.items() if validator[1](k)})
                    if not v.validate():
                        errors.extend(ErrorFieldType.from_validator(v.get_message()))
                return errors
            ad = additional_data or {}
            try:
                if deferred:
                    def validate(validation_data: Optional[dict] = None) -> None:
                        ve = get_errors(validation_data)
                        if len(ve):
                            raise ValidationError(ve)
                    info.context.validate = validate
                    return func(cls, root, info, *args, **kwargs)
                else:
                    e = get_errors()
                    return cls(success=False, errors=e, *ad) if len(e) else func(cls, root, info, *args, **kwargs)
            except ValidationError as ex:
                return cls(success=False, errors=ex.errors, *ad)
        return inner
    return wrapped_decorator


def register_users(key: str, delete: bool = False) -> Callable[[Callable], Callable]:
    """Регистрация пользователя в кеше.

    :param key: ключ регистрации
    :param delete: удаляем пользователя или нет
    """

    def wrapped_decorator(func: Callable) -> Callable:
        @wraps(func)
        def inner(*args, **kwargs):
            info: ResolveInfo = _get_resolve_info(*args)
            user_id: Optional[int] = info.context.user.id if hasattr(info.context, 'user') else None
            if redis and user_id:
                value: int = convert_str_to_int(redis.hget(key, user_id)) or 0
                # Если значение <= 0 и очищаем, то мы не можем отнять -1 -> удаляем
                if value <= 0 and delete:
                    redis.hdel(key, user_id)
                else:
                    redis.hincrby(key, user_id, -1 if delete else 1)
            return func(*args, **kwargs)
        return inner
    return wrapped_decorator


def _check_permissions(permissions: Iterable[Type[BasePermission]], context: Any) -> bool:
    """Проверка разрешений.

    :param permissions: классы разрешений
    :param context: контекст
    :return: результат проверки
    """

    for permission in permissions:
        if not permission.has_permission(context):
            return False
    return True


def _check_object_permissions(permissions: Iterable[Type[BasePermission]], context: Any, obj: Any) -> bool:
    """Проверка разрешений для заданного объекта.

    :param permissions: классы разрешений
    :param context: контекст
    :param obj: заданный объект
    :return: результат проверки
    """

    for permission in permissions:
        if not permission.has_object_permission(context, obj):
            return False
    return True


def _validation_filter(kwargs: dict) -> dict:
    """Фильтр для исключения TemporaryUploadedFile из валидации, т.к. такие файлы приводят к ошибке валидатора.

    :param kwargs: словарь для валидации
    :return: словарь для валидации с исключенными значениями TemporaryUploadedFile
    """

    return {k: v for k, v in kwargs.items() if not isinstance(v, TemporaryUploadedFile)}


def _get_resolve_info(*args) -> ResolveInfo:
    """Получение ResolveInfo из аргументов, которые могут быть,
    как аргументами метода экземпляра или класса, так и аргументами статического метода.

    :param args: аргументы метода неизвестного типа
    :return: объект ResolveInfo
    """

    return args[2] if len(args) >= 3 and hasattr(args[2], 'context') else args[1]
