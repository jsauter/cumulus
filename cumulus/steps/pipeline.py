import awacs
import troposphere
from awacs import aws, sts, s3, logs, ec2
from cumulus.chain import step
from cumulus.util.tropo import TemplateQuery

from troposphere import codepipeline, Ref, codebuild, iam, ec2
from troposphere import logs as log_resource
from troposphere.s3 import Bucket, VersioningConfiguration

META_PIPELINE_BUCKET_REF = 'pipeline-bucket-Ref'
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

        chain_context.metadata[META_PIPELINE_BUCKET_REF] = Ref(pipeline_bucket)

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
                        Effect=aws.Allow,
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
            AssumeRolePolicyDocument=aws.Policy(
                Statement=[
                    aws.Statement(
                        Effect=aws.Allow,
                        Action=[sts.AssumeRole],
                        Principal=aws.Principal(
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
                        "S3ObjectKey": "pipeline-spike/iteration-1.tar.gz"
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
            PolicyName='S3ReadArtifactBucket',
            PolicyDocument=awacs.aws.PolicyDocument(
                Version="2012-10-17",
                Id="CodeBuildPolicyForPipeline",
                Statement=[
                    aws.Statement(
                        Effect=aws.Allow,
                        Action=[
                            awacs.aws.Action("cloudformation", "*"),
                        ],
                        # TODO: restrict more accurately
                        Resource=["*"]
                    ),
                    aws.Statement(
                        Effect=aws.Allow,
                        Action=[
                            logs.CreateLogGroup,
                            logs.CreateLogStream,
                            logs.PutLogEvents,
                        ],
                        # TODO: restrict more accurately
                        Resource=["*"]
                    ),
                    aws.Statement(
                        Effect=aws.Allow,
                        Action=[
                            s3.GetObject,
                            s3.GetObjectVersion,
                            s3.ListObjects,
                        ],
                        # TODO: restrict more accurately.  What does codebuild need?
                        Resource=[
                            "*"
                            # troposphere.Join('', [
                            #     awacs.s3.ARN(),
                            #     chain_context.metadata[META_PIPELINE_BUCKET_REF],
                            #     "/*"
                            # ])
                        ]
                    ),
                    aws.Statement(
                        Effect=aws.Allow,
                        Action=[
                            aws.Action("s3", "*"),
                        ],
                        Resource=[
                            # s3.ARN("bswift-spike")
                            troposphere.Join('', [
                                awacs.s3.ARN(),
                                chain_context.metadata[META_PIPELINE_BUCKET_REF],
                                "/*"
                            ])
                        ]
                    ),
                    aws.Statement(
                        Effect=aws.Allow,
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
            AssumeRolePolicyDocument=aws.Policy(
                Statement=[
                    aws.Statement(
                        Effect=aws.Allow,
                        Action=[sts.AssumeRole],
                        Principal=aws.Principal(
                            'Service',
                            "codebuild.amazonaws.com"
                        )
                    )]
            ),
            Policies=[
                codebuild_policy
            ]
        )

        environment = codebuild.Environment(
            ComputeType='BUILD_GENERAL1_SMALL',
            Image='aws/codebuild/python:2.7.12',
            Type='LINUX_CONTAINER',
            EnvironmentVariables=[
                {'Name': 'TEST_VAR', 'Value': 'demo'}
            ],
        )

        project = self.create_project(
            chain_context=chain_context,
            codebuild_role=codebuild_role,
            environment=environment
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

    def create_project(self, chain_context, codebuild_role, environment):

        artifacts = codebuild.Artifacts(Type='CODEPIPELINE')

        vpc_config = {}

        # Configure vpc if available
        if self.vpc_config:
            sg = troposphere.ec2.SecurityGroup(
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
            Environment=environment,
            Name="DeployStacker",
            ServiceRole=troposphere.GetAtt(codebuild_role, 'Arn'),
            Source=codebuild.Source(
                "Deploy",
                Type='CODEPIPELINE',
            ),
            **vpc_config
        )

        return project
