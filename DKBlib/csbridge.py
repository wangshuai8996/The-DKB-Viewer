#!/usr/bin/env python3
# -*- coding:utf-8 -*-


'''
This file specifies the bridge between the Client and the Server.
The bridge is intended to mimic the server API call from the client, to decouple the code, for future separation into API calls.
'''

import requests
import json
import warnings

from datetime import datetime

from .common.client_exception import IdentifierWrongError
from .common.cs_exception import handle_server_exception, DKBException
from .common import format

from .setting import get_site

from typing import (
        Dict,
        List,
        Optional,
        Union,
        )
#from dare_kb.common.dkb_typing import (
from common.dkb_typing import (
        PID,
        ConceptComm,
        )


def _expect_server_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DKBException as e:
            e.coerce()
    return wrapper

_reqm = {
        'GET': requests.get,
        'POST': requests.post,
        'PUT': requests.put,
        'DELETE': requests.delete,
        }
def _do_request(site: str, method: str, path: str, parse_json=False, **data: dict) -> str:
    server = get_site(site)
    if method == 'GET':
        r = _reqm[method](server + path, params=data)
    else:
        headers = {'Content-Type': 'application/json'}
        r = _reqm[method](server + path, headers=headers, data=json.dumps(data))
    msg = r.text
    if parse_json:
        if 'Content-Type' in r.headers and r.headers['Content-Type'] == 'application/json':
            msg = json.loads(r.text)
    if not r.ok:
        msg = r.text
        if 'Content-Type' in r.headers and r.headers['Content-Type'] == 'application/json':
            msg = json.loads(r.text)
        handle_server_exception(r.status_code, msg)
    return msg


@_expect_server_exception
def new_dkb(site_name: str, reset: bool = False, profile = None) -> None:
    _do_request('POST', '/admin/install', site_name=site_name, reset=reset)

@_expect_server_exception
def login(site_name, username, session_id = None, **infos) -> str:
    res = _do_request(site_name, 'POST', '/user/login', site_name=site_name, username=username, session=session_id, **infos)
    return res

@_expect_server_exception
def close(site: str, session_id: str) -> None:
    _do_request(site, 'POST', '/user/logout', session=session_id)

@_expect_server_exception
def enter(site: str, session_id, a_prefix, rw) -> str:
    ret = _do_request(site, 'POST', '/user/current_context', session=session_id, prefix=a_prefix, rw=rw)
    return ret

@_expect_server_exception
def leave(site: str, session_id) -> None:
    _do_request(site, 'DELETE', '/user/current_context', session=session_id)

@_expect_server_exception
def get_search_path(site: str, session_id) -> List[str]:
    res = _do_request(site, 'GET', '/user/search_path', parse_json=True, session=session_id).strip()
    return res.split('\n') if res else []

@_expect_server_exception
def set_search_path(site: str, session_id, new_search_path: Union[str,List[str]]) -> None:
    if not isinstance(new_search_path, list):
        new_search_path = [new_search_path]
    _do_request(site, 'POST', '/user/search_path', session=session_id, search_path=new_search_path)

@_expect_server_exception
def new_context(site: str, session_id, prefix, title=None, search_path=None, owner = None) -> str:
    if not prefix: # Server would return 404, so we hijack thi in advance
        raise IdentifierWrongError('A context must have a non-empty prefix')
    res = _do_request(site, 'POST', '/context/'+prefix, parse_json=True, session=session_id, title=title, search_path=search_path, owner=owner)
    return res
    
@_expect_server_exception
def new_user(site: str, session_id, username, prefer_context, credentials, email) -> str:
    res = _do_request(site, 'POST', '/user/'+username, parse_json=True, session=session_id, prefer_context=prefer_context, credentials=credentials, email=email)
    return res

@_expect_server_exception
def context_reset(site: str, session_id, prefix = None) -> None:
    _do_request(site, 'DELETE', '/context/reset/', session=session_id, prefix=prefix)
    
@_expect_server_exception
def context_deprecate(site: str, session_id, prefix = None) -> None:
    _do_request(site, 'DELETE', '/context/deprecated/', session=session_id, prefix=prefix)

@_expect_server_exception
def context_freeze(site: str, session_id, prefix = None) -> None:
    _do_request(site, 'DELETE', '/context/freeze/', session=session_id, prefix=prefix)

@_expect_server_exception
def status(site: str, session_id) -> Dict:
    res = _do_request(site, 'GET', '/user/status', session=session_id)
    return json.loads(res)

@_expect_server_exception
def context_status(site: str, session_id, prefix = None) -> Dict:
    res = _do_request(site, 'GET', '/context/status/', session=session_id, prefix=prefix)
    return json.loads(res)

