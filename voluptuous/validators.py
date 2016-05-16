import os
import re
import datetime
import sys
from functools import wraps


try:
    from schema_builder import Schema, raises, message
    from error import (MultipleInvalid, CoerceInvalid, TrueInvalid, FalseInvalid, BooleanInvalid, Invalid, AnyInvalid,
                       AllInvalid, MatchInvalid, UrlInvalid, EmailInvalid, FileInvalid, DirInvalid, RangeInvalid,
                       PathInvalid, ExactSequenceInvalid, LengthInvalid, DatetimeInvalid, InInvalid, TypeInvalid,
                       NotInInvalid)
except ImportError:
    from .schema_builder import Schema, raises, message
    from .error import (MultipleInvalid, CoerceInvalid, TrueInvalid, FalseInvalid, BooleanInvalid, Invalid, AnyInvalid,
                        AllInvalid, MatchInvalid, UrlInvalid, EmailInvalid, FileInvalid, DirInvalid, RangeInvalid,
                        PathInvalid, ExactSequenceInvalid, LengthInvalid, DatetimeInvalid, InInvalid, TypeInvalid,
                        NotInInvalid)


if sys.version_info >= (3,):
    import urllib.parse as urlparse
    basestring = str
else:
    import urlparse

# Taken from https://github.com/kvesteri/validators/blob/master/validators/email.py
USER_REGEX = re.compile(
    # dot-atom
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+"
    r"(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*$"
    # quoted-string
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|'
    r"""\\[\001-\011\013\014\016-\177])*"$)""",
    re.IGNORECASE
)
DOMAIN_REGEX = re.compile(
    # domain
    r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
    r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?$)'
    # literal form, ipv4 address (SMTP 4.1.3)
    r'|^\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)'
    r'(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$',
    re.IGNORECASE)

__author__ = 'tusharmakkar08'


def truth(f):
    """Convenience decorator to convert truth functions into validators.

        >>> @truth
        ... def isdir(v):
        ...   return os.path.isdir(v)
        >>> validate = Schema(isdir)
        >>> validate('/')
        '/'
        >>> with raises(MultipleInvalid, 'not a valid value'):
        ...   validate('/notavaliddir')
    """

    @wraps(f)
    def check(v):
        t = f(v)
        if not t:
            raise ValueError
        return v

    return check


class Coerce(object):
    """Coerce a value to a type.

    If the type constructor throws a ValueError or TypeError, the value
    will be marked as Invalid.

    Default behavior:

        >>> validate = Schema(Coerce(int))
        >>> with raises(MultipleInvalid, 'expected int'):
        ...   validate(None)
        >>> with raises(MultipleInvalid, 'expected int'):
        ...   validate('foo')

    With custom message:

        >>> validate = Schema(Coerce(int, "moo"))
        >>> with raises(MultipleInvalid, 'moo'):
        ...   validate('foo')
    """

    def __init__(self, type, msg=None):
        self.type = type
        self.msg = msg
        self.type_name = type.__name__

    def __call__(self, v):
        try:
            return self.type(v)
        except (ValueError, TypeError):
            msg = self.msg or ('expected %s' % self.type_name)
            raise CoerceInvalid(msg)

    def __repr__(self):
        return 'Coerce(%s, msg=%r)' % (self.type_name, self.msg)


@message('value was not true', cls=TrueInvalid)
@truth
def IsTrue(v):
    """Assert that a value is true, in the Python sense.

    >>> validate = Schema(IsTrue())

    "In the Python sense" means that implicitly false values, such as empty
    lists, dictionaries, etc. are treated as "false":

    >>> with raises(MultipleInvalid, "value was not true"):
    ...   validate([])
    >>> validate([1])
    [1]
    >>> with raises(MultipleInvalid, "value was not true"):
    ...   validate(False)

    ...and so on.

    >>> try:
    ...  validate([])
    ... except MultipleInvalid as e:
    ...   assert isinstance(e.errors[0], TrueInvalid)
    """
    return v


