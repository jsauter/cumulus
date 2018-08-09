class ChainContext:

    def __init__(self,
                 template,
                 instance_name,
                 ):
        """

        :type template: troposphere.Template
        """
        self._instance_name = instance_name
        self._template = template
        self._metadata = {}

    @property
    def template(self):
        return self._template

    @property
    def metadata(self):
        """
        Steps can write data here to be used later in the chain.
        Example: Code development initial step might create an s3 bucket
                 Subsequent steps might want to reference this.
                 It could be a string, or even a troposphere Ref object.
        :return:
        """
        return self._metadata

    @property
    def instance_name(self):
        # TODO: validate instance name for s3 compatibility (cuz it could be used there)
        return self._instance_name
