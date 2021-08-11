import functools

from datetime import datetime

from ..common.Exceptions import *
from . import setting
from .internal import (
        name_spec,
        pid as pid_util,
        )
from .internal.inst_mixer import MixType
from .Profile import *
from .MyContext import *
from .Concept import *
from .instance import Instance, InstanceBuilder
from .storage import Storage

from typing import Dict, Iterable, Tuple
from ..common.dkb_typing import PID
from dare_kb.common import format

from .internal.consts import context_state_list

class DareKB:

    list_of_concepts = {}
    username = None
    ontology_file = ""
    state = True
    _namespace = None

    def __require_open_dkb(f):
        '''
        Indicates and checks the function {f} requires a open DKB session
        '''
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            if (self.state == False):
                raise DKBclosedError(f.__name__)
            ret = f(self, *args, **kwargs)
            return ret
        return wrapper

    def __require_in_context(f):
        '''
        Indicates and checks the function {f} requires the session in a Context (i.e. _home is set)
        '''
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            if (self._home is None):
                raise NoContextSetError(f.__name__)
            ret = f(self, *args, **kwargs)
            return ret
        return wrapper
    
    def __require_writting(f):
        '''
        Indicates and checks the function {f} requires the 'W' option
        '''
        @functools.wraps(f)
        def wrapper(self, *args, **kwargs):
            if (self._home is not None and self._home.prefix != 'kb' and self._home.mode != 'W'):
                raise WritingPermissionDeniedError(f.__name__)
            ret = f(self, *args, **kwargs)
            return ret
        return wrapper


    def __init__(self, site_name=None, base_dir='', database_path=None, base_ontology_file=None):
        self._storage = Storage(self, base_dir, base_ontology_file, database_path)
        self._home = None  # home (default) context for the user
#        self.my_markers = 999
#        self.current_marker = 0
        self.site_identifier = site_name
        self.python_concepts = {} # TO BE USED
        self.python_contexts = {}

    def __del__(self):
        if self.state:
            self.shutdown()

    def shutdown(self):
        self.close()
        self._storage.shutdown()
        print("The DKB is now closed")

    def _add_default_context(self):  # TODO: replace with proper initialisation (through OWL file?)?
        '''
        Initialise a default Context (used when creating the DKB)
        '''
        c = self._new_context("kb", "knowledge base", [], "root")
        self._home = c
        self._home.activate_context()
        self._storage.update_state(self._home)

    def _restore_previous_context(self) -> None:
        self._home = self._storage.get_last_context()

    def open(self, session_id, username):  # TODO 10: Open a session. Session handle may be necessary?
        self.state = True
        self.session_id = session_id
        self.username = username

    def close(self):
        self.state = False
        if self._home is not None:
            self._storage.set_last_context(self._home)
        self._storage.flush()

    @__require_open_dkb
    def status(self):
        kb_status = {}
        kb_status["session_id"] = self.session_id
        kb_status["site_name"] = self.site_identifier
        kb_status["current_context"] = self._home.prefix
        kb_status["contexts_available"] = self._storage.context_list()
        kb_status["username"] = self.username
        return kb_status
    
    @__require_open_dkb
    def context_status(self, prefix=None):
        if prefix is not None:
            return self._storage.get_context(prefix).context_status()
        return self._home.context_status()

    def current_context(self):
        return self._home

    def _load_python_context_from_storage(self, c):
        newCkb = self._storage.get_context(c)
        self._cache_context(newCkb)

    def _context_loaded(self, prefix):
        return prefix in self.python_contexts

    @__require_open_dkb
    def new_context(self, prefix: str, title: str = None, search_path: List[str] = None, owner: str = None):

        #### Let's see if there an existing instance in the DKB that has the relevant prefix
        if self._storage.has_context(prefix):
            raise ExistingContextError(prefix, "new_context")

        if (owner is None):
            owner = self.username
        
        #### Verify the regex of the prefix and title
        if ((not name_spec.my_regex_for_identifiers(prefix)) or prefix == ""):
            raise IdentifierWrongError(prefix, "new_context")
