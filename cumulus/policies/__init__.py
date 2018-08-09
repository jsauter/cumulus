import awacs
import awacs.aws
import awacs.ec2

POLICY_VPC_CONFIG = awacs.aws.Statement(
    Effect=awacs.aws.Allow,
    Action=[
        awacs.ec2.DescribeSecurityGroups,
        awacs.ec2.DescribeSubnets,
        awacs.ec2.DescribeNetworkInterfaces,
        awacs.ec2.CreateNetworkInterface,
        awacs.ec2.DeleteNetworkInterface,
        awacs.ec2.DescribeDhcpOptions,
        awacs.ec2.DescribeVpcs,
        awacs.ec2.CreateNetworkInterfacePermission,
    ],
    Resource=['*'])
