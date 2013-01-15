# encoding: utf-8
#
# Copyright (C) 2010-2013 Alec Thomas <alec@swapoff.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Alec Thomas <alec@swapoff.org>

"""
Backward-compatibility functions/classes for Voluptous.

Will be removed in 1.0.
"""

import warnings
from .voluptuous import (
    Marker, Optional, Required, Msg, IsTrue, IsFalse, Boolean,
    Any, All, Match, Replace, IsFile, IsDir, PathExists, Range, Clamp,
    Length, Lower, Upper, Capitalize, Title, DefaultTo, MultipleInvalid
)


# From: http://code.activestate.com/recipes/577819-deprecated-decorator/
def _deprecated(replacement=None):
    def outer(oldfun):
        def inner(*args, **kwargs):
            msg = "voluptuous.%s is deprecated" % oldfun.__name__
            if replacement is not None:
                msg += "; use voluptuous.%s instead" % (replacement.__name__)
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            if replacement is not None:
                return replacement(*args, **kwargs)
            else:
                return oldfun(*args, **kwargs)
        return inner
    return outer


def _deprecated_class(old_name, new_class):
    class DeprecatedClass(new_class):
        def __init__(self, *args, **kwargs):
            warnings.warn(
                'voluptuous.%s is deprecated; use voluptuous.%s instead'
                % (old_name, new_class.__name__),
                DeprecationWarning,
                stacklevel=2,
            )
            new_class.__init__(self, *args, **kwargs)
    return type(old_name, (DeprecatedClass, new_class),
                {'__doc__': 'This class is deprecated, use: ' + new_class.__name__})


def _deprecated_function(old_name, new_function):
    @_deprecated(new_function)
    def f(*args, **kwargs):
        return new_function(*args, **kwargs)

    return f


marker = _deprecated_class('marker', Marker)
optional = _deprecated_class('optional', Optional)
required = _deprecated_class('required', Required)
InvalidList = _deprecated_class('InvalidList', MultipleInvalid)
msg = _deprecated_function('msg', Msg)
true = _deprecated_function('true', IsTrue)
false = _deprecated_function('false', IsFalse)
boolean = _deprecated_function('boolean', Boolean)
any = _deprecated_function('any', Any)
all = _deprecated_function('all', All)
match = _deprecated_function('match', Match)
sub = _deprecated_function('sub', Replace)
isfile = _deprecated_function('isfile', IsFile)
isdir = _deprecated_function('isdir', IsDir)
path_exists = _deprecated_function('path_exists', PathExists)
range = _deprecated_function('range', Range)
clamp = _deprecated_function('clamp', Clamp)
length = _deprecated_function('length', Length)
lower = _deprecated_function('lower', Lower)
upper = _deprecated_function('upper', Upper)
capitalize = _deprecated_function('capitalize', Capitalize)
title = _deprecated_function('title', Title)
default_to = _deprecated_function('default_to', DefaultTo)