@_expect_server_exception
def new_concept(site: str, session_id, precise_term, specialises = None, mutability = "mutable", required = dict(), recommended = dict(), optional = dict(), translation = dict(), description = None, methods = dict(), py_class = None) -> PID:
    res = _do_request(site, 'POST', '/concept/'+precise_term, parse_json=True, session=session_id, specialises=specialises, mutability=mutability, required=required, recommended=recommended, optional=optional, translation=translation, description=description, methods=methods, py_class=py_class)
    return res

@_expect_server_exception
def new_instance(site: str, session_id, cls, name, **extra) -> PID:
    extra['class'] = cls  # Writing this because we can't write `class=cls` (syntax error)
    res = _do_request(site, 'POST', '/instance/'+name, parse_json=True, session=session_id, **extra)
    return res

@_expect_server_exception
def get(site: str, session_id, identity, only_these, ignore_discarded):
    if (only_these == []):
        only_these = '__empty__'
    res = _do_request(site, 'GET', '/entry/'+identity, session=session_id, only_these=only_these, ignore_discarded=ignore_discarded)
    return json.loads(res)

@_expect_server_exception
def find(site: str, session_id, query, pid_only, only_these, ignore_discarded):
    if (only_these == []):
        only_these = '__empty__'
    res = _do_request(site, 'POST', '/entry', session=session_id, query=query, pid_only=pid_only, only_these=only_these, ignore_discarded=ignore_discarded)
    return json.loads(res)

@_expect_server_exception
def update(site: str, session_id, identity, **extra) -> PID:
    res = _do_request(site, 'POST', '/update/'+identity, parse_json=True, session=session_id, **extra)
    return res

def login_obj(site_name, username, session_id=None, raw_data=True, **infos) -> 'DKBAPIUserHandle':
    return DKBAPIUserHandle(site_name, login(site_name, username, session_id, **infos), raw_data=raw_data)


# TODO: For all the `XXXHandle`: change to separate classes and function calls

class DKBAPIHandle:

    def __init__(self, site: str, session_id: str, raw_data=True):
        self.site = site
        self.session_id = session_id
        self.raw_data = raw_data

    def close(self):
        close(self.site, self.session_id)


# TODO
# class DKBAdminHandle(DKBHandle):

#     def deprecate(self) -> None:
#         self._server_kb.deprecate()


class DKBAPIUserHandle(DKBAPIHandle):

    def get_search_path(self) -> List[str]:
        return get_search_path(self.site, self.session_id)

    def set_search_path(self, new_search_path: Union[str,List[str]]) -> None:
        set_search_path(self.site, self.session_id, new_search_path)

    def enter(self, a_prefix, rw) -> None:
        mess = enter(self.site, self.session_id, a_prefix, rw)
        if mess != '':
            warnings.warn(mess, DeprecationWarning)

    def leave(self) -> None:
        leave(self.site, self.session_id)

    def context_reset(self, a_prefix = None) -> None:
        context_reset(self.site, self.session_id, a_prefix)
        
    def context_deprecate(self, a_prefix = None) -> None:
        context_deprecate(self.site, self.session_id, a_prefix)

    def context_freeze(self, a_prefix = None) -> None:
        context_freeze(self.site, self.session_id, a_prefix)

    def new_context(self, prefix, title=None, search_path=None, owner = None) -> str:
        return new_context(self.site, self.session_id, prefix, title, search_path, owner)
    
    def new_user(self, username, prefer_context, credentials, email = None) -> str:
        return new_user(self.site, self.session_id, username, prefer_context, credentials, email)

    def new_concept(self, precise_term, **kwargs) -> PID:
        return new_concept(self.site, self.session_id, precise_term, **kwargs)

    def new_instance(self, cls, name, **extra) -> PID:
        return new_instance(self.site, self.session_id, cls, name, **extra)
    
    def update(self, identity, **extra) -> PID:
        return update(self.site, self.session_id, identity, **extra)

    def get(self, identity, only_these, ignore_discarded):
        ret = get(self.site, self.session_id, identity, only_these, ignore_discarded)
        if not self.raw_data:
            if ('timestamp' in ret.keys()):
                ret['timestamp'] = format.timestamp_deserialise(ret['timestamp'])
        return ret

    def status(self):
        return status(self.site, self.session_id)
    
    def context_status(self, a_prefix=None):
        return context_status(self.site, self.session_id, a_prefix)

    def find(self, query, pid_only, only_these, ignore_discarded):
        ret = find(self.site, self.session_id, query, pid_only, only_these, ignore_discarded)
        if not self.raw_data:
            for i in ret:
                if isinstance(i, dict) and ('timestamp' in i.keys()):
                    i['timestamp'] = format.timestamp_deserialise(i['timestamp'])
        return ret
