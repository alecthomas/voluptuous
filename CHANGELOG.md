# Changelog

## [Unreleased]

**Changes**:

- [#198](https://github.com/alecthomas/voluptuous/issues/198):
  `{}` and `[]` now always evaluate as is, instead of as any dict or any list.
  To specify a free-form list, use `list` instead of `[]`. To specify a
  free-form dict, use `dict` instead of `Schema({}, extra=ALLOW_EXTRA)`.

**New**:

**Fixes**:

- [#259](https://github.com/alecthomas/voluptuous/issues/259):
  Fixed a performance issue of exponential complexity where all of the dict keys were matched against all keys in the schema.
  This resulted in O(n*m) complexity where n is the number of keys in the dict being validated and m is the number of keys in the schema.
  The fix ensures that each key in the dict is matched against the relevant schema keys only. It now works in O(n).

## 0.9.3 (2016-08-03)

Changelog not kept for 0.9.3 and earlier releases.
