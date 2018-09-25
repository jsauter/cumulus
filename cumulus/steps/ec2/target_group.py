from troposphere import elasticloadbalancingv2 as alb

from cumulus.chain import step
from cumulus.steps.ec2 import META_TARGET_GROUP_NAME


class TargetGroup(step.Step):

    def __init__(self,
                 port,
                 vpc_id
                 ):

        step.Step.__init__(self)

        self.port = port
        self.vpc_id = vpc_id

    def handle(self, chain_context):

        # todo: why is this not allowing a reference?

        name = '%sTargetGroup' % chain_context.instance_name

        chain_context.metadata[META_TARGET_GROUP_NAME] = name
        template = chain_context.template

        template.add_resource(alb.TargetGroup(
            name,
            HealthCheckPath="/",
            HealthCheckIntervalSeconds="30",
            HealthCheckProtocol="HTTP",
            HealthCheckTimeoutSeconds="10",
            HealthyThresholdCount="4",
            Matcher=alb.Matcher(HttpCode="200"),
            Port=self.port,
            Protocol="HTTP",
            UnhealthyThresholdCount="3",
            VpcId=self.vpc_id
        ))
