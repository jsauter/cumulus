from awacs.aws import Allow, Principal, Policy, Statement
from awacs.sts import AssumeRole
from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import EC2VPCId, EC2SubnetIdList, CFNCommaDelimitedList, CFNString, CFNNumber, \
    EC2KeyPairKeyName
from troposphere import cloudformation, ec2, iam, Ref
from troposphere.iam import Role
from cumulus.chain import chain, chaincontext
from cumulus.steps.ec2 import scaling_group, launch_config, block_device_data, ingress_rule, target_group, dns, alb
from cumulus.steps.ec2.instance_profile_role import InstanceProfileRole


class Alb(Blueprint):
    VARIABLES = {
        'VpcId': {'type': EC2VPCId, 'description': 'Vpc Id'},
        'PrivateSubnets': {
            'type': EC2SubnetIdList,
            'description': 'Subnets to deploy private '
                           'instances in.'},
        'AvailabilityZones': {'type': CFNCommaDelimitedList,
                              'description': 'Availability Zones to deploy '
                                             'instances in.'},
        'InstanceType': {'type': CFNString,
                         'description': 'EC2 Instance Type',
                         'default': 't2.micro'},
        'MinSize': {'type': CFNNumber,
                    'description': 'Minimum # of instances.',
                    'default': '1'},
        'MaxSize': {'type': CFNNumber,
                    'description': 'Maximum # of instances.',
                    'default': '5'},
        'ALBHostName': {
            'type': CFNString,
            'description': 'A hostname to give to the ALB. If not given '
                           'no ALB will be created.',
            'default': ''},
        'ALBCertName': {
            'type': CFNString,
            'description': 'The SSL certificate name to use on the ALB.',
            'default': ''},
        'ALBCertType': {
            'type': CFNString,
            'description': 'The SSL certificate type to use on the ALB.',
            'default': 'acm'},
    }

    def create_template(self):

        instance_profile_name = "InstanceProfile" + self.name

        t = self.template
        t.add_description("Acceptance Tests for cumulus scaling groups")

        instance = self.context.environment['namespace'] + self.context.environment['env']

        the_chain = chain.Chain()


        the_chain.add(alb.Alb(
        ))

        chain_context = chaincontext.ChainContext(
            template=t,
            instance_name=instance
        )

        the_chain.run(chain_context)
