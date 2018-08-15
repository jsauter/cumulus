class VpcConfig:
    def __init__(self, vpc_id, subnets):
        """
        :type subnets: List[basestring] or List[troposphere.Ref]
        :type vpc_id: str or troposphere.ImportValue
        """
        self._vpc_id = vpc_id
        self._subnets = subnets

    @property
    def vpc_id(self):
        return self._vpc_id

    @property
    def subnets(self):
        return self._subnets

    @vpc_id.setter
    def vpc_id(self, value):
        self._vpc_id = value

    @subnets.setter
    def subnets(self, value):
        self._subnets = value
