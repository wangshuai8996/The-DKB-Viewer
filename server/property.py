
class Property:
    ## class for defining properties
    pass


class MyDataProperty(Property):

    def __init__(self, name, domain, range, isfunctional, type):
        self.name = name
        self.domain = domain
        self.range = range
        self.type = type
        self.isfunctional = isfunctional


class MyObjectProperty(Property):

    def __init__(self, name, domain, range, isfunctional, type):
        self.name = name
        self.domain = domain
        self.range = range
        self.type = type
        self.isfunctional = isfunctional
