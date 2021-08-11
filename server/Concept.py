from datetime import datetime

from .Class import *
from . import setting
from .internal import (
        datatype as dt,
        name_spec,
        )
from .internal.consts import property_types
from .property import MyDataProperty, MyObjectProperty

from ..common import Exceptions as E

from typing import Union


class Concept(Class):

    def __init__(self, context: Union[str, 'MyContext'], name, subClass, description, mutab, required={}, recommended={}, optional={}, translation={}, identifier=None, timestamp: datetime=None, **extra):
        self.label = name
        self.subClass = subClass
        try:
            self.prefix = context.prefix
        except AttributeError:
            self.prefix = context
        self.description = description
        self.identifier = identifier or context.identifier + ":" + str(context.lastMarker) + ":" + self.label
        self.mutability = mutab
        self.state = "new"
        self.timestamp = timestamp or datetime.now()
        self.extra = extra

        # Properties
        ## For faster lookup when creating owl Concept
        self.objectProperties = {} ## dictionnary of the new properties between Object
        self.dataProperties = {} ## dictionnary of the new properties linked to data

        ## All properties used during runtime lookup
        self.properties = {
                'direct': {
                    'required': self._handle_properties(context, required, 'required'),
                    'recommended': self._handle_properties(context, recommended, 'recommended'),
                    'optional': self._handle_properties(context, optional, 'optional'),
                    },
                'indirect': {
                    'required': {},
                    'recommended': {},
                    'optional': {},
                    }
                }

        self.translation = translation
        self.allInstances = {}  # TODO

    def __str__(self):
        return f'Concept {self.identifier} ({self.label} (subclass-of {self.subClass})) in {self.prefix}'

    def populate_inherited_properties(self, context):
        if self.subClass:  # Just in case. This shouldn't matter, because only `Concept` and top-level Concepts has `self.subClass == None`
            parent = context.getConcept(self.subClass)
            self.properties['indirect'] = {
                    'required': parent.get_properties('required', direct_only=False),
                    'recommended': parent.get_properties('recommended', direct_only=False),
                    'optional': parent.get_properties('optional', direct_only=False),
                    }


    ## subClass is specialization of a Concept : concept in Python class so Right now could not be a concept from owl

    def newIdentifier(self):
## construct an identifier of the form : cp + id ?
        pass

    def get_properties(self, p_type=property_types, direct_only=True):
        if not isinstance(p_type, set):
            p_type = {p_type}

        res = {}
        for pt in property_types:
            if pt in p_type:
                res.update(self.properties['direct'][pt])
        if not direct_only:
            for pt in property_types:
                if pt in p_type:
                    res.update(self.properties['indirect'][pt])
        return res


    # def addDataProperty(self, k, prop):
    #     self.dataProperties[k] = prop

    # def addObjectProperty(self, k, prop):
    #     self.objectProperties[k] = prop

    def _handle_property(self, context, name, p_range, p_type):
        if (not name_spec.myRegexForPropertyName(name) or name == ""):
            raise E.IdentifierWrongError(name, "Properties")
        if dt.has_str(p_range):
            dp = MyDataProperty(name, self, dt.from_str(p_range), True, p_type)
            self.dataProperties[name] = dp
        else: ### it is then a concept
            if (p_range == self.label):
                dp = MyObjectProperty(name, self, self, True, p_type)
            else:
                try:
                    concept = context.getConcept(p_range)
                    dp = MyObjectProperty(name, self, concept, True, p_type)
                except E.ConceptNotFoundError:
                    raise E.NotAConceptError(name, "newConcept")
            self.objectProperties[name] = dp
        return dp

    def _handle_properties(self, context, dic, ptype):
        properties = {}
        for name, p_range in dic.items():
            if isinstance(p_range, MyDataProperty):
                dp = p_range
                self.dataProperties[name] = dp
            elif isinstance(p_range, MyObjectProperty):
                dp = p_range
                self.objectProperties[name] = dp
            else:
                dp = self._handle_property(context, name, p_range, ptype)
            properties[name] = dp
        return properties

    def newInstance(self):
        pass

    def toString(self):
        return self.label

    # FIXME: Not used? What's the purpose of this function?
    def retrieveMyOwlProperties(self):
        from . import server_state as ss
        graph = ss.DKB._my_world.as_rdflib_graph()
        graph.bind("dkb", setting.graph_bind_link)
        graph.bind("w3", "http://www.w3.org/2000/01/rdf-schema#")
        print(self.label)
        my_query = """
            SELECT * WHERE {?x w3:subPropertyOf dkb:"""+ self.identifier +"""_property}
            """
        print(my_query)
        r = list(graph.query_owlready(my_query))
        for r1 in r:
            print(r1)
