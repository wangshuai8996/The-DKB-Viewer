'''
The entry point for client-side / user-side DKB library.
The bridges replaces DKB_functions.py file

This is temporarily a file, but will be moved to a module.
'''

from . import csbridge as br
from .csbridge import DKBAPIUserHandle

from .decorator import delegate

from typing import (
        List,
        )
from .common.dkb_typing import (
        PID,
        )

def new_dkb(site_name: str, reset: bool = False, profile = None) -> None:
    br.new_dkb(site_name, reset, profile)

def login(site_name, username, session_id=None, **infos) -> 'DKBService':
    return DKBService(br.login_obj(site_name, username, session_id, raw_data=False, **infos))


@delegate('_user_handle', 'close', 'get_search_path', 'set_search_path', 'enter', 'leave', 'new_context', 'new_concept', 'new_instance', 'status', 'context_status', 'context_reset', 'context_deprecate', 'context_freeze', 'new_user')
class DKBService:

    def __init__(self, user_handle: DKBAPIUserHandle):
        self._user_handle = user_handle

    def get(self, identity, only_these=None, ignore_discarded=False):
        return self._user_handle.get(identity, only_these, ignore_discarded)

    def find(self, query, pid_only=True, only_these=None, ignore_discarded=False):
        res = self._user_handle.find(query, pid_only, only_these, ignore_discarded)  # TODO: convert to Instance or Concept helper class?
        return res
        
    def update(self, name, **other):
        res = self._user_handle.update(name, **other)
        return res


@delegate('concept_props', '__len__', '__getitem__', '__setitem__', '__delitem__', '__missing__', '__iter__', '__repr__')
class DKBConcept:

    def __init__(self, concept_props):
        self.concept_props = concept_props

