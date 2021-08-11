from datetime import datetime

from .internal import pid as pid_util
from .internal.inst_mixer import MixType

class Instance:
    def __init__(self, name: str, prefix: str, pid: str, cls: str, state: str, mutability: str, timestamp: datetime, **kwargs):
        self.name = name  # name represented as a string
        self.prefix = prefix  # prefix (context name) represented as a string
        self.pid = pid  # full pid represented as a string
        self.cls = cls  # class; the pid of the class (a Concept) that this Instance is
        self.state = state
        self.mutability = mutability
        self.timestamp = timestamp
        self.extras = kwargs  ## TODO: make use of extras, when for OWL

    def __str__(self):
        return f'Instance {self.pid} ({self.name}) of {self.cls} in {self.prefix} (created: {self.timestamp})'


class InstanceBuilder:

    def __init__(self, dkb = None, **kwargs):
        self.dkb = dkb
        def init(*names):
            for name in names:
                if name in kwargs:
                    setattr(self, name, kwargs[name])
        init('name', 'cls', 'pid', 'prefix', 'state', 'timestamp', 'mutability', 'extras')

    def _g(self, var):
        if hasattr(self, var):
            return getattr(self, var)
        return None

    def build(self) -> Instance:
        cls = self.cls if pid_util.isPID(self.cls) else self.dkb.resolve(self.cls, type=MixType.CONCEPT)
        name = self.name
        prefix = self.prefix
        if not isinstance(prefix, str):
            context = prefix
            prefix = context.prefix
        else:
            context = self.dkb.get_context(prefix)
        pid = self._g('pid') or "{}:{}:{}".format(context.identifier, context.lastMarker, name)
        state = self._g('state') or 'new'
        mutability = self._g('mutability') or 'mutable'
        timestamp = self._g('timestamp') or datetime.now()
        extras = self._g('extras') or {}
        return Instance(name, prefix, pid, cls, state, mutability, timestamp, **extras)

