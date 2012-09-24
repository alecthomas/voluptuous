# encoding: utf-8
#
# Copyright (C) 2010 Alec Thomas <alec@swapoff.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Jean-Tiare Le Bigot <admin@jtlebi.fr>

from .voluptuous import *
from _deprecated import deprecated

marker = Marker
optional = Optional
required = Required

@deprecated(Extra)
def extra(_): pass

@deprecated(Msg)
def msg(schema, msg): pass

@deprecated(Coerce)
def coerce(type, msg=None): pass

@deprecated(IsTrue)
def true(msg=None): pass

@deprecated(IsFalse)
def false(msg=None): pass

@deprecated(Boolean)
def boolean(msg=None): pass

@deprecated(Any)
def any(*validators, **kwargs): pass

@deprecated(All)
def all(*validators, **kwargs): pass

@deprecated(Match)
def match(pattern, msg=None): pass

@deprecated(Sub)
def sub(pattern, substitution, msg=None): pass

@deprecated(Url)
def url(msg=None): pass

@deprecated(IsFile)
def isfile(msg=None): pass

@deprecated(IsDir)
def isdir(msg=None): pass

@deprecated(PathExists)
def path_exists(msg=None): pass

@deprecated(InRange)
def range(min=None, max=None, msg=None): pass

@deprecated(Clamp)
def clamp(min=None, max=None, msg=None): pass

@deprecated(Length)
def length(min=None, max=None, msg=None): pass

@deprecated(ToLower)
def lower(v): pass

@deprecated(ToUpper)
def upper(v): pass

@deprecated(Capitalize)
def capitalize(v): pass

@deprecated(Title)
def title(v): pass

@deprecated(DefaultTo)
def default_to(default_value, msg=None): pass
