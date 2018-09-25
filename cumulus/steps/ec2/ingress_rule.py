import re

from troposphere import (
    ec2)

from cumulus.chain import step
from cumulus.steps.ec2 import META_SECURITY_GROUP_REF


class IngressRule(step.Step):

    def __init__(self,
                 port_to_open,
                 cidr):

        step.Step.__init__(self)

        self.port_to_open = port_to_open
        self.cidr = cidr

    def handle(self, chain_context):
        template = chain_context.template

        clean_cidr = re.compile('[\W_]+').sub('', self.cidr)

        template.add_resource(ec2.SecurityGroupIngress(
            "Cidr%sToASGPort%s" % (clean_cidr, self.port_to_open),
            IpProtocol="tcp",
            FromPort=self.port_to_open,
            ToPort=self.port_to_open,
            CidrIp=self.cidr,
            GroupId=chain_context.metadata[META_SECURITY_GROUP_REF]
        ))
