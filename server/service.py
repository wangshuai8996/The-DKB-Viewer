#!/usr/bin/env python3
# -*- coding:utf-8 -*-

'''
The server application for DareKB.
See also __main__.py
'''

from flask import Flask, request, abort
from flask_restful import reqparse, abort, Api, Resource
import json

from ..common.cs_exception import try_propagate as try_pr
from . import sbridge as sbr

app = Flask(__name__)
api = Api(app)


@app.route('/')
def index():
    return 'DareKB Server'

@app.route('/user/login', methods=['POST'])
def login():
    site_name = request.json['site_name']
    username = request.json['username']
    session_id = request.json.get('session_id', None)
    try:
        return sbr.login(site_name, username, session_id)
    except Exception as e:
        return try_pr(e)

@app.route('/user/logout', methods=['POST'])
def logout():
    session_id = request.json['session']
    username = request.json.get('username', '')
    sbr.close(session_id)
    return ''

@app.route('/user/current_context', methods=['POST', 'PUT', 'DELETE'])
def current_context():
    try:
        session_id = request.json['session']
        if request.method in {'POST', 'PUT'}:
            prefix = request.json['prefix']
            rw = request.json['rw']
            sbr.enter(session_id, prefix, rw)
            return ''
        if request.method == 'DELETE':
            sbr.leave(session_id)
            return ''
    except Exception as e:
        return try_pr(e)

@app.route('/user/search_path', methods=['GET', 'POST', 'PUT'])
def search_path():
    try:
        if request.method == 'GET':
            session_id = request.args['session']
            return '\n'.join(sbr.get_search_path(session_id))
        elif request.method in {'POST', 'PUT'}:
            session_id = request.json['session']
            new_search_path = request.json['search_path']
            sbr.set_search_path(session_id, new_search_path)
            return ''
    except Exception as e:
        return try_pr(e)

@app.route('/user/status')
def status():
    try:
        session_id = request.args['session']
        return sbr.status(session_id)
    except Exception as e:
        return try_pr(e)

@app.route('/context/status/', methods=['GET'])
def context_status():
    try:
        session_id = request.args['session']
        if (request.args.get('prefix')):
            prefix = request.args['prefix']
        else:
            prefix = None
        return sbr.context_status(session_id, prefix)
    except Exception as e:
        return try_pr(e)

@app.route('/context/reset/', methods=['DELETE'])
def context_reset():
    try:
        session_id = request.json['session']
        if (request.args.get('prefix')):
            prefix = request.args['prefix']
        else:
            prefix = None
        sbr.context_reset(session_id, prefix)
        return ''
    except Exception as e:
        return try_pr(e)

@app.route('/context/freeze/', methods=['DELETE'])
def context_freeze():
    try:
        session_id = request.json['session']
        if (request.args.get('prefix')):
            prefix = request.args['prefix']
        else:
            prefix = None
        sbr.context_freeze(session_id, prefix)
        return ''
    except Exception as e:
        return try_pr(e)

@app.route('/context/<prefix>', methods=['POST'])
def context(prefix: str):
    session_id = request.json['session']
    title = request.json.get('title', None)
    search_path = request.json.get('search_path', None)
    owner = request.json.get('owner', None)
    try:
        return sbr.new_context(session_id, prefix, title, search_path, owner)
    except Exception as e:
        return try_pr(e)

@app.route('/entry/<identity>', methods=['GET'])
def entry(identity: str):
    session_id = request.args['session']
    try:
        return sbr.get(session_id, identity)
    except Exception as e:
        return try_pr(e)

@app.route('/entry', methods=['POST'])
def find():
    session_id = request.json['session']
    query = request.json['query']
    pid_only = request.json.get('pid_only', False)
    only_these = request.json.get('only_these', None)
    try:
        return json.dumps(sbr.find(session_id, query, pid_only, only_these))
    except Exception as e:
        return try_pr(e)


class Concept(Resource):
    def get(self, identity):
        try:
            session_id = request.args['session']
            base = request.args.get('base', None)
            return sbr.getConcept(session_id, identity, base)
        except Exception as e:
            return try_pr(e)

    def post(self, identity):
        try:
            session_id = request.json['session']
            preciseTerm = identity
            return sbr.newConcept(session_id, preciseTerm, **request.json)
        except Exception as e:
            return try_pr(e)


class Instance(Resource):
    def get(self, identity):
        try:
            session_id = request.args['session']
            return sbr.getInstance(session_id, identity)
        except Exception as e:
            return try_pr(e)

    def post(self, identity):
        try:
            session_id = request.json['session']
            cls = request.json['class']
            name = identity
            extra_args = {k: request.json[k] for k in request.json if k not in {'session', 'class'}}
            return sbr.newInstance(session_id, cls, name, **extra_args)
        except Exception as e:
            return try_pr(e)


api.add_resource(Concept, '/concept/<identity>')
api.add_resource(Instance, '/instance/<identity>')


@app.before_first_request
def setup():
    sbr.open_dkb()

def run(*args, **kwargs):
    import argparse
    from . import setting
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default='5000')
    parser.add_argument('-d', '--directory', default=setting.base_dir)
    parser.add_argument('site_name', nargs='?', default=setting.site_name)
    parser.add_argument('database_path', nargs='?', default=setting.database_path)
    parser.add_argument('ontology_path', nargs='?', default=setting.ontology_path)
    cargs = parser.parse_args()
    setting.base_dir = cargs.directory
    setting.site_name = cargs.site_name
    setting.database_path = cargs.database_path
    setting.ontology_path = cargs.ontology_path
    app.run(*args, debug=cargs.debug, host=cargs.host, port=cargs.port, **kwargs)
