
def isJustName(cname):
    if (len(cname.split(':')) == 1):
        return True
    return False

def isContextSpecified(cname):  # TODO 5: rename or create a dedicated PID class (and PartialPID)
    l = cname.split(':')
    if (len(l) == 2):
        return l, True
    return l, False

def isSpecificUpdate(cname):  # TODO 5: rename or create a dedicated PID class (and PartialPID)
    l = cname.split(':')
    if (len(l) == 3):
        return l, True
    return l, False

def isPID(cname):
    if (len(cname.split(':')) == 4):
        return True
    return False

class PartialPID:

    def __init__(self, identity):
        dkb_instance, context, version, name = [None] * 4
        seg = identity.split(':')
        if len(seg) == 4:
            dkb_instance, context, version, name = seg
        elif len(seg) == 3:
            context, version, name = seg
        elif len(seg) == 2:
            context, name = seg
        elif len(seg) == 1:
            name = seg[0]
        self.instance = dkb_instance
        self.context = context
        self.version = version
        self.name = name

