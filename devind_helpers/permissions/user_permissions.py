"""Модуль с разрешениями пользователя."""

from typing import Any

from .base_permissions import BasePermission


class AllowAny(BasePermission):
    """Пропускает всех пользователей."""

    pass


class IsAuthenticated(BasePermission):
    """Пропускает только авторизованных пользователей."""

    @staticmethod
    def has_permission(context: Any) -> bool:
        """Непосредственная проверка разрешений."""
        return hasattr(context, 'user') and context.user.is_authenticated


class IsGuest(BasePermission):
    """Пропускает только неавторизованных пользователей."""

    @staticmethod
    def has_permission(context: Any) -> bool:
        """Непосредственная проверка разрешений."""
        return not (hasattr(context, 'user') and context.user.is_authenticated)