#        if (title is not None):
#            if ((not name_spec.my_regex_for_title(title)) or title == ""):
#                raise IdentifierWrongError(title, "new_context")
        if title is None:
            title = "Context "+prefix+" for "+owner+" created in session: "+self.session_id+" at "+format.timestamp_serialise(datetime.now())
        if (search_path is None):
            ### check if we are in a context or not
            if (self._home is None):
                search_path = ['kb']
            else:
                search_path = [self._home.prefix]
        for c in search_path:
            if not self._storage.has_context(c):
                raise ContextNotFoundError(c, "new_context")
            else:
                if not self._context_loaded(c):
                    self._load_python_context_from_storage(c)
        c = self._new_context(prefix, title, search_path, owner)
        return c.prefix

    def _new_context(self, prefix: str, title: str, search_path: List[str], owner: str) -> MyContext:
        '''
        (Internal) Create the Context object (Python) and individual (OWL)
        '''

        c = MyContext(self, prefix, title, search_path, owner)
        self._storage.on_new_context(c)
        self._cache_context(c)
        return c

    def _cache_context(self, context: MyContext) -> None:
        '''
        Add the context to the state of DareKB object
        '''
        self.python_contexts[context.prefix] = context

    def get_context(self, prefix: str) -> MyContext:
        if prefix not in self.python_contexts:
            self._load_python_context_from_storage(prefix)
        return self.python_contexts[prefix]

    def resolve(self, eId, base=None, type=MixType.BOTH) -> Union[PID, Tuple[PID, str]]:
        '''
        This function implements the Entry search algorithm.
        Currently, only Concept exists (as subclass of Entry), so this function only looks for Concept.

        @param eId: The Entry ID
        @param base: Optional context (prefix) to start the resolve if eId does not have a prefix
        @param type: Optionally specify the type (Concept or Instance) to look up, represented using the MixType enum
        @return: The full PID of the found Entry if `type` is specified, or (PID, type)
        @throws ConceptNotFoundError: When the Concept can't be found and `type == MixType.CONCEPT`
        @throws InstanceNotFoundError: When the Instance can't be found and `type == MixType.INSTANCE` or `type == MixType.BOTH`
        '''
        def lookInContext(prefix, name):
            if type.has_concept():
                context = self.get_context(prefix)
                try:
                    pid = context.getConcept(name, followSearchPath=False).identifier
                    return type.with_type_if_needed(pid, MixType.CONCEPT)
                except ConceptNotFoundError:
                    if not type.has_instance():
                        raise ConceptNotFoundError(f'{prefix}::{name}', 'lookInContext')
            if type.has_instance():
                try:
                    pid = self._storage.get_instance(prefix, name).pid
                    return type.with_type_if_needed(pid, MixType.INSTANCE)
                except InstanceNotFoundError:
                    raise InstanceNotFoundError(f'{prefix}::{name}', 'lookInContext')

        if pid_util.isPID(eId):
            return self._storage.lookupPID(eId, type)
        parts, b = pid_util.isSpecificUpdate(eId)
        if b:
            return self._storage.lookupUpdate(*parts, type)
        parts, b = pid_util.isContextSpecified(eId)
        if b:
            return lookInContext(*parts)
        if base is None:
            base = self._home.prefix
        toDo = [base]
        visited = set()
        while toDo:
            pref, toDo = toDo[0], toDo[1:]
            if pref in visited:
                continue
            visited.add(pref)
            toDo += self.get_context(pref).get_search_path()
            try:
                return lookInContext(pref, eId)
            except ConceptNotFoundError:
                continue
        if eId == 'Concept':
            return type.with_type_if_needed(self._storage.id_for_root_concept(), MixType.CONCEPT)
        raise ConceptNotFoundError(eId, 'resolve')

    def id_for_root_concept(self) -> PID:
        return self._storage.id_for_root_concept()

    @__require_open_dkb
    @__require_in_context
    @__require_writting
    def newConcept(self, preciseTerm, specialisationOf = None, extra = dict(), mutability = "mutable", description = None, required = dict(), recommended = dict(), optional = dict(), translation = dict()) -> PID:

        c = self._home.newConcept(preciseTerm, specialisationOf, extra, mutability, description, required, recommended, optional, translation=translation)
        return c.identifier

    @__require_open_dkb
    def getConcept(self, identity, base=None) -> Concept:
        ### Careful here we don't look in the _ontology only in the current session

        pid = self.resolve(identity, base, type=MixType.CONCEPT)
        _, prefix, _, name = pid.split(':')
        context = self.get_context(prefix)
        concept = context.getConcept(name, followSearchPath=False)

        return concept

    @__require_open_dkb
    def get_search_path(self) -> List[str]:
        return self._home.get_search_path()


    @__require_open_dkb
    @__require_writting
    def set_search_path(self, new_search_path: List[str]):
        ### Let's look if the context in new_search_path exist
        for c in new_search_path:
            if not self._storage.has_context(c):
                raise ContextNotFoundError(c, "set_search_path")
            if (c not in self.python_contexts):
                self._load_python_context_from_storage(c)
        self._home.set_search_path(new_search_path)

    @__require_open_dkb
    def enter(self, a_prefix: str, rw: str) -> None:

        if (not isinstance(a_prefix, str)):
            raise TypeError("The specified context should be a String. Argument was of type ", type(a_prefix))
        if not self._storage.has_context(a_prefix):
            raise ContextNotFoundError(a_prefix, "enter")
        if (rw != 'R' and rw != 'W'):
            raise TypeError("Reading or writing option is not one the two following tokens 'R' or 'W'")

        ### Find the new context to enter
        if (a_prefix not in self.python_contexts):
            ### We add it to the python_context
            self._load_python_context_from_storage(a_prefix)

        if (self.python_contexts.get(a_prefix).state == context_state_list[2] and rw == 'W'):
            raise WritingPermissionDeniedError("This context is frozen, you are not permitted to enter for writting try enter(_,'R').")

        ## leave old
        if self._home is not None:
            self._home.leave_mode()
            self._storage.update_mode(self._home)

        ## re-enter
        self._home = self.python_contexts.get(a_prefix)
        self._home.activate_context()
        self._storage.set_last_context(self._home)
        self._home.enter_mode(rw)
        self._storage.update_mode(self._home)
        self._storage.update_state(self._home)
        print("Context is now set for "+self._home.title+" with prefix "+self._home.prefix)

    @__require_open_dkb
    def leave(self):
        self._storage.set_last_context(None)
        self._home.leave_mode()
        self._storage.update_mode(self._home)
        self._home = None
    

    @__require_open_dkb
    @__require_in_context
    @__require_writting
    def newInst(self, cls: str, name: str, **kwargs):
        prefix = self._home

        if self._storage.has_instance(prefix.prefix, name):
            raise NameInUseError(name, name, 'newInst')

        inst = InstanceBuilder(self,
                name = name,
                prefix = prefix,
                cls = cls,
                **kwargs,
                ).build()
        self._storage.on_new_instance(inst)
        return inst.pid

    @__require_open_dkb
    def getInstance(self, identity) -> Instance:  # TODO: extract common patterns with getConcept, and merge them
        pid = self.resolve(identity, type=MixType.INSTANCE)
        _, prefix, _, name = pid.split(':')

        inst = self._storage.get_instance(prefix, name)

        return inst

    @__require_open_dkb
    def get(self, identity):
        try:
            pid, type = self.resolve(identity)
            if type == MixType.CONCEPT:
                return self.getConcept(pid)
            else:
                return self.getInstance(pid)
        except InstanceNotFoundError:
            raise InstanceNotFoundError(identity, 'get')

    @__require_open_dkb
    def find(self, query):
        '''
        The find() function is described in the DKB Design document.
        The params `pid_only` and `only_these` are implemented in `sbridge`
        TODO: support Concept
        TODO: more terms
        TODO: other logic operators
        '''
        def filter_on_list(pattern, instance_list: List[Instance]):
            if pattern[0] == 'isa_exactly':
                concept_name = pattern[1]
                concept_pid = self.resolve(concept_name, type=MixType.CONCEPT)
                return (inst for inst in instance_list if inst.cls == concept_pid)
            elif pattern[0] == 'isa':
                concept_name = pattern[1]
                descendants = self._storage.descendant_concepts(self._home.prefix, concept_name)
                return (inst for inst in instance_list if inst.cls in descendants)
            elif pattern[0] == '==':
                attr, attribute_value = pattern[1:]
                proj = {
                        'pid': lambda inst: inst.pid,
                        'prefix': lambda inst: inst.prefix,
                        'name': lambda inst: inst.name,
                        'state': lambda inst: inst.state,
                        }
                selec = proj[attr] if attr in proj else lambda inst: inst.extras[attr]
                return (inst for inst in instance_list if selec(inst) == attribute_value)
            else:
                raise NotImplementedError(f"The find() function is not yet implemented for query pattern {pattern}")

        def on_section(query, instance_list: Iterable[Instance]):
            result = instance_list
            if query[0] == 'AND':
                for q in query[1:]:
                    result = on_section(q, result)
            else:
                result = filter_on_list(query, result)
            return result

        res = on_section(query, self._storage.instance_list())
        return res

    @__require_writting
    def reset_context(self, a_prefix: str = None) -> None:
        self._storage.del_context(self._home)
        self._storage.set_last_context(None)
        self._home = None

    @__require_writting
    def freeze_context(self, a_prefix:str = None) -> None:
        self._home.freeze()
        self._storage.update_state(self._home)
        self._storage.update_mode(self._home)
