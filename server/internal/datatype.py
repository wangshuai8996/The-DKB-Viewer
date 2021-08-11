from dare_kb.common import Exceptions as E

_builtInDatatype = { # a dictionary from string key (the Concept's name) to the Concept
#    'Method': DKBm.Method,        # ones beyond here may not exist
#    'Dataset': DKBm.Dataset,    # or be dummies with limited content and function
#    'Collection': DKBm.Collection,
#    'Context': DKBm.Context,     # for tailoring for different groups, individuals & roles
    'String': str,        # built-in types
#    'Time': DKBm.Time,
    'Number': float,        # all forms
    'Integer': int,    # a specialisation of Number
#    'FloatingPoint': DKBm.FloatingPoint,     # maybe should be real, even though that
                                            # isn't mathematically correct
#    'Complex': DKBm.Complex,
    }

def has_str(type_str: str):
    return type_str in _builtInDatatype

def from_str(type_str: str):
    if type_str in _builtInDatatype:
        return _builtInDatatype[type_str]
    raise E.UnknownTypeError(type_str)

def to_str(type_py):
    for k, v in _builtInDatatype.items():
        if v == type_py:
            return k
    raise E.UnknownTypeError(type_py)
