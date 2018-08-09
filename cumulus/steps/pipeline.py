import awacs
import troposphere

# from awacs import aws, sts, s3, logs, ec2, iam
import awacs.iam
import awacs.aws
import awacs.sts
import awacs.s3
import awacs.logs
import awacs.ec2
import awacs.iam

from cumulus.chain import step
from cumulus.util.tropo import TemplateQuery

from troposphere import codepipeline, Ref, iam, codebuild, ec2
from troposphere import logs as log_resource
from troposphere.s3 import Bucket, VersioningConfiguration

META_PIPELINE_BUCKET_REF = 'pipeline-bucket-Ref'
META_PIPELINE_BUCKET_POLICY_REF = 'pipeline-bucket-policy-Ref'

META_LAST_STAGE_OUTPUT = 'last_pipeline_stage'


class Pipeline(step.Step):

    def __init__(self, name, bucket_name):
        step.Step.__init__(self)
        self.name = name
        self.bucket_name = bucket_name

    def handle(self, chain_context):
        # TODO: validate for artifact store location
        # TODO: add pipeline service role

        # TODO: optionally inject
        pipeline_bucket = Bucket(
            "pipelinebucket%s" % chain_context.instance_name,
            BucketName=self.bucket_name,
            VersioningConfiguration=VersioningConfiguration(
                Status="Enabled"
            )
        )

        pipeline_bucket_access_policy = iam.ManagedPolicy(
            "PipelineBucketAccessPolicy",
            Path='/managed/',
            PolicyDocument=awacs.aws.PolicyDocument(
                Version="2012-10-17",
                Id="bucket-access-policy%s" % chain_context.instance_name,
                Statement=[
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.s3.ListBucket,
                            awacs.s3.GetBucketVersioning,
                            # awacs.aws.Action("s3", "*"),
                        ],
                        Resource=[
                            # awacs.s3.ARN(pipeline_bucket),
                            troposphere.Join('', [
                                awacs.s3.ARN(),
                                Ref(pipeline_bucket),
                            ]),
                        ],
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.s3.HeadBucket,
                        ],
                        Resource=[
                            '*'
                        ]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.s3.GetObject,
                            awacs.s3.GetObjectVersion,
                            awacs.s3.PutObject,
                            awacs.s3.ListObjects,
                            awacs.s3.ListBucketMultipartUploads,
                            awacs.s3.AbortMultipartUpload,
                            awacs.s3.ListMultipartUploadParts,
                            awacs.aws.Action("s3", "Get*"),
                        ],
                        Resource=[
                            troposphere.Join('', [
                                awacs.s3.ARN(),
                                Ref(pipeline_bucket),
                                '/*'
                            ]),
                        ],
                    )
                ]
            )
        )

        chain_context.template.add_resource(pipeline_bucket_access_policy)
        # pipeline_bucket could be a string or Join object.. unit test this.
        chain_context.metadata[META_PIPELINE_BUCKET_REF] = Ref(pipeline_bucket)
        chain_context.metadata[META_PIPELINE_BUCKET_POLICY_REF] = Ref(pipeline_bucket_access_policy)

        pipeline_policy = iam.Policy(
            PolicyName="%sPolicy" % self.name,
            PolicyDocument=awacs.aws.PolicyDocument(
                Version="2012-10-17",
                Id="PipelinePolicy",
                Statement=[
                    awacs.aws.Statement(
                        Sid="1",
                        Effect=awacs.aws.Allow,
                        # Principal=awacs.aws.Principal("AWS", [awacs.aws.IAM_ARN(user, '', account)]),
                        Action=[awacs.aws.Action("s3", "*")],
                        Resource=[
                            # awacs.s3.ARN(pipeline_bucket),
                            awacs.s3.ARN('*'),  # TODO: inject
                        ],
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.aws.Action("cloudformation", "*"),
                            awacs.aws.Action("codebuild", "*"),
                        ],
                        # TODO: restrict more accurately
                        Resource=["*"]
                    )
                ],
            )
        )

        pipeline_service_role = iam.Role(
            "PipelineServiceRole",
            Path="/",
            RoleName="PipelineRole%s" % chain_context.instance_name,
            AssumeRolePolicyDocument=awacs.aws.Policy(
                Statement=[
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[awacs.sts.AssumeRole],
                        Principal=awacs.aws.Principal(
                            'Service',
                            "codepipeline.amazonaws.com"
                        )
                    )]
            ),
            Policies=[
                pipeline_policy
            ]
        )

        source_stage = codepipeline.Stages(
            Name="SourceStage",
            Actions=[
                codepipeline.Actions(
                    Name="SourceAction",
                    ActionTypeId=codepipeline.ActionTypeId(
                        Category="Source",
                        Owner="AWS",
                        Version="1",
                        Provider='S3',
                    ),
                    OutputArtifacts=[
                        codepipeline.OutputArtifacts(
                            Name="SourceStageOutput"
                        )
                    ],
                    Configuration={
                        # TODO: inject the s3 things
                        "S3Bucket": Ref(pipeline_bucket),
                        "S3ObjectKey": "iteration-1.tar.gz"
                    },
                    RunOrder="1"
                )
            ]
        )

        generic_pipeline = codepipeline.Pipeline(
            "AppPipeline",
            RoleArn=troposphere.GetAtt(pipeline_service_role, "Arn"),
            Stages=[source_stage],
            ArtifactStore=codepipeline.ArtifactStore(
                Type="S3",
                Location=Ref(pipeline_bucket)
            )
        )

        # TODO: don't add this to the template if one has been supplied
        chain_context.template.add_resource(pipeline_bucket)
        chain_context.template.add_resource(pipeline_service_role)
        chain_context.template.add_resource(generic_pipeline)

        chain_context.metadata[META_LAST_STAGE_OUTPUT] = 'SourceStageOutput'


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


