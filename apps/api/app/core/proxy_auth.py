"""Trust a proxy supplied identity only at the configured network boundary."""

from contextvars import ContextVar
from ipaddress import ip_address, ip_network

from app.core.config import settings
from fastapi import Request

_username: ContextVar[str | None] = ContextVar("dcmsim_username", default=None)


def current_username() -> str | None:
    return _username.get()


def set_username(value: str | None):
    return _username.set(value)


def reset_username(token) -> None:
    _username.reset(token)


def proxy_username(request: Request) -> str | None:
    if not (settings.proxy_auth_enabled or settings.proxy_auth_required):
        return None
    try:
        remote = ip_address(request.client.host if request.client else "")
        networks = [ip_network(item.strip(), strict=False) for item in settings.trusted_proxies.split(",") if item.strip()]
    except ValueError:
        return None
    if not any(remote in network for network in networks):
        return None
    value = request.headers.get(settings.proxy_user_header, "").strip()
    if not value or len(value) > 128 or any(ord(char) < 32 or ord(char) == 127 for char in value):
        return None
    return value
