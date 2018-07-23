import abc


class Handler:
    """
    Define an interface for handling requests.
    Implement the successor link.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, successor=None, template=None):
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
        Usage:  Handle the chain.
                You must make a call to super() at the top of your handle() method when implementing handle()
                Currently there is no logic to exit the chain early except with an exception.
        :return:
        """
        self.next()

    def next(self):
        # self.print_template(template)
        # print(template.__dict__)

        if self._successor:
            self._successor.handle()
