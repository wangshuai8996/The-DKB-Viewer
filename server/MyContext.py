from .Concept import Concept
from .internal import (
        name_spec,
        pid as pid_util,
        )
from .internal.consts import context_state_list
from ..common import Exceptions as E

from typing import List, Optional
from ..common.dkb_typing import PID

class MyContext:

    readers = []
    writers = []
    mode = None
    history = [] ### all 3 attributes are not used yet

    def __init__(self, dkb, prefix, title, search_path, owner, identifier=None, lastMarker=0):
        self._dkb = dkb  # TODO: not very elegant, may need to be replaced with other ways (e.g. passing parameters every time?)

        self.title = title
        self.prefix = prefix
        self.identifier = identifier or self._dkb.site_identifier + ":" + self.prefix
        self.search_path = search_path
        self.usePath = False
        self.lastMarker = lastMarker
        self.owner = owner
        self.user = []
        self.state = context_state_list[0]
        self.changes = {}

        self.list_of_concepts = {}  # Python object of the Concepts in current Context

    def enter_mode(self, mode):
        self.mode = mode
    
    def leave_mode(self):
        self.mode = None
    
    def concepts_info(self) -> List:
        return self._dkb._storage.get_concepts_for_context(self.prefix)
    
    def instances_info(self) -> List:
        return self._dkb._storage.get_instances_for_context(self.prefix)

    def _load_concept_from_storage(self, identifier) -> None:
        '''
        Load the concept from backend data storage into a python Concept object, and cache it
        '''
        concept = self._dkb._storage.get_concept(self.prefix, identifier)
        concept.populate_inherited_properties(self)
        self.list_of_concepts[identifier] = concept

    def activate_context(self):
        if (self.state == context_state_list[0] or self.state == None):
            self.state = context_state_list[1]

    def nextMarker(self):
        self.lastMarker += 1
        self._dkb._storage.update_last_marker(self.prefix, self.lastMarker)
        return self.lastMarker

    def get_search_path(self):
        return self.search_path

    def set_search_path(self, new_search_path):
        self.search_path = new_search_path
        self._dkb._storage.update_search_path(self.prefix, new_search_path)

    def _has_concept(self, preciseTerm) -> bool:
        return self._dkb._storage.has_concept(self.prefix, preciseTerm)

    def newConcept(self, preciseTerm, specialisationOf = None, extra = dict(), mutability = "mutable", description = None, required = dict(), recommended = dict(), optional = dict(), translation = dict()) -> PID:

        ### First test if name comply and if already a Concept for this preciseTerm:
        if (not name_spec.my_regex_for_concept_name(preciseTerm) or preciseTerm == ""):
            raise E.IdentifierWrongError(preciseTerm, "newConcept")

        ## test if concept exists in given context
        # if so error Context exist
        # if not look if exist in search_path context with the status no-hiding
        if self._has_concept(preciseTerm):
            raise E.NameInUseError(preciseTerm, self.getConcept(preciseTerm), "newConcept")
        # else:  ## FIXME: why does this branch exist? Shouldn't we create it directly?
        #     ### search all concepts
        #     my_label = '*' + preciseTerm
        #     res = self._ontology.search(iri = my_label)
        #     for c in res:
        #         ## check if c is in search_path
# #                if (c.concept_prefix in (list(self._home.search_path.keys))):
        #         if (c.concept_mutability is not None and (c.concept_mutability == "no-hiding")):
        #             raise NameInUseError(preciseTerm, c, "newConcept")

        ### From this, either it is new or being redefined : No distinction is made at this stage

        ## check the different other attributes now
        ### specialisationOf is name of a Concept (str) or the identifier
        ## it is stored as a str of the identifier in any case
        if specialisationOf is None:
            specialisationOf = self._dkb._storage.id_for_root_concept()
        spe_python = self.getConcept(specialisationOf, followSearchPath=True)
        spe = spe_python.identifier

        if (description is None):
            desc = ""
        else:
            desc = description
        c = Concept(self, preciseTerm, spe, desc, mutability, required, recommended, optional)
        self.nextMarker()

        c.populate_inherited_properties(self)

        self._dkb._storage.on_new_concept(c)
        self.list_of_concepts[preciseTerm] = c
        return c

    def getConcept(self, identity, followSearchPath=True) -> Concept:  # TODO 6: add version
        if identity == 'Concept':
            return self._dkb._storage.get_concept(self.prefix, identity)
        identity = pid_util.PartialPID(identity).name  # FIXME: what if identity is in a different Context (caused by, e.g., Concept.populate_inherited_properties()). Probably the proper fix is to keep a Context function as only a cache, and move all query/get to DareKB
        if not self._has_concept(identity):
            if followSearchPath:
                return self._dkb.getConcept(identity, self.prefix)
            else:
                raise E.ConceptNotFoundError(identity, 'getConcept')
        if identity not in self.list_of_concepts:
            self._load_concept_from_storage(identity)
        return self.list_of_concepts[identity]


    def context_status(self):
        cx_status = {}
        cx_status["title"] = self.title
        cx_status["prefix"] = self.prefix
        cx_status["identifier"] = self.identifier
        cx_status["search_path"] = self.search_path
        cx_status["owner"] = self.owner
        cx_status["mode"] = self.mode
        cx_status["state"] = self.state
        cx_status["concepts"] = self.concepts_info()
        cx_status["instances"] = self.instances_info()
        return cx_status

    def reset(self):
        l = self._dkb._storage.concept_list(self.prefix)
        for c in l.values():
            self._dkb._storage.del_entity(c)

    def freeze(self):
        self.state = context_state_list[2]
        self.mode = 'R'