@message('value was not false', cls=FalseInvalid)
def IsFalse(v):
    """Assert that a value is false, in the Python sense.

    (see :func:`IsTrue` for more detail)

    >>> validate = Schema(IsFalse())
    >>> validate([])
    []
    >>> with raises(MultipleInvalid, "value was not false"):
    ...   validate(True)

    >>> try:
    ...  validate(True)
    ... except MultipleInvalid as e:
    ...   assert isinstance(e.errors[0], FalseInvalid)
    """
    if v:
        raise ValueError
    return v


@message('expected boolean', cls=BooleanInvalid)
def Boolean(v):
    """Convert human-readable boolean values to a bool.

    Accepted values are 1, true, yes, on, enable, and their negatives.
    Non-string values are cast to bool.

    >>> validate = Schema(Boolean())
    >>> validate(True)
    True
    >>> validate("1")
    True
    >>> validate("0")
    False
    >>> with raises(MultipleInvalid, "expected boolean"):
    ...   validate('moo')
    >>> try:
    ...  validate('moo')
    ... except MultipleInvalid as e:
    ...   assert isinstance(e.errors[0], BooleanInvalid)
    """
    if isinstance(v, basestring):
        v = v.lower()
        if v in ('1', 'true', 'yes', 'on', 'enable'):
            return True
        if v in ('0', 'false', 'no', 'off', 'disable'):
            return False
        raise ValueError
    return bool(v)


class Any(object):
    """Use the first validated value.

    :param msg: Message to deliver to user if validation fails.
    :param kwargs: All other keyword arguments are passed to the sub-Schema constructors.
    :returns: Return value of the first validator that passes.

    >>> validate = Schema(Any('true', 'false',
    ...                       All(Any(int, bool), Coerce(bool))))
    >>> validate('true')
    'true'
    >>> validate(1)
    True
    >>> with raises(MultipleInvalid, "not a valid value"):
    ...   validate('moo')

    msg argument is used

    >>> validate = Schema(Any(1, 2, 3, msg="Expected 1 2 or 3"))
    >>> validate(1)
    1
    >>> with raises(MultipleInvalid, "Expected 1 2 or 3"):
    ...   validate(4)
    """

    def __init__(self, *validators, **kwargs):
        self.validators = validators
        self.msg = kwargs.pop('msg', None)
        self._schemas = [Schema(val, **kwargs) for val in validators]

    def __call__(self, v):
        error = None
        for schema in self._schemas:
            try:
                return schema(v)
            except Invalid as e:
                if error is None or len(e.path) > len(error.path):
                    error = e
        else:
            if error:
                raise error if self.msg is None else AnyInvalid(self.msg)
            raise AnyInvalid(self.msg or 'no valid value found')

    def __repr__(self):
        return 'Any([%s])' % (", ".join(repr(v) for v in self.validators))


# Convenience alias
Or = Any


class All(object):
    """Value must pass all validators.

    The output of each validator is passed as input to the next.

    :param msg: Message to deliver to user if validation fails.
    :param kwargs: All other keyword arguments are passed to the sub-Schema constructors.

    >>> validate = Schema(All('10', Coerce(int)))
    >>> validate('10')
    10
    """

    def __init__(self, *validators, **kwargs):
        self.validators = validators
        self.msg = kwargs.pop('msg', None)
        self._schemas = [Schema(val, **kwargs) for val in validators]

    def __call__(self, v):
        try:
            for schema in self._schemas:
                v = schema(v)
        except Invalid as e:
            raise e if self.msg is None else AllInvalid(self.msg)
        return v

    def __repr__(self):
        return 'All(%s, msg=%r)' % (
            ", ".join(repr(v) for v in self.validators),
            self.msg
        )


# Convenience alias
And = All


