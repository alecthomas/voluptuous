# fmt: off
from __future__ import annotations

import gettext as _gettext
import typing
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from contextvars import ContextVar

# Public interface for translating user-visible strings.
TranslateFunc = Callable[[str], str]


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

    This updates the module default translator.
    """

    global _default_translator
    _default_translator = translation_func
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
    by gettext_scope() remain active for the current context.
    """

    global _default_translator
    translation = _gettext.translation(
        domain,
        localedir=localedir,
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


# Backward-compatible alias for existing callers.
_ = gettext


@contextmanager
def gettext_scope(translation_func: TranslateFunc):
    """Temporarily activate a translator for the current execution context."""

    token = _translator.set(translation_func)
    try:
        yield
    finally:
        _translator.reset(token)
