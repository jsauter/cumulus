from cumulus.chain import Handler


class Resource(Handler):
    """
    Adds any resource to the template using the chain.
    """

    def __init__(self, resource, successor=None, template=None):
        super(Resource, self).__init__(successor, template)
        self.resource = resource

    def handle(self):
        super(Resource, self).handle()

        self.template.add_resource(self.resource)