class Match(object):
    """Value must be a string that matches the regular expression.

    >>> validate = Schema(Match(r'^0x[A-F0-9]+$'))
    >>> validate('0x123EF4')
    '0x123EF4'
    >>> with raises(MultipleInvalid, "does not match regular expression"):
    ...   validate('123EF4')

    >>> with raises(MultipleInvalid, 'expected string or buffer'):
    ...   validate(123)

    Pattern may also be a _compiled regular expression:

    >>> validate = Schema(Match(re.compile(r'0x[A-F0-9]+', re.I)))
    >>> validate('0x123ef4')
    '0x123ef4'
    """

    def __init__(self, pattern, msg=None):
        if isinstance(pattern, basestring):
            pattern = re.compile(pattern)
        self.pattern = pattern
        self.msg = msg

    def __call__(self, v):
        try:
            match = self.pattern.match(v)
        except TypeError:
            raise MatchInvalid("expected string or buffer")
        if not match:
            raise MatchInvalid(self.msg or 'does not match regular expression')
        return v

    def __repr__(self):
        return 'Match(%r, msg=%r)' % (self.pattern.pattern, self.msg)


class Replace(object):
    """Regex substitution.

    >>> validate = Schema(All(Replace('you', 'I'),
    ...                       Replace('hello', 'goodbye')))
    >>> validate('you say hello')
    'I say goodbye'
    """

    def __init__(self, pattern, substitution, msg=None):
        if isinstance(pattern, basestring):
            pattern = re.compile(pattern)
        self.pattern = pattern
        self.substitution = substitution
        self.msg = msg

    def __call__(self, v):
        return self.pattern.sub(self.substitution, v)

    def __repr__(self):
        return 'Replace(%r, %r, msg=%r)' % (self.pattern.pattern,
                                            self.substitution,
                                            self.msg)


def _url_validation(v):
    parsed = urlparse.urlparse(v)
    if not parsed.scheme or not parsed.netloc:
        raise UrlInvalid("must have a URL scheme and host")
    return parsed


@message('expected an Email', cls=EmailInvalid)
def Email(v):
    """Verify that the value is an Email or not.

    >>> s = Schema(Email())
    >>> with raises(MultipleInvalid, 'expected an Email'):
    ...   s("a.com")
    >>> with raises(MultipleInvalid, 'expected an Email'):
    ...   s("a@.com")
    >>> with raises(MultipleInvalid, 'expected an Email'):
    ...   s("a@.com")
    >>> s('t@x.com')
    't@x.com'
    """
    try:
        if not v or "@" not in v:
            raise EmailInvalid("Invalid Email")
        user_part, domain_part = v.rsplit('@', 1)

        if not (USER_REGEX.match(user_part) and DOMAIN_REGEX.match(domain_part)):
            raise EmailInvalid("Invalid Email")
        return v
    except:
        raise ValueError


@message('expected a Fully qualified domain name URL', cls=UrlInvalid)
def FqdnUrl(v):
    """Verify that the value is a Fully qualified domain name URL.

    >>> s = Schema(FqdnUrl())
    >>> with raises(MultipleInvalid, 'expected a Fully qualified domain name URL'):
    ...   s("http://localhost/")
    >>> s('http://w3.org')
    'http://w3.org'
    """
    try:
        parsed_url = _url_validation(v)
        if "." not in parsed_url.netloc:
            raise UrlInvalid("must have a domain name in URL")
        return v
    except:
        raise ValueError


@message('expected a URL', cls=UrlInvalid)
def Url(v):
    """Verify that the value is a URL.

    >>> s = Schema(Url())
    >>> with raises(MultipleInvalid, 'expected a URL'):
    ...   s(1)
    >>> s('http://w3.org')
    'http://w3.org'
    """
    try:
        _url_validation(v)
        return v
    except:
        raise ValueError


