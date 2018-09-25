from awacs.aws import Allow, Principal, Policy, Statement
from awacs.sts import AssumeRole
from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import EC2SubnetIdList, CFNCommaDelimitedList, CFNString, CFNNumber, \
    EC2KeyPairKeyName
from troposphere import cloudformation, ec2, iam, Ref

from cumulus.chain import chain, chaincontext
from cumulus.steps.ec2 import scaling_group, launch_config, block_device_data, ingress_rule, target_group, dns, \
    alb_port, listener_rule
from cumulus.steps.ec2.instance_profile_role import InstanceProfileRole


class WebsiteSimple(Blueprint):
    VARIABLES = {
        'namespace': {
            'type': CFNString
        },
        'env': {
            'type': CFNString
        },
        'IAlbListener': {
            'type': CFNString,
            'description': 'From the ALB',
        },
        'AlbCanonicalHostedZoneID': {
            'type': CFNString,
            'description': 'From the ALB',
            'default': 'acm',
        },
        'AlbDNSName': {
            'type': CFNString,
            'description': 'From the ALB',
            'default': 'acm',
        },
        'AlbSg': {
            'type': CFNString,
            'description': 'From the ALB',
        },
        'InstanceType': {'type': CFNString,
                         'description': 'EC2 Instance Type',
                         'default': 't2.micro'},
        'SshKeyName': {'type': EC2KeyPairKeyName},
        'ImageName': {
            'type': CFNString,
            'description': 'The image name to use from the AMIMap (usually '
                           'found in the config file.)'},
        'BaseDomain': {
            'type': CFNString},
        'MinSize': {'type': CFNNumber,
                    'description': 'Minimum # of instances.',
                    'default': '1'},
        'MaxSize': {'type': CFNNumber,
                    'description': 'Maximum # of instances.',
                    'default': '5'},
        'PrivateSubnets': {'type': EC2SubnetIdList,
                           'description': 'Subnets to deploy private '
                                          'instances in.'},
        'AvailabilityZones': {'type': CFNCommaDelimitedList,
                              'description': 'Availability Zones to deploy '
                                             'instances in.'},
        'VpcId': {'type': CFNString,
                  'description': 'Vpc Id'},
    }

    def get_metadata(self):
        metadata = cloudformation.Metadata(
            cloudformation.Init(
                cloudformation.InitConfigSets(
                    default=['install_and_run']
                ),
                install_and_run=cloudformation.InitConfig(
                    commands={
                        '01-startup': {
                            'command': 'nohup python -m SimpleHTTPServer 8000 &'
                        },
                    }
                )
            )
        )
        return metadata

    def create_template(self):
        t = self.template
        t.add_description("Acceptance Tests for cumulus scaling groups")

        # TODO fix
        # instance = self.name + self.context.environment['env']
        # TODO: give to builder
        the_chain = chain.Chain()

        application_port = "8000"

        instance_profile_name = "InstanceProfile" + self.name

        the_chain.add(InstanceProfileRole(
            instance_profile_name=instance_profile_name,
            role=iam.Role(
                "SomeRoleName1",
                AssumeRolePolicyDocument=Policy(
                    Statement=[
                        Statement(
                            Effect=Allow,
                            Action=[AssumeRole],
                            Principal=Principal("Service", ["ec2.amazonaws.com", "s3.amazonaws.com"])
                        )
                    ]
                ),
            )))

        the_chain.add(launch_config.LaunchConfig(meta_data=self.get_metadata(),
                                                 vpc_id=Ref("VpcId")))

        the_chain.add(block_device_data.BlockDeviceData(ec2.BlockDeviceMapping(
            DeviceName="/dev/xvda",
            Ebs=ec2.EBSBlockDevice(
                VolumeSize="40"
            ))))

        the_chain.add(target_group.TargetGroup(
            port=application_port,
            vpc_id=Ref("VpcId")
        ))

        the_chain.add(scaling_group.ScalingGroup(
        ))

        the_chain.add(ingress_rule.IngressRule(
            port_to_open="22",
            cidr="10.0.0.0/8"
        ))

        the_chain.add(ingress_rule.IngressRule(
            port_to_open=application_port,
            cidr="10.0.0.0/8"
        ))

        the_chain.add(dns.Dns(
            base_domain=Ref("BaseDomain"),
            hosted_zone_id=Ref("AlbCanonicalHostedZoneID"),
            dns_name=Ref("AlbDNSName"),
        ))

        the_chain.add(alb_port.AlbPort(
            port_to_open=application_port,
            alb_sg_name="AlbSg",
        ))

        the_chain.add(listener_rule.ListenerRule(
            base_domain_name=Ref("BaseDomain"),
            alb_listener_rule=Ref("IAlbListener"),
            path_pattern="/*",
            priority="2"
        ))

        chain_context = chaincontext.ChainContext(
            template=t,
            instance_name=instance_profile_name
        )

        the_chain.run(chain_context)
