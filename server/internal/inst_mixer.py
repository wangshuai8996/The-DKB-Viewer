'''
Instance mixer, for mixed resolution for Concept and Instance
'''

from enum import Enum

class MixType(Enum):
    CONCEPT = 0
    INSTANCE = 1
    BOTH = 2  # Used when the upstream does not know the type and usually indicates that it needs an indication of the type

    def has_concept(self):
        return self != MixType.INSTANCE

    def has_instance(self):
        return self != MixType.CONCEPT

    def with_type_if_needed(self, *args):
        type = args[-1]
        args = args[:-1]
        if self == MixType.BOTH:
            return *args, type
        else:
            return args if len(args) > 1 else args[0]