class CodeBuildStage(step.Step):

    def __init__(self, vpc_config=None):
        """
        :type vpc_config: required if the codebuild step requires access to the VPC
        """
        step.Step.__init__(self)
        self.vpc_config = vpc_config

    def handle(self, chain_context):

        previous_stage_output = chain_context.metadata[META_LAST_STAGE_OUTPUT]

        log_group = log_resource.LogGroup(
            "%sLogGroup" % chain_context.instance_name,
            LogGroupName=troposphere.Join('/', [
                '/aws/codebuild',
                chain_context.instance_name
            ]),
            RetentionInDays=90,
        )

        # TODO: put code build stuff into some kind of component?
        codebuild_policy = iam.Policy(
            PolicyName="CodeBuildPolicy%s" % chain_context.instance_name,
            PolicyDocument=awacs.aws.PolicyDocument(
                Version="2012-10-17",
                Id="CodeBuildPolicyForPipeline",
                Statement=[
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        # TODO: candidate for a component, re-use in cloudformation policies
                        Action=[
                            awacs.aws.Action("cloudformation", "*"),
                            awacs.aws.Action("ec2", "*"),
                            awacs.aws.Action("route53", "*"),
                            awacs.aws.Action("iam", "*"),
                            awacs.aws.Action("elasticloadbalancing", "*"),
                            awacs.aws.Action("s3", "*"),
                            awacs.aws.Action("autoscaling", "*"),
                            awacs.aws.Action("apigateway", "*"),
                            awacs.aws.Action("cloudwatch", "*"),
                            awacs.aws.Action("cloudfront", "*"),
                            awacs.aws.Action("rds", "*"),
                            awacs.aws.Action("dynamodb", "*"),
                            awacs.aws.Action("lambda", "*"),
                            awacs.aws.Action("sqs", "*"),
                            awacs.aws.Action("events", "*"),
                            awacs.iam.PassRole,
                        ],
                        # TODO: restrict more accurately
                        Resource=["*"]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.logs.CreateLogGroup,
                            awacs.logs.CreateLogStream,
                            awacs.logs.PutLogEvents,
                        ],
                        # TODO: restrict more accurately
                        Resource=["*"]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.s3.HeadBucket,
                        ],
                        Resource=[
                            '*'
                        ]
                    ),
                    # ec2:DescribeKeyPairs
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.aws.Action('ec2', 'Describe*'),
                        ],
                        # TODO: restrict more accurately.  What does codebuild need?
                        Resource=[
                            "*"
                        ]
                    ),
                    # used for codebuild in a vpc
                    awacs.aws.Statement(
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
                        Resource=['*']
                    )
                ]
            )
        )

        codebuild_role = iam.Role(
            "CodeBuildServiceRole",
            Path="/",
            AssumeRolePolicyDocument=awacs.aws.Policy(
                Statement=[
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[awacs.sts.AssumeRole],
                        Principal=awacs.aws.Principal(
                            'Service',
                            "codebuild.amazonaws.com"
                        )
                    )]
            ),
            Policies=[
                codebuild_policy
            ],
            ManagedPolicyArns=[
                chain_context.metadata[META_PIPELINE_BUCKET_POLICY_REF]
            ]
        )

        environment = codebuild.Environment(
            ComputeType='BUILD_GENERAL1_SMALL',
            Image='aws/codebuild/python:2.7.12',
            Type='LINUX_CONTAINER',
            EnvironmentVariables=[
                {'Name': 'PIPELINE_BUCKET', 'Value': chain_context.metadata[META_PIPELINE_BUCKET_REF]}
            ],
        )

        project = self.create_project(
            chain_context=chain_context,
            codebuild_role=codebuild_role,
            codebuild_environment=environment
        )

        code_build_stage = codepipeline.Stages(
            Name="Beta",  # TODO: inject name
            Actions=[
                codepipeline.Actions(
                    Name="DeployInfrastructureAction",
                    InputArtifacts=[
                        codepipeline.InputArtifacts(
                            Name=previous_stage_output
                        )
                    ],
                    ActionTypeId=codepipeline.ActionTypeId(
                        Category="Build",
                        Owner="AWS",
                        Version="1",
                        Provider="CodeBuild"
                    ),
                    Configuration={
                         'ProjectName': Ref(project)
                    },
                    RunOrder="1"
                )
            ]
        )

        chain_context.template.add_resource(log_group)
        chain_context.template.add_resource(codebuild_role)
        chain_context.template.add_resource(project)

        found_pipeline = TemplateQuery.get_resource_by_type(
            template=chain_context.template,
            type_to_find=codepipeline.Pipeline)[0]
        stages = found_pipeline.properties['Stages']  # type: list

        stages.append(code_build_stage)

    def create_project(self, chain_context, codebuild_role, codebuild_environment):

        artifacts = codebuild.Artifacts(Type='CODEPIPELINE')

        vpc_config = {}

        # Configure vpc if available
        if self.vpc_config:
            sg = ec2.SecurityGroup(
                "CodebBuild%sSG" % chain_context.instance_name,
                GroupDescription="Gives codebuild access to VPC",
                VpcId=self.vpc_config.vpc_id,
                SecurityGroupEgress=[
                    {
                        "IpProtocol": "-1",
                        "CidrIp": "0.0.0.0/0",
                        "FromPort": "0",
                        "ToPort": "65535",
                    }
                ],
            )
            chain_context.template.add_resource(sg)
            vpc_config = {'VpcConfig': codebuild.VpcConfig(
                    VpcId=self.vpc_config.vpc_id,
                    Subnets=self.vpc_config.subnets,
                    SecurityGroupIds=[Ref(sg)],
                )}

        project = codebuild.Project(
            "project%s" % chain_context.instance_name,
            DependsOn=codebuild_role.title,
            Artifacts=artifacts,
            BadgeEnabled=True,
            Environment=codebuild_environment,
            Name="pipeline-%s" % chain_context.instance_name,
            ServiceRole=troposphere.GetAtt(codebuild_role, 'Arn'),
            Source=codebuild.Source(
                "Deploy",
                Type='CODEPIPELINE',
            ),
            **vpc_config
        )

        return project
