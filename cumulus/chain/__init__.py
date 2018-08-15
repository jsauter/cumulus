import abc


class Handler:
    """
    Interface for handling the chain

    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, successor=None, template=None):
        """
        Accepts a successor to chain calls to.
        The template should only be sent in on the first item in the chain.
        After that, the template is extracted out of the successor for convenience.

        :param successor:
        :param template:
        """
        self._successor = successor
        if template:
            self.template = template
        elif successor:
            if not successor.template:
                raise ValueError("Expected successor to have a template but didn't")
            self.template = successor.template
        else:
            raise ValueError("successor or the template was not set.")

    @abc.abstractmethod
    def handle(self):
        """
        Must override this.
        To continue the chain, call self._successor.next()
        To stop the chain, don't call that.
        Always call the super constructor when overriding.
            super(ChildClass, self).__init__(args)
        :param template:
        :return:
        """
        pass

    def next(self, template):
        if self._successor:
            self._successor.handle(template=template)
