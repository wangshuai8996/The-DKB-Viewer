'''
Exceptions used on the client side
'''

class ReturnedException(Exception):
    def __init__(self, message, *extra):
        self.message = message
        self.extra = extra

    def __str__(self):
        if not self.extra:
            return self.message
        else:
            return "{}\n{}".format(self.message, self.extra)

class DKBclosedError(ReturnedException):
    pass

class DKBnotFoundError(ReturnedException):
    pass

class DKBnotResetError(ReturnedException):
    pass

class IdentifierWrongError(ReturnedException):
    pass

class ContextNotFoundError(ReturnedException):
    pass

class NoContextSetError(ReturnedException):
    pass

class ExistingContextError(ReturnedException):
    pass

class NameInUseError(ReturnedException):
    pass

class NotAConceptError(ReturnedException):
    pass

class NotAConceptUnderCurrentContextError(NotAConceptError):
    pass

class ConceptNotFoundError(NotAConceptError):
    pass

class InstanceNotFoundError(ReturnedException):
    pass

class UnknownTypeError(ReturnedException):
    pass
    
class PermissionDeniedError(ReturnedException):
    pass

class WritingPermissionDeniedError(PermissionDeniedError):
    pass

class FrozenPermissionDeniedError(PermissionDeniedError):
    pass

class AlreadyLoggedInError(ReturnedException):
    pass

class MultiUserError(ReturnedException):
    pass
    
class NamePropertyDoesNotExistError(ReturnedException):
    pass
    
class PropertyRangeNotMatchingTypeError(ReturnedException):
    pass