@message('not a file', cls=FileInvalid)
@truth
def IsFile(v):
    """Verify the file exists.

    >>> os.path.basename(IsFile()(__file__)).startswith('validators.py')
    True
    >>> with raises(FileInvalid, 'not a file'):
    ...   IsFile()("random_filename_goes_here.py")
    """
    return os.path.isfile(v)


@message('not a directory', cls=DirInvalid)
@truth
def IsDir(v):
    """Verify the directory exists.

    >>> IsDir()('/')
    '/'
    """
    return os.path.isdir(v)


@message('path does not exist', cls=PathInvalid)
@truth
def PathExists(v):
    """Verify the path exists, regardless of its type.

    >>> os.path.basename(PathExists()(__file__)).startswith('validators.py')
    True
    >>> with raises(Invalid, 'path does not exist'):
    ...   PathExists()("random_filename_goes_here.py")
    """
    return os.path.exists(v)


class Range(object):
    """Limit a value to a range.

    Either min or max may be omitted.
    Either min or max can be excluded from the range of accepted values.

    :raises Invalid: If the value is outside the range.

    >>> s = Schema(Range(min=1, max=10, min_included=False))
    >>> s(5)
    5
    >>> s(10)
    10
    >>> with raises(MultipleInvalid, 'value must be at most 10'):
    ...   s(20)
    >>> with raises(MultipleInvalid, 'value must be higher than 1'):
    ...   s(1)
    >>> with raises(MultipleInvalid, 'value must be lower than 10'):
    ...   Schema(Range(max=10, max_included=False))(20)
    """

    def __init__(self, min=None, max=None, min_included=True,
                 max_included=True, msg=None):
        self.min = min
        self.max = max
        self.min_included = min_included
        self.max_included = max_included
        self.msg = msg

    def __call__(self, v):
        if self.min_included:
            if self.min is not None and v < self.min:
                raise RangeInvalid(
                    self.msg or 'value must be at least %s' % self.min)
        else:
            if self.min is not None and v <= self.min:
                raise RangeInvalid(
                    self.msg or 'value must be higher than %s' % self.min)
        if self.max_included:
            if self.max is not None and v > self.max:
                raise RangeInvalid(
                    self.msg or 'value must be at most %s' % self.max)
        else:
            if self.max is not None and v >= self.max:
                raise RangeInvalid(
                    self.msg or 'value must be lower than %s' % self.max)
        return v

    def __repr__(self):
        return ('Range(min=%r, max=%r, min_included=%r,'
                ' max_included=%r, msg=%r)' % (self.min, self.max,
                                               self.min_included,
                                               self.max_included,
                                               self.msg))


class Clamp(object):
    """Clamp a value to a range.

    Either min or max may be omitted.
    >>> s = Schema(Clamp(min=0, max=1))
    >>> s(0.5)
    0.5
    >>> s(5)
    1
    >>> s(-1)
    0
    """

    def __init__(self, min=None, max=None, msg=None):
        self.min = min
        self.max = max
        self.msg = msg

    def __call__(self, v):
        if self.min is not None and v < self.min:
            v = self.min
        if self.max is not None and v > self.max:
            v = self.max
        return v

    def __repr__(self):
        return 'Clamp(min=%s, max=%s)' % (self.min, self.max)


class Length(object):
    """The length of a value must be in a certain range."""

    def __init__(self, min=None, max=None, msg=None):
        self.min = min
        self.max = max
        self.msg = msg

    def __call__(self, v):
        if self.min is not None and len(v) < self.min:
            raise LengthInvalid(
                self.msg or 'length of value must be at least %s' % self.min)
        if self.max is not None and len(v) > self.max:
            raise LengthInvalid(
                self.msg or 'length of value must be at most %s' % self.max)
        return v

    def __repr__(self):
        return 'Length(min=%s, max=%s)' % (self.min, self.max)


