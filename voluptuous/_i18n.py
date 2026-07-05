# fmt: off
from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

import gettext as _gettext
import typing

# Public interface for translating user-visible strings.
TranslateFunc = Callable[[str], str]


def _resolve_localedir(localedir: typing.Optional[str] = None) -> typing.Optional[str]:
    if localedir is not None:
        return localedir

    package_locale_dir = Path(__file__).resolve().parent / "locale"
    if package_locale_dir.is_dir():
        return str(package_locale_dir)
    return None


def _normalize_languages(
    languages: typing.Optional[typing.Union[str, Iterable[str]]],
) -> typing.Optional[list[str]]:
    if languages is None:
        return None
    if isinstance(languages, str):
        return [languages]
    return list(languages)

_default_translator: TranslateFunc = _gettext.gettext
_translator: ContextVar[typing.Optional[TranslateFunc]] = ContextVar(
    "voluptuous_gettext", default=None
)


def set_gettext(translation_func: TranslateFunc) -> TranslateFunc:
    """Inject a custom gettext-compatible callable used by voluptuous messages.

    This updates the current context translator and the module default.
    """

    global _default_translator
    _default_translator = translation_func
    _translator.set(translation_func)
    return translation_func


def configure_i18n(
    *,
    domain: str = "voluptuous",
    localedir: typing.Optional[str] = None,
    languages: typing.Optional[typing.Union[str, Iterable[str]]] = None,
    fallback: bool = True,
) -> TranslateFunc:
    """Configure module-level translation backend for voluptuous messages.

    This updates the module default translator. Explicit context overrides set
    by set_gettext() or gettext_scope() remain active for the current context.
    """

    global _default_translator
    translation = _gettext.translation(
        domain,
        localedir=_resolve_localedir(localedir),
        languages=_normalize_languages(languages),
        fallback=fallback,
    )
    translation_func = translation.gettext
    _default_translator = translation_func
    return translation_func


def gettext(message: str) -> str:
    """Translate a user-facing message through active backend."""

    translator = _translator.get()
    if translator is None:
        translator = _default_translator
    return translator(message)

@contextmanager
def gettext_scope(translation_func: TranslateFunc):
    """Temporarily activate a translator for the current execution context."""

    token = _translator.set(translation_func)
    try:
        yield
    finally:
        _translator.reset(token)


# Initialize the default translator using the default locale chain.
configure_i18n()
