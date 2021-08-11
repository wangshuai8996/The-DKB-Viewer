## This file contains all the functions necessary to the development and use of the DKB

import functools

from owlready2 import *
from .DareKB import *
from .Profile import *

import os.path
import uuid

from . import setting
from .internal import datatype as dt
from .internal import consts
from . import server_state as ss

from dare_kb.common import format

from typing import List, Optional
from ..common.dkb_typing import (
        PID,
        ConceptComm,
        )


###### Session manage
###### TODO 10: replace with fine-grained user & session manage
user = None
session = None

def _require_valid_session(session_id: str) -> None:
    global session
    if not session_id == session:
        raise DKBInvalidSessionException()

def require_session(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if args[0] != session:
            return
        return func(*args, **kwargs)
    return wrapper

class DKBCapacityExceededException(Exception):
    def __init__(self):
        super().__init__("DKB only allows one user login currently")

class DKBInvalidSessionException(Exception):
    def __init__(self):
        super().__init__("Current session is not a valid session")

###### End of session manage


def open_dkb(site_name: Optional[str]=None, base_dir: Optional[str]=None, database_path: Optional[str]=None, ontology_path: Optional[str]=None) -> DareKB:
    '''
    Function to open DKB.
    This function will be replaced with fine-grained server application (which has appropriate API calls)
    '''
    site_name = site_name or setting.site_name
    base_dir = base_dir or setting.base_dir
    myfilename = database_path or setting.database_path
    ontology_path = ontology_path or setting.ontology_path

    previous_dkb = DareKB(site_name, base_dir, database_path=myfilename, base_ontology_file=ontology_path)

    previous_dkb._restore_previous_context()


########### There should always be a context set unless you leave a specific concept. In that case, do we make a automatic enter into kb or something else?
###########
    if (previous_dkb.current_context() is None):
        print("DKB "+site_name+" has been retrieved and is connected under no context")
    else:
        print("DKB "+site_name+" has been retrieved and is connected under "+previous_dkb.current_context().title+" context/prefix="+previous_dkb.current_context().prefix)

    ### NEED TO FILL THE DKB WITH KNOWN CONTEXTS
    # previous_dkb._load_contexts()
    #print(ss.DKB._contexts)
    #print()
    #print()

    ss.DKB = previous_dkb
    ss.site_name = site_name

    return ss.DKB  # TODO 10: Used for tests. May not be necessary


def login(site_name: str, username: str, session_id: str = None) -> str:
    global user, session

    if ss.DKB:
        if site_name != ss.DKB.site_identifier: # Temporary "fix" for trying to login with a second site_name
            raise DKBnotFoundError(site_name, "login")

    if user and user != username:
        raise DKBCapacityExceededException()

    user = username
    if (session_id is not None):
        session = session_id
    else:
        session = str(uuid.uuid1())
    ss.DKB.open(session, user)

    return session

@require_session
def close(session_id: str) -> None:
    global user
    ss.DKB.close()
    user = None

@require_session
def enter(session_id: str, a_prefix: str, rw: str) -> None:
    ss.DKB.enter(a_prefix, rw)

@require_session
def leave(session_id) -> None:
    ss.DKB.leave()

@require_session
def get_search_path(session_id) -> List[str]:
    return ss.DKB.get_search_path()

@require_session
def set_search_path(session_id, new_search_path: List[str]) -> None:
    ss.DKB.set_search_path(new_search_path)

@require_session
def new_context(session_id, prefix, title=None, search_path=None, owner = None) -> str:
    return ss.DKB.new_context(prefix, title, search_path, owner)

@require_session
def context_reset(session_id, prefix=None) -> Dict:
    return ss.DKB.reset_context(prefix)

@require_session
def context_freeze(session_id, prefix=None) -> Dict:
    return ss.DKB.freeze_context(prefix)

@require_session
def status(session_id) -> Dict:
    return ss.DKB.status()

@require_session
def context_status(session_id, prefix=None) -> Dict:
    return ss.DKB.context_status(prefix)

@require_session
def newConcept(session_id, preciseTerm, specialisationOf = None, extra = dict(), mutability = "mutable", description = None, required = dict(), recommended = dict(), optional = dict(), translation = dict(), **kwargs) -> PID:
    return ss.DKB.newConcept(preciseTerm, specialisationOf, extra, mutability, description, required, recommended, optional, translation)

@require_session
def getConcept(session_id, identity, base=None) -> ConceptComm:
    concept = ss.DKB.getConcept(identity, base)

    return serialise_concept(concept)

def serialise_concept(concept):
    def handle_properties(key, properties):
        p_dict = {}
        if properties:
            for k, p in properties.items():
                if isinstance(p, MyObjectProperty):
                    p_dict[k] = p.range.identifier
                else:
                    p_dict[k] = dt.to_str(p.range)
        props[key] = p_dict

    props = {
            # "identity": concept.label,
            'name': concept.label,
            'prefix': concept.prefix,
            'pid': concept.identifier,
            'specialisationOf': concept.subClass,
            'instanceOf': ss.DKB.id_for_root_concept(),
            'description': concept.description,
            'state': concept.state,
            'timestamp': format.timestamp_serialise(concept.timestamp),
            'mutability': concept.mutability,
            'extra': concept.extra,
            'translation': concept.translation,
            }
    for p_type in consts.property_types:
        handle_properties(p_type, concept.get_properties(p_type=p_type, direct_only=False))

    return props

@require_session
def newInstance(session_id, cls: str, name: str, **kwargs):
    return ss.DKB.newInst(cls, name, **kwargs)


@require_session
def getInstance(session_id, identity):
    instance = ss.DKB.getInstance(identity)

    return serialise_instance(instance)

def serialise_instance(instance):
    props = {
            'name': instance.name,
            'prefix': instance.prefix,
            'instanceOf': instance.cls,
            'pid': instance.pid,
            'state': instance.state,
            'mutability': instance.mutability,
            'timestamp': format.timestamp_serialise(instance.timestamp),
            'extra': {k: v for k, v in instance.extras.items()},
            }

    return props


@require_session
def get(session_id, identity):
    entry = ss.DKB.get(identity)
    if isinstance(entry, Concept):
        return serialise_concept(entry)
    else:
        return serialise_instance(entry)

@require_session
def find(session_id, query, pid_only=False, only_these=None):
    instances = ss.DKB.find(query)
    if not pid_only or only_these:
        res = [serialise_instance(instance) for instance in instances]
        if only_these:
            res = [{k:v for k, v in r.items() if k in only_these} for r in res]
    else:  # == elif pid_only:
        res = [instance.pid for instance in instances]
    return res
