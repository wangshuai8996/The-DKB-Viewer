class Error(Exception):
    """ Base class for exceptions in this modules. """
    pass
    
class ReturnableError(Error):
    '''Error which can be returned from server to client'''
    def __init__(self, message, *extra):
        self.message = message
        self.extra = extra
    def __str__(self):
        if not self.extra:
            return self.message
        else:
            return "{}\n{}".format(self.message, self.extra)
            
class PermissionDeniedError(ReturnableError):
    '''Error which can be returned from server to client'''
    def __init__(self, rest_mess):
        super().__init__(rest_mess)

class DKBclosedError(ReturnableError):
    """ Raised when the DKB is no longer open"""
    def __init__(self, function):
        super().__init__("The current instance of the DKB has been closed by a previous call to DKB.close(). Function "+function+" failed.")

class DKBnotFoundError(ReturnableError):
    """ Raised when the DKB is not found"""
    def __init__(self, instance, function):
        super().__init__("The instance of the DKB named "+instance+" cannot be found. Function "+function+" failed.")

class DKBnotResetError(ReturnableError, FileExistsError):
    """ Raised when the given instance already exist and the optional parameter reset has not been supplied to True"""
    def __init__(self, instance):
        super().__init__("The "+instance+" already exists and contains a previous version of the DKB, to use it call the function login otherwise try a different site_name to register your DKB. Another solution is to use the optional argument reset=True to overwrite the existing saved instance of the DKB of the same name.")

class IdentifierWrongError(ReturnableError, SyntaxError):
    """ Raised when an identifier is an empty string or
    contains inappropriate characters"""
    def __init__(self, identifier, function):
        super().__init__("The "+identifier+" contains inappropriate characters or is an empty string. Function "+function+" failed.")

class ContextNotFoundError(ReturnableError):
    """ Raised when a context is not in the DKB or cannot be access by this user or group or context"""
    def __init__(self, context, function):
        super().__init__("Context '"+context+"' cannot be found, unexisting or access not granted. Function "+function+" failed.")

class NoContextSetError(ReturnableError):
    """ Raised when a context is not set up. """
    def __init__(self, function):
        super().__init__("No context set up. Function "+function+" failed.")

class ExistingContextError(ReturnableError):
    """ Raised when trying to create a new context with an existing prefix. """
    def __init__(self, name, function):
        super().__init__("Context '"+name+"' already exists. Function "+function+" failed.")

class NameInUseError(ReturnableError):
    """ Raised when trying to create a new concept with an existing label. """
    def __init__(self, name, list, function):
        super().__init__("A concept for the precise_term: '"+name+"' already exists. Here is the existing concept for this precise_term: "+ str(list) + ". Function "+function+" failed.")

class NotAConceptError(ReturnableError):
    """ Raised if the value supplied for specialises is not
        a Concept or cannot be found.
    """
    def __init__(self, *args):
        if len(args) >= 2:
            name, function = args[:2]
            super().__init__("The concept for specialises: '"+name+"' does not exist or cannot be found. Function "+function+" failed.")
        else:
            super().__init__(args[0])

class NotAConceptUnderCurrentContextError(NotAConceptError):
    """ Raised if the value supplied for specialises is not
        a Concept or cannot be found.
    """
    def __init__(self, name, context, function):
        super().__init__("The concept for specialises: '"+name+"' does not exist or cannot be found under the context " + context +". Function "+function+" failed.")

class ConceptNotFoundError(NotAConceptError):
    """ Raised if the search concept can't be found given search_path.
    """
    def __init__(self, name, function):
        super().__init__("The concept: '"+name+"' does not exist or cannot be found under the current context and associated search_path. Function "+function+" failed.")

class InstanceNotFoundError(ReturnableError):
    """ Raised if the requested identity is not an Instance or can not be found under the current search path.
    """
    def __init__(self, name, function):
        super().__init__("The instance for : '"+name+"' does not exist or cannot be found. Function "+function+" failed.")

class UnknownTypeError(ReturnableError):
    """
    Raised if the type specified by the user (or the database) or used in the system is not recognised by the current version of DKB.
    """
    def __init__(self, atype):
        super().__init__(f"The type {atype} is not recognised by DKB.")

class WritingPermissionDeniedError(ReturnableError):
    """
    Raised if user is trying something he not allowed to.
    """
    def __init__(self, a_message):
        super().__init__(f"You are not allowed to do this action. {a_message}")

class FrozenPermissionDeniedError(ReturnableError):
    """
    Raised if user is trying something he not allowed to because of a Frozen context.
    """
    def __init__(self, a_message):
        super().__init__(f"You are not allowed to do this action, the context is frozen. {a_message}")

class AlreadyLoggedInError(ReturnableError):
    """
    Raised if user is trying to login more than once at a time.
    """
    def __init__(self, a_message):
        super().__init__(f"You are already logged in")

class MultiUserError(ReturnableError):
    """
    Raised if user is trying to enter a context he can't because of multi-user.
    """
    def __init__(self, mode, prefix, users, other_mode):
        super().__init__(f"Multi user in {mode} is not supported for context {prefix}. Users: {users} are using {prefix} in {other_mode} mode.")

class DeprecatedWarningError(ReturnableError):
    def __init__(self, message):
        super().__init__(f"Deprecated context")

class NamePropertyDoesNotExistError(ReturnableError):
    def __init__(self, prop):
        super().__init__(f"The property(ies) {prop} none existing. Verify the spelling.")
        
class PropertyRangeNotMatchingTypeError(ReturnableError):
    def __init__(self, prop, range, type):
        super().__init__(f"The property {prop} has for range {range}, supplied was {type}.")
