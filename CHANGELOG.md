# Changelog

## [0.15.2]

**Fixes**:

* [522](https://github.com/alecthomas/voluptuous/pull/522) Fix regression with ALLOW_EXTRA and `Any` validator

## [0.15.1]

**Fixes**:

* [515](https://github.com/alecthomas/voluptuous/pull/515) Fix `Remove` not removing keys that do not validate
* [516](https://github.com/alecthomas/voluptuous/pull/516) Improve validator typing to allow non-number formats for min and max
* [517](https://github.com/alecthomas/voluptuous/pull/517) Remove `Maybe` validator typing
* [518](https://github.com/alecthomas/voluptuous/pull/518) Use typing.Container for `In` validator
* [519](https://github.com/alecthomas/voluptuous/pull/519) Don't enforce type for unused description attribute
* [521](https://github.com/alecthomas/voluptuous/pull/521) Type schema attribute as `Any`

## [0.15.0]

**Fixes**:

* [#512](https://github.com/alecthomas/voluptuous/pull/512): Add Any type to defaults
* [#513](https://github.com/alecthomas/voluptuous/pull/513): Only calculate hash once for Marker objects
  
**Changes**:

* [#514](https://github.com/alecthomas/voluptuous/pull/514): Remove python 3.8 support

## [0.14.2]

**New**:
* [#507](https://github.com/alecthomas/voluptuous/pull/507): docs: document description field of Marker

**Fixes**:
* [#506](https://github.com/alecthomas/voluptuous/pull/506): fix: allow unsortable containers in In and NotIn validators (fixes [#451](https://github.com/alecthomas/voluptuous/issues/451)) (bug introduced in 0.12.1)
* [#488](https://github.com/alecthomas/voluptuous/pull/488): fix(typing): fix type hint for Coerce type param (bug introduced in 0.14.0)
* [#497](https://github.com/alecthomas/voluptuous/pull/497): fix(typing): allow path to be a list of strings, integers or any other hashables (bug introduced in 0.14.0)

**Changes**:
* [#499](https://github.com/alecthomas/voluptuous/pull/499): support: drop support for python 3.7
* [#501](https://github.com/alecthomas/voluptuous/pull/501): support: run tests on python 3.11
* [#502](https://github.com/alecthomas/voluptuous/pull/502): support: run tests on python 3.12
* [#495](https://github.com/alecthomas/voluptuous/pull/495): refactor: drop duplicated type checks in Schema._compile
* [#500](https://github.com/alecthomas/voluptuous/pull/500): refactor: fix few tests, use pytest.raises, extend raises helper
* [#503](https://github.com/alecthomas/voluptuous/pull/503): refactor: Add linters configuration, reformat whole code

## [0.14.1]

**Changes**:
* [#487](https://github.com/alecthomas/voluptuous/pull/487): Add pytest.ini and tox.ini to sdist
* [#494](https://github.com/alecthomas/voluptuous/pull/494): Add `python_requires` so package installers know requirement is >= 3.7

## [0.14.0]

**Fixes**:
* [#470](https://github.com/alecthomas/voluptuous/pull/470): Fix a few code comment typos
* [#472](https://github.com/alecthomas/voluptuous/pull/472): Change to SPDX conform license string


**New**:
* [#475](https://github.com/alecthomas/voluptuous/pull/475): Add typing information
* [#478](https://github.com/alecthomas/voluptuous/pull/478): Fix new type hint of schemas, for example for `Required('key')`
* [#486](https://github.com/alecthomas/voluptuous/pull/486): Fix new type hints and enable `mypy`
* [#479](https://github.com/alecthomas/voluptuous/pull/479): Allow error reporting on keys

**Changes**:
* [#476](https://github.com/alecthomas/voluptuous/pull/476): Set static PyPI project description
* [#482](https://github.com/alecthomas/voluptuous/pull/482): Remove Travis build status badge

## [0.13.1]

**Fixes**:

- [#439](https://github.com/alecthomas/voluptuous/pull/454): Ignore `Enum` if it is unavailable
- [#456](https://github.com/alecthomas/voluptuous/pull/456): Fix email regex match for Python 2.7

**New**:

- [#457](https://github.com/alecthomas/voluptuous/pull/457): Enable github actions
- [#462](https://github.com/alecthomas/voluptuous/pull/462): Convert codebase to adhere to `flake8` W504 (PEP 8)
- [#459](https://github.com/alecthomas/voluptuous/pull/459): Enable `flake8` in github actions
- [#464](https://github.com/alecthomas/voluptuous/pull/464): `pytest` migration + enable Python 3.10

## [0.13.0]

**Changes**:

- [#450](https://github.com/alecthomas/voluptuous/pull/450): Display valid `Enum` values in `Coerce`

## [0.12.2]

**Fixes**:

- [#439](https://github.com/alecthomas/voluptuous/issues/439): Revert Breaking `Maybe` change in 0.12.1
- [#447](https://github.com/alecthomas/voluptuous/issues/447): Fix Email Regex to not match on extra characters

## [0.12.1]

**Changes**:
- [#435](https://github.com/alecthomas/voluptuous/pull/435): Extended a few tests (`Required` and `In`)
- [#425](https://github.com/alecthomas/voluptuous/pull/425): Improve error message for `In` and `NotIn`
- [#436](https://github.com/alecthomas/voluptuous/pull/436): Add sorted() for `In` and `NotIn` + fix tests
- [#437](https://github.com/alecthomas/voluptuous/pull/437): Grouped `Maybe` tests plus added another `Range` test
- [#438](https://github.com/alecthomas/voluptuous/pull/438): Extend tests for `Schema` with empty list or dict

**New**:
- [#433](https://github.com/alecthomas/voluptuous/pull/433): Add Python 3.9 support

**Fixes**:
- [#431](https://github.com/alecthomas/voluptuous/pull/431): Fixed typos + made spelling more consistent
- [#411](https://github.com/alecthomas/voluptuous/pull/411): Ensure `Maybe` propagates error information
- [#434](https://github.com/alecthomas/voluptuous/pull/434): Remove value enumeration when validating empty list

## [0.12.0]

**Changes**:
- n/a

**New**:
- [#368](https://github.com/alecthomas/voluptuous/pull/368): Allow a discriminant field in validators

**Fixes**:
- [#420](https://github.com/alecthomas/voluptuous/pull/420): Fixed issue with 'required' not being set properly and added test 
- [#414](https://github.com/alecthomas/voluptuous/pull/414): Handle incomparable values in Range
- [#427](https://github.com/alecthomas/voluptuous/pull/427): Added additional tests for Range, Clamp and Length + catch TypeError exceptions

## [0.11.7]

**Changes**:

- [#378](https://github.com/alecthomas/voluptuous/pull/378): Allow `extend()` of a `Schema` to return a subclass of a `Schema` as well.

**New**:

- [#364](https://github.com/alecthomas/voluptuous/pull/364): Accept `description` for `Inclusive` instances.
- [#373](https://github.com/alecthomas/voluptuous/pull/373): Accept `msg` for `Maybe` instances.
- [#382](https://github.com/alecthomas/voluptuous/pull/382): Added support for default values in `Inclusive` instances.

**Fixes**:

- [#371](https://github.com/alecthomas/voluptuous/pull/371): Fixed `DeprecationWarning` related to `collections.Mapping`.
- [#377](https://github.com/alecthomas/voluptuous/pull/377): Preserve Unicode strings when passed to utility functions (e.g., `Lower()`, `Upper()`).
- [#380](https://github.com/alecthomas/voluptuous/pull/380): Fixed regression with `Any` and `required` flag.

## [0.11.5]

- Fixed issue with opening README file in `setup.py`.

## [0.11.4]

- Removed use of `pypandoc` as Markdown is now supported by `setup()`.

## [0.11.3] and [0.11.2]

**Changes**:

- [#349](https://github.com/alecthomas/voluptuous/pull/349): Support Python 3.7.
- [#343](https://github.com/alecthomas/voluptuous/pull/343): Drop support for Python 3.3.

**New**:

- [#342](https://github.com/alecthomas/voluptuous/pull/342): Add support for sets and frozensets.

**Fixes**:

- [#332](https://github.com/alecthomas/voluptuous/pull/332): Fix Python 3.x compatibility for setup.py when `pypandoc` is installed.
- [#348](https://github.com/alecthomas/voluptuous/pull/348): Include path in `AnyInvalid` errors.
- [#351](https://github.com/alecthomas/voluptuous/pull/351): Fix `Date` behaviour when a custom format is specified.

## [0.11.1] and [0.11.0]

**Changes**:

- [#293](https://github.com/alecthomas/voluptuous/pull/293): Support Python 3.6.
- [#294](https://github.com/alecthomas/voluptuous/pull/294): Drop support for Python 2.6, 3.1 and 3.2.
- [#318](https://github.com/alecthomas/voluptuous/pull/318): Allow to use nested schema and allow any validator to be compiled.
- [#324](https://github.com/alecthomas/voluptuous/pull/324):
  Default values MUST now pass validation just as any regular value. This is a backward incompatible change if a schema uses default values that don't pass validation against the specified schema.
- [#328](https://github.com/alecthomas/voluptuous/pull/328):
  Modify `__lt__` in Marker class to allow comparison with non Marker objects, such as str and int.

**New**:

- [#307](https://github.com/alecthomas/voluptuous/pull/307): Add description field to `Marker` instances.
- [#311](https://github.com/alecthomas/voluptuous/pull/311): Add `Schema.infer` method for basic schema inference.
- [#314](https://github.com/alecthomas/voluptuous/pull/314): Add `SomeOf` validator.

**Fixes**:

- [#279](https://github.com/alecthomas/voluptuous/pull/279):
  Treat Python 2 old-style classes like types when validating.
- [#280](https://github.com/alecthomas/voluptuous/pull/280): Make
  `IsDir()`, `IsFile()` and `PathExists()` consistent between different Python versions.
- [#290](https://github.com/alecthomas/voluptuous/pull/290): Use absolute imports to avoid import conflicts.
- [#291](https://github.com/alecthomas/voluptuous/pull/291): Fix `Coerce` validator to catch `decimal.InvalidOperation`.
- [#298](https://github.com/alecthomas/voluptuous/pull/298): Make `Schema([])` usage consistent with `Schema({})`.
- [#303](https://github.com/alecthomas/voluptuous/pull/303): Allow partial validation when using validate decorator.
- [#316](https://github.com/alecthomas/voluptuous/pull/316): Make `Schema.__eq__` deterministic.
- [#319](https://github.com/alecthomas/voluptuous/pull/319): Replace implementation of `Maybe(s)` with `Any(None, s)` to allow it to be compiled.

## [0.10.5]

- [#278](https://github.com/alecthomas/voluptuous/pull/278): Unicode
translation to python 2 issue fixed.

## [0.10.2]

**Changes**:

- [#195](https://github.com/alecthomas/voluptuous/pull/195):
  `Range` raises `RangeInvalid` when testing `math.nan`.
- [#215](https://github.com/alecthomas/voluptuous/pull/215):
  `{}` and `[]` now always evaluate as is, instead of as any dict or any list.
  To specify a free-form list, use `list` instead of `[]`. To specify a
  free-form dict, use `dict` instead of `Schema({}, extra=ALLOW_EXTRA)`.
- [#224](https://github.com/alecthomas/voluptuous/pull/224):
  Change the encoding of keys in error messages from Unicode to UTF-8.

**New**:

- [#185](https://github.com/alecthomas/voluptuous/pull/185):
  Add argument validation decorator.
- [#199](https://github.com/alecthomas/voluptuous/pull/199):
  Add `Unordered`.
- [#200](https://github.com/alecthomas/voluptuous/pull/200):
  Add `Equal`.
- [#207](https://github.com/alecthomas/voluptuous/pull/207):
  Add `Number`.
- [#210](https://github.com/alecthomas/voluptuous/pull/210):
  Add `Schema` equality check.
- [#212](https://github.com/alecthomas/voluptuous/pull/212):
  Add `coveralls`.
- [#227](https://github.com/alecthomas/voluptuous/pull/227):
  Improve `Marker` management in `Schema`.
- [#232](https://github.com/alecthomas/voluptuous/pull/232):
  Add `Maybe`.
- [#234](https://github.com/alecthomas/voluptuous/pull/234):
  Add `Date`.
- [#236](https://github.com/alecthomas/voluptuous/pull/236), [#237](https://github.com/alecthomas/voluptuous/pull/237), and [#238](https://github.com/alecthomas/voluptuous/pull/238):
  Add script for updating `gh-pages`.
- [#256](https://github.com/alecthomas/voluptuous/pull/256):
  Add support for `OrderedDict` validation.
- [#258](https://github.com/alecthomas/voluptuous/pull/258):
  Add `Contains`.

**Fixes**:

- [#197](https://github.com/alecthomas/voluptuous/pull/197):
  `ExactSequence` checks sequences are the same length.
- [#201](https://github.com/alecthomas/voluptuous/pull/201):
  Empty lists are evaluated as is.
- [#205](https://github.com/alecthomas/voluptuous/pull/205):
  Filepath validators correctly handle `None`.
- [#206](https://github.com/alecthomas/voluptuous/pull/206):
  Handle non-subscriptable types in `humanize_error`.
- [#231](https://github.com/alecthomas/voluptuous/pull/231):
  Validate `namedtuple` as a `tuple`.
- [#235](https://github.com/alecthomas/voluptuous/pull/235):
  Update docstring.
- [#249](https://github.com/alecthomas/voluptuous/pull/249):
  Update documentation.
- [#262](https://github.com/alecthomas/voluptuous/pull/262):
  Fix a performance issue of exponential complexity where all of the dict keys were matched against all keys in the schema.
  This resulted in O(n*m) complexity where n is the number of keys in the dict being validated and m is the number of keys in the schema.
  The fix ensures that each key in the dict is matched against the relevant schema keys only. It now works in O(n).
- [#266](https://github.com/alecthomas/voluptuous/pull/266):
  Remove setuptools as a dependency.

## 0.9.3 (2016-08-03)

Changelog not kept for 0.9.3 and earlier releases.