class Datetime(object):
    """Validate that the value matches the datetime format."""

    DEFAULT_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

    def __init__(self, format=None, msg=None):
        self.format = format or self.DEFAULT_FORMAT
        self.msg = msg

    def __call__(self, v):
        try:
            datetime.datetime.strptime(v, self.format)
        except (TypeError, ValueError):
            raise DatetimeInvalid(
                self.msg or 'value does not match'
                            ' expected format %s' % self.format)
        return v

    def __repr__(self):
        return 'Datetime(format=%s)' % self.format


class In(object):
    """Validate that a value is in a collection."""

    def __init__(self, container, msg=None):
        self.container = container
        self.msg = msg

    def __call__(self, v):
        try:
            check = v not in self.container
        except TypeError:
            check = True
        if check:
            raise InInvalid(self.msg or 'value is not allowed')
        return v

    def __repr__(self):
        return 'In(%s)' % (self.container,)


class NotIn(object):
    """Validate that a value is not in a collection."""

    def __init__(self, container, msg=None):
        self.container = container
        self.msg = msg

    def __call__(self, v):
        try:
            check = v in self.container
        except TypeError:
            check = True
        if check:
            raise NotInInvalid(self.msg or 'value is not allowed')
        return v

    def __repr__(self):
        return 'NotIn(%s)' % (self.container,)


class ExactSequence(object):
    """Matches each element in a sequence against the corresponding element in
    the validators.

    :param msg: Message to deliver to user if validation fails.
    :param kwargs: All other keyword arguments are passed to the sub-Schema
        constructors.

    >>> from voluptuous import Schema, ExactSequence
    >>> validate = Schema(ExactSequence([str, int, list, list]))
    >>> validate(['hourly_report', 10, [], []])
    ['hourly_report', 10, [], []]
    >>> validate(('hourly_report', 10, [], []))
    ('hourly_report', 10, [], [])
    """

    def __init__(self, validators, **kwargs):
        self.validators = validators
        self.msg = kwargs.pop('msg', None)
        self._schemas = [Schema(val, **kwargs) for val in validators]

    def __call__(self, v):
        if not isinstance(v, (list, tuple)):
            raise ExactSequenceInvalid(self.msg)
        try:
            v = type(v)(schema(x) for x, schema in zip(v, self._schemas))
        except Invalid as e:
            raise e if self.msg is None else ExactSequenceInvalid(self.msg)
        return v

    def __repr__(self):
        return 'ExactSequence([%s])' % (", ".join(repr(v)
                                                  for v in self.validators))


class Unique(object):
    """Ensure an iterable does not contain duplicate items.

    Only iterables convertable to a set are supported (native types and
    objects with correct __eq__).

    JSON does not support set, so they need to be presented as arrays.
    Unique allows ensuring that such array does not contain dupes.

    >>> s = Schema(Unique())
    >>> s([])
    []
    >>> s([1, 2])
    [1, 2]
    >>> with raises(Invalid, 'contains duplicate items: [1]'):
    ...   s([1, 1, 2])
    >>> with raises(Invalid, "contains duplicate items: ['one']"):
    ...   s(['one', 'two', 'one'])
    >>> with raises(Invalid, regex="^contains unhashable elements: "):
    ...   s([set([1, 2]), set([3, 4])])
    >>> s('abc')
    'abc'
    >>> with raises(Invalid, regex="^contains duplicate items: "):
    ...   s('aabbc')
    """

    def __init__(self, msg=None):
        self.msg = msg

    def __call__(self, v):
        try:
            set_v = set(v)
        except TypeError as e:
            raise TypeInvalid(
                self.msg or 'contains unhashable elements: {0}'.format(e))
        if len(set_v) != len(v):
            seen = set()
            dupes = list(set(x for x in v if x in seen or seen.add(x)))
            raise Invalid(
                self.msg or 'contains duplicate items: {0}'.format(dupes))
        return v

    def __repr__(self):
        return 'Unique()'
