class VpcConfig:
    def __init__(self, vpc_id, subnets):
        """
        :type subnets: List[basestring] or List[troposphere.Ref]
        :type vpc_id: str or troposphere.ImportValue
        """
        self.vpc_id = vpc_id
        self.subnets = subnets

    @property
    def vpc_id(self):
        return self.vpc_id

    @property
    def subnets(self):
        return self.subnets
