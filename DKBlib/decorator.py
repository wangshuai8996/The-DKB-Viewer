'''
This file contains delegators to be used across the project.
'''

def delegate(to, *methods):
    '''
    Obtained from https://stackoverflow.com/a/55563139
    '''
    def dec(klass):
        def create_delegator(method):
            def delegator(self, *args, **kwargs):
                obj = getattr(self, to)
                m = getattr(obj, method)
                return m(*args, **kwargs)
            return delegator
        for m in methods:
            setattr(klass, m, create_delegator(m))
        return klass
    return dec

