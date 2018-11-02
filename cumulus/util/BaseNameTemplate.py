
class BaseNameTemplate:

    def _throw_not_implemented(self, type_name):
        raise NotImplementedError('%s does not support naming type of %s' % (self.__class__.__name__, type_name))
