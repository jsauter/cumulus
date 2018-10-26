from troposphere import Ref, iam

from cumulus.chain import step


class InstanceProfilePolicy(step.Step):

    def __init__(self,
                 name,
                 ec2_role_name,
                 policy):
        step.Step.__init__(self)
        self.name = name
        self.ec2_role_name = ec2_role_name
        self.policy = policy

    def handle(self, chain_context):
        template = chain_context.template

        template.add_resource(iam.PolicyType(
            "%sPolicy" % self.name,
            PolicyName=self.name,
            PolicyDocument=self.policy,
            Roles=[Ref(self.ec2_role_name)],
        ))
