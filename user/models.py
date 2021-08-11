from django.db import models
import datetime
# import logging
# logger = logging.getLogger('django')

# define the data models of the SQL database and the DKB elements


class User(models.Model):
    name = models.CharField(max_length=30, null=False)
    password = models.CharField(max_length=30)
    email = models.EmailField()

    def __str__(self):
        return self.name


class State(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    page = models.CharField(max_length=30)
    user_name = models.CharField(max_length=30, null=False)
    save_time = models.DateField(auto_now=True)
    data = models.JSONField()
    link = models.JSONField()

    def __str__(self):
        return str(self.id)


# no use
class Common(models.Model):
    id = models.AutoField(primary_key=True)
    save_time = models.DateField(auto_now=True)
    data = models.JSONField()
    link = models.JSONField()


class Context:
    def __init__(self, name, pid, search_path, concepts, instances, mode, users, owner, state, title):
        self.name = name
        self.pid = pid
        self.id = pid
        self.search_path = search_path
        self.concepts = concepts
        self.instances = instances
        self.mode = mode
        self.users = users
        self.owner = owner
        self.state = state
        self.title = title
        self.category = 0
        self.store = 0
        self.symbolSize = 30
        self.is_hide = False
        self.is_expand = False
        self.is_mark = False
        self.color = '#D2E9FF'

    def get_info(self):
        info = "name: " + self.name + "<br>" + "pid: " + self.pid + "<br>" + "mode: " + self.mode + "<br>" +\
               "state: " + self.state + "<br>" + "owner: " + self.owner + "<br>" + "users: " + ','.join(self.users) +\
               "<br>" + "title: " + self.title
        return info


class Concept:
    def __init__(self, name, pid, description, mutability, state, timestamp, translation, specialise, attributes,
                 context):
        self.name = name
        self.pid = pid
        self.id = pid
        self.description = description
        self.mutability = mutability
        self.state = state
        self.timestamp = timestamp
        self.translation = translation
        self.specialise = specialise #数组
        self.attributes = attributes
        self.context = context
        self.instances = []
        self.category = 1
        self.store = 1
        self.symbolSize = 60
        self.is_hide = False
        self.is_expand = False
        self.is_mark = False
        self.color = '#D2E9FF'

    def get_info(self):
        time = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        info = "name: " + self.name + "<br>" + "pid: " + self.pid + "<br>" + "prefix: " + self.context + "<br>" + \
               "mutability: " + self.mutability + "<br>" + "specialises: " + ''.join(self.specialise) + "<br>" +\
               "state: " + self.state + "<br>" + "translation: " + str(self.translation) + "<br>" +\
               "description: " + self.description + "<br>" + "timestamp: " + time
        return info

    def add_instance(self, instance):
        self.instances.append(instance)

    def get_attributes(self):
        attrs = {}
        for attribute in self.attributes:
            attrs[attribute.key] = attribute.value
        return attrs


class Instance:
    def __init__(self, name, pid, context, concept, mutability, state):
        self.name = name
        self.pid = pid
        self.id = pid
        self.attributes = []
        self.context = context
        self.concept = concept
        self.mutability = mutability
        self.state = state
        self.category = 2
        self.store = 2
        self.symbolSize = 45
        self.is_hide = False
        self.is_expand = False
        self.is_mark = False
        self.color = '#D2E9FF'

    def get_attributes(self):
        attrs = {}
        for attribute in self.attributes:
            attrs[attribute.key] = attribute.value
        return attrs


class Attribute:
    def __init__(self, key, value, attribute_of):
        self.key = key
        self.value = value
        self.attribute_of = attribute_of
        # self.type = type #instance concept
        self.id = attribute_of + ":" + key
        self.name = key
        self.category = -1 #默认不显示
        self.color = '#D2E9FF'
        self.symbolSize = 30
        self.store = 3
        # type包括：
        #     recommended
        #     optional
        #     required


class Relation:
    def __init__(self, source, target, relationship):
        self.source = source
        self.target = target
        self.relationship = relationship

    def get_link(self):
        return {"source": self.source, "target": self.target, "lineStyle": {"type": self.relationship}}
    # relation的类型：
        # search_path 0 dashed
        # 继承 1 dotted
        # 包含 2 solid
