from troposphere import (
    Ref, ec2)

from cumulus.chain import step
from cumulus.steps.ec2 import META_SECURITY_GROUP_REF


class AlbPort(step.Step):

    def __init__(self,
                 port_to_open,
                 alb_sg_name):

        step.Step.__init__(self)

        self.port_to_open = port_to_open
        self.alb_sg_name = alb_sg_name

    def handle(self, chain_context):
        template = chain_context.template

        name = '%sElbToASGPort%s' % (chain_context.instance_name, self.port_to_open)

        template.add_resource(ec2.SecurityGroupIngress(
            name,
            IpProtocol="tcp",
            FromPort=self.port_to_open,
            ToPort=self.port_to_open,
            SourceSecurityGroupId=Ref(self.alb_sg_name),
            GroupId=chain_context.metadata[META_SECURITY_GROUP_REF]
        ))
