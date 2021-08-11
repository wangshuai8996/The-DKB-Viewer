'''
The storage backend for DareKB.
It handles the data(-base) storage.
'''
from owlready2 import *
from owlready2 import issubclass_owlready
from owlready2.class_construct import Restriction
from owlready2 import owl

import json
from pathlib import Path

from ..common.Exceptions import ConceptNotFoundError, ContextNotFoundError, InstanceNotFoundError

from .internal.inst_mixer import MixType
from . import setting

from .MyContext import MyContext
from .Concept import Concept
from .instance import Instance, InstanceBuilder
from .property import MyDataProperty, MyObjectProperty

from typing import List, Optional, Tuple, Union, Dict
from ..common.dkb_typing import PID

import logging
logger = logging.getLogger('Storage')
logger.setLevel(logging.DEBUG)

class Storage:

    def __init__(self, dkb, base_dir=None, base_ontology_file=None, world_db_filename=None):
        base_dir = base_dir or setting.base_dir
        base_ontology_file = str(Path(base_dir) / (base_ontology_file or setting.ontology_path))
        world_db_filename = str(Path(base_dir) / (world_db_filename or setting.database_path))
        logger.info(f"base_dir: {base_dir}; ontology_file: {base_ontology_file}; database_path: {world_db_filename}")
        self._dkb = dkb
        self._base_dir = base_dir
        self._my_world = World(filename = world_db_filename)
        self._ontology = self._my_world.get_ontology(base_ontology_file).load()
        self.namespace_label = "http://www.semanticweb.org/ryey/ontologies/2020/5/untitled-ontology-36"
        self._namespace = self._ontology.get_namespace(self.namespace_label)
        self._contexts = {}
        self._load_contexts()
        self._state = True

    def _load_contexts(self) -> None:
        for i in self._namespace.Context.instances():
            self._contexts[i.prefix] = i

    def __del__(self):
        if self._state:
            try:
                self.shutdown()
            except Exception:
                pass

    def shutdown(self):
        self._state = False
        self.flush()
        self._my_world.close()

    def flush(self):
        # self._ontology.save("test.owl")
        self._ontology.save(str(Path(self._base_dir) / "dkb.owl"))
        self._my_world.save()

    def _normalise_name(self, name: str) -> str:
        return name.replace(':', '__')

    def _get_owl_entry_by_pid(self, pid: str):
        res_concept = self._ontology.search(class_pid = pid)
        if res_concept:
            assert len(res_concept) == 1
            return res_concept[0]
        res_instance = self._ontology.search(pid = pid)
        if res_instance:
            assert len(res_instance) == 1
            return res_instance[0]
        raise InstanceNotFoundError()

    def _instantiate_python_context(self, acontext) -> MyContext:
        '''
        @param acontext: a context object from ontology
        '''
        context = MyContext(self._dkb, acontext.prefix, acontext.title, [sp.prefix for sp in acontext.search_path], acontext.owner, identifier=acontext.identifier, lastMarker=int(acontext.lastMarker))
        context.my_context = acontext
        context.state = acontext.state
        context.mode = acontext.mode
        return context

    def _cache_context(self, context: MyContext, owl_context) -> None:
        self._contexts[context.prefix] = owl_context

    def has_context(self, prefix: str) -> bool:
        return prefix in self._contexts

    def get_context(self, prefix: str) -> MyContext:
        def create_python_context_given_prefix(c):
            owl_c = self._contexts[c]
            newCkb = self._instantiate_python_context(owl_c)
            return newCkb
        if not self.has_context(prefix):
            raise ContextNotFoundError(prefix, 'get_context')
        return create_python_context_given_prefix(prefix)

    def context_list(self) -> List:
        return list(self._contexts.keys())

    #TODO: rename to new_context()?
    def on_new_context(self, c: MyContext) -> None:
        '''
        Create the Context individual (OWL)
        '''
        def create_owl_context(c):
            my_context = self._namespace.Context(self._normalise_name(c.identifier))
            my_context.prefix = c.prefix
            my_context.title = c.title
            my_context.lastMarker = str(c.lastMarker)
            my_context.owner = c.owner
            my_context.identifier = c.identifier
            my_context.state = c.state
            my_context.mode = c.mode
            my_context.search_path = [self._contexts[sp] for sp in c.search_path]
            return my_context

        owl_context = create_owl_context(c)
        self._cache_context(c, owl_context)

    def update_search_path(self, context: str, search_path: List[str]) -> None:
        owl_context = self._contexts[context]
        owl_context.context_search_path = [self._contexts[sp] for sp in search_path]

    def update_last_marker(self, context: Union[str,MyContext], marker: int) -> None:
        if isinstance(context, MyContext):
            context = context.prefix
        self._contexts[context].context_lastMarker = str(marker)

    def lookupPID(self, pid, type=MixType.BOTH) -> Union[PID, Tuple[PID, MixType]]:
        '''
        Checks if the given PID exists
        '''
        if type.has_concept():
            if pid == self._namespace.Concept.class_pid[0]:  # TODO 9: this is a hack. See lookupPID().
                return type.with_type_if_needed(pid, MixType.CONCEPT)
            # This function can't find the right PID, because PID is not the same as class/entity id in the ontology -- PID is in the concept_identifier property. This way of storing information is unlikely right. Consulting Amelie is needed.
            my_label = "*" + pid
            res = self._ontology.search(class_pid = my_label)
            if (res != []):
                assert len(res) == 1
                return type.with_type_if_needed(res[0].class_pid[0], MixType.CONCEPT)
            else:
                if not type.has_instance():
                    raise ConceptNotFoundError(pid, 'lookupPID')
        if type.has_instance():
            res = self._ontology.search(pid = pid)
            if (res != []):
                assert len(res) == 1
                return type.with_type_if_needed(res[0].pid, MixType.INSTANCE)
            else:
                raise InstanceNotFoundError(pid, 'lookupPID')
        raise RuntimeError("IllegalAccess: type must fall into either Concept or Instance")

    def lookupUpdate(self, c, marker, name, type=MixType.BOTH) -> Union[PID, Tuple[PID, MixType]]:
        my_label = "*:" + c + ":" + marker + ":" + name
        if type.has_concept():
            res = self._ontology.search(class_pid = my_label)
            if (res != []):
                return type.with_type_if_needed(res[0].class_pid[0], MixType.CONCEPT)
            raise ConceptNotFoundError(pid, 'lookupUpdate')
        if type.has_instance():
            res = self._ontology.search(pid = my_label)
            if (res != []):
                return type.with_type_if_needed(res[0].pid[0], MixType.INSTANCE)
            raise ConceptNotFoundError(pid, 'lookupUpdate')
        raise RuntimeError("IllegalAccess: type must fall into either Concept or Instance")

    def id_for_root_concept(self) -> PID:
        return self._namespace.Concept.class_pid[0]
    def owlRootConcept(self):
        return self._namespace.Concept

    def concept_list(self, prefix) -> Dict:
        _concepts_current_context = {}
        c = self._namespace.Concept
        res = self._ontology.search(is_a = c)
        for c in res:
            if c.class_prefix and c.class_prefix[0] == prefix:
                _concepts_current_context[c.class_name[0]] = c
        return _concepts_current_context

    def has_concept(self, prefix, name) -> bool:
        return name in self.concept_list(prefix)

    def get_concept(self, prefix, name) -> Concept:
        '''
        Strictly finds Concept (name) in Context (prefix) without looking up the search path
        '''
        if name == 'Concept':  # TODO: this is likely a hack. Needs further checks
            owl_concept = self.owlRootConcept()
            subclass = None
        else:
            try:
                owl_concept = self.concept_list(prefix)[name]
            except KeyError:
                raise ConceptNotFoundError(name, 'get_concept')
            subclass = owl_concept.is_a[0]
            assert self.owlRootConcept() in subclass.ancestors(), f"{name} is not a regular Concept as its super class is not its first type. {owl_concept.is_a}"  # TODO: Improve the retrieval of super Concept
            if subclass == self.owlRootConcept():
                subclass = None
            else:
                subclass = subclass.class_pid

        required = {}
        recommended = {}
        optional = {}

        # Only the direct constraints are retrieved here. Indirect ones are dealt with in MyContext
        with self._ontology as onto:
            for sup in onto.get_parents_of(owl_concept):
                if isinstance(sup, Restriction):
                    if issubclass_owlready(sup.property, onto.dkb_data_property):
                        p_name = sup.property.name
                        p_range = sup.value
                    elif issubclass_owlready(sup.property, onto.dkb_object_property):
                        p_name = sup.property.name
                        p_range = sup.value.pid
                    else:
                        continue  # Unknown. Probably other subclass-of restrictions, so we ignore them.
                    if sup.type == 26: # exactly
                        required[p_name] = p_range
                    elif sup.type == 28: # max
                        optional[p_name] = p_range
                        # FIXME: optional and recommended both uses `max 1`. They are differentiated by the annotation, but getting the annotation will trigger a bug. Needs upstream fix or suggestions: http://owlready.8326.n8.nabble.com/Annotaion-on-subclassOf-constraint-not-correctly-get-td1931.html

        translation = owl_concept.class_translation
        if translation:
            translation = json.loads(translation[0])
        else:
            translation = {}
        concept = Concept(owl_concept.class_prefix[0], owl_concept.class_name[0], subclass, owl_concept.class_description[0], owl_concept.class_mutability[0],
                required = required,
                recommended = recommended,
                optional = optional,
                identifier = owl_concept.class_pid[0],
                timestamp = owl_concept.class_timestamp,
                translation = translation)
        concept.my_concept = owl_concept
        return concept

    def on_new_concept(self, c: Concept) -> None:
        def create_owl_concept_basic(c):
            with self._namespace:
                _, p_prefix, _, p_name = self._dkb.resolve(c.subClass, type=MixType.CONCEPT).split(':')
                paren_concept = self.get_concept(p_prefix, p_name)
                my_concept = types.new_class(self._normalise_name(c.identifier), (paren_concept.my_concept,))
                # my_concept = types.new_class(c.identifier, (c.subClass,))
                my_concept.class_description=c.description
                paren = self._dkb.getConcept(c.subClass, c.prefix)
                my_concept.is_a=[paren.my_concept]
                my_concept.class_pid=c.identifier
                my_concept.class_name=c.label
                my_concept.class_prefix=c.prefix
                my_concept.class_mutability=c.mutability
                my_concept.class_timestamp = c.timestamp
                my_concept.class_translation = json.dumps(c.translation)
                return my_concept
    #            print("Taille dic in write "+str(len(c.dataProperties)))
        def create_owl_object_property(dp, owl_concept):
            with self._namespace:
                my_property = types.new_class(dp.name, (self._namespace.dkb_object_property, FunctionalProperty))
                my_property.domain.append(owl_concept)
                my_property.range =[dp.range.my_concept]

                my_property.comment = [dp.type]
                if dp.type == 'required':
                    c.my_concept.is_a.append(my_property.exactly(1, dp.range.my_concept))
                else:
                    c.my_concept.is_a.append(my_property.max(1, dp.range.my_concept))

                return my_property
        def create_owl_data_property(dp, owl_concept):
            with self._namespace:
                my_property = types.new_class(dp.name, (self._namespace.dkb_data_property, FunctionalProperty))
                my_property.domain.append(owl_concept)
                my_property.range = [dp.range]

                my_property.comment = [dp.type]
                if dp.type == 'required':
                    c.my_concept.is_a.append(my_property.exactly(1, dp.range))
                else:
                    c.my_concept.is_a.append(my_property.max(1, dp.range))

                return my_property

        my_concept = create_owl_concept_basic(c)
        c.my_concept = my_concept
        for dp in c.dataProperties.values():
            my_property = create_owl_data_property(dp, my_concept)
            dp.my_property = my_property
        for dp in c.objectProperties.values():
            my_property = create_owl_object_property(dp, my_concept)
            dp.my_property = my_property

    def ancestor_concepts(self, prefix: str, concept: str) -> List[PID]:
        concept = self.get_concept(prefix, concept)
        owl_concept = concept.my_concept
        return [ancestor.class_pid for ancestor in owl_concept.ancestors() & self.owlRootConcept().descendants()]

    def descendant_concepts(self, prefix: str, concept: str) -> List[PID]:
        concept = self.get_concept(prefix, concept)
        owl_concept = concept.my_concept
        return [descendant.class_pid[0] for descendant in owl_concept.descendants()]

    # Instance
    def has_instance(self, prefix: str, name: str):
        res = self._ontology.search(pid = f'*:{prefix}:*:{name}')
        if not res:
            return False
        return True

    def _instantiate_python_instance(self, owl_inst):
        '''
        Converts a OWL Instance to Python Instance
        '''
        cls = owl_inst.is_a[0] # TODO: better implementation
        o_dp = self._namespace.dkb_data_property
        o_op = self._namespace.dkb_object_property
        properties = {}
        for p in owl_inst.get_properties():
            if issubclass_owlready(p, o_dp):
                p_name = p.name
                dp = owl_inst.__getattr__(p_name)
                properties[p_name] = dp
            # elif o_op in p.is_a:
            elif issubclass_owlready(p, o_op):
                p_name = p.name
                op = owl_inst.__getattr__(p_name)
                properties[p_name] = op.pid  # TODO: Python representation of the object (Instance?)
        instance = Instance(owl_inst.name_dkb, owl_inst.prefix, owl_inst.pid, cls.class_pid[0], owl_inst.state, owl_inst.mutability, owl_inst.timestamp, **properties) #, extras)
        instance.my_instance = owl_inst
        return instance

    def get_instance(self, prefix: str, name: str):
        res = self._ontology.search(pid = f'*:{prefix}:*:{name}')
        if not res:
            raise InstanceNotFoundError(f'{prefix}::{name}', 'get_instance')
        owl_inst = res[0]
        return self._instantiate_python_instance(owl_inst)

    def on_new_instance(self, instance: Instance):
        def create_owl_instance(ins):
            with self._namespace as ns:
                owl_instance = self._get_owl_entry_by_pid(ins.cls)()
                owl_instance.name_dkb = ins.name
                owl_instance.prefix = ins.prefix
                owl_instance.pid = ins.pid
                owl_instance.state = ins.state
                owl_instance.mutability = ins.mutability
                owl_instance.timestamp = ins.timestamp
                for k, v in ins.extras.items():
                    owl_k = ns[k]  # FIXME: what if name conflict
                    if not owl_k:  # If the property doesn't exist (not owl_k), ignore it. TODO: Improve this behaviour
                        continue
                    if not v:  # If the value is null (`v == None`, thus `not v`), do not store it because owlready doesn't allow to store a null value. This behaviour is needed for future update (e.g. circular dependencies), so it should be no harm
                        continue
                    if issubclass_owlready(owl_k, owl.ObjectProperty):
                        owl_obj = self._get_owl_entry_by_pid(v)  # v is the PID of the Instance
                        owl_instance.__setattr__(k, owl_obj)
                    else:  # It is a data property
                        owl_instance.__setattr__(k, v)
                return owl_instance
        owl_instance = create_owl_instance(instance)
        instance.my_instance = owl_instance

    def instance_list(self):
        concepts = set(self.owlRootConcept().descendants())
        individuals = []
        for individual in self._ontology.individuals():
            if set(individual.is_a) & concepts:
                individuals.append(individual)
        return [self._instantiate_python_instance(individual) for individual in individuals]

    ### System information

    def set_last_context(self, context: Optional[Union[str,MyContext]]) -> None:
        if isinstance(context, MyContext):
            context = context.prefix
        map(lambda ctx: ctx.dkb_context_lastset == 0,
                filter(lambda ctx: ctx.dkb_context_lastset == 1,
                    self._contexts.values()))
        ## Equivalent to
        # for ctx in self._contexts.values():
        #     if ctx.context_lastset == 1:
        #         ctx.context_lastset = 0
        if context:
            self._contexts[context].dkb_context_lastset = 1

    def get_last_context(self) -> Optional[MyContext]:
        for i in self._namespace.Context.instances():
            if (i.dkb_context_lastset == 1):
                c = self._instantiate_python_context(i)
                self._cache_context(c, i)
                return c
        return None

    def update_state(self, a_context):
        self._contexts[a_context.prefix].state = a_context.state

    def update_mode(self, a_context):
        self._contexts[a_context.prefix].mode = a_context.mode


    def get_instances_for_context(self, a_context: str) -> Dict:
        _instances = {}
        res = self._ontology.search(prefix = a_context)
        for i in res:
            if (i.name_dkb):
                _instances[i.name_dkb] = i.pid
        return _instances

    def get_concepts_for_context(self, a_context: str) -> Dict:
        _concepts = {}
        res = self._ontology.search(class_prefix = a_context)
        for i in res:
            _concepts[i.class_name[0]] = i.class_pid[0]
        return _concepts

    def del_entity(self, pid):
        destroy_entity(pid)

    def del_context(self, a_context):
        pid = self._contexts.get(a_context.prefix)
        destroy_entity(pid)
        del self._contexts[a_context.prefix]
