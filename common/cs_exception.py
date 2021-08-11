'''
Structured exceptions passed from server to client
'''

import traceback
import warnings
from . import Exceptions as E
from .Exceptions import ReturnableError
from . import client_exception as cE


error_mapping = {
        ('DKBclosed', E.DKBclosedError, cE.DKBclosedError),
        ('DKBnotFound', E.DKBnotFoundError, cE.DKBnotFoundError),
        ('DKBnotReset', E.DKBnotResetError, cE.DKBnotResetError),
        ('IdentifierWrong', E.IdentifierWrongError, cE.IdentifierWrongError),
        ('ContextNotFound', E.ContextNotFoundError, cE.ContextNotFoundError),
        ('NoContextSet', E.NoContextSetError, cE.NoContextSetError),
        ('ExistingContext', E.ExistingContextError, cE.ExistingContextError),
        ('NameInUse', E.NameInUseError, cE.NameInUseError),
        ('NotAConcept', E.NotAConceptError, cE.NotAConceptError),
        ('NotAConceptUnderCurrentContext', E.NotAConceptUnderCurrentContextError, cE.NotAConceptUnderCurrentContextError),
        ('ConceptNotFound', E.ConceptNotFoundError, cE.ConceptNotFoundError),
        ('InstanceNotFound', E.InstanceNotFoundError, cE.InstanceNotFoundError),
        ('UnknownType', E.UnknownTypeError, cE.UnknownTypeError),
        ('PermissionDenied', E.PermissionDeniedError, cE.PermissionDeniedError),
        ('TypeError', TypeError, TypeError),
        ('DeprecationWarning', DeprecationWarning, DeprecationWarning),
        ('WritingPermissionDenied', E.WritingPermissionDeniedError, cE.WritingPermissionDeniedError),
        ('FrozenPermissionDenied', E.FrozenPermissionDeniedError, cE.FrozenPermissionDeniedError),
        ('AlreadyLoggedIn', E.AlreadyLoggedInError, cE.AlreadyLoggedInError),
        ('MultiUser', E.MultiUserError, cE.MultiUserError),
        ('PropertyRangeNotMatchingType', E.PropertyRangeNotMatchingTypeError, cE.PropertyRangeNotMatchingTypeError),
        ('NamePropertyDoesNotExist', E.NamePropertyDoesNotExistError, cE.NamePropertyDoesNotExistError)
        }

def find_error_code(err):
    '''
    @param err: a server-side error
    '''
    for error_code, exception, _ in error_mapping:
        if isinstance(err, exception):
            return error_code

def find_exception(err_code):
    for error_code, _, exception in error_mapping:
        if err_code == error_code:
            return exception
    return None


def try_propagate(e):
    traceback.print_exc()
    error_code = find_error_code(e)
    if error_code:
        return "{}\n{}".format(error_code, e), 499
    else:
        raise e

def handle_server_exception(status_code, message):
    if status_code == 499:
        parts = message.split('\n')
        error_code, message, extra = parts[0], parts[1], parts[2:]
        raise DKBException(error_code, message, extra)
    else:
        raise Exception(message)


class DKBException(Exception):
    def __init__(self, error_code, message, *extra):
        self.error_code = error_code
        self.message = message
        self.extra = extra

    def coerce(self):
        raise find_exception(self.error_code)(self.message, *self.extra)


