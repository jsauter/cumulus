
import awacs
import awacs.aws
import awacs.awslambda
import awacs.codecommit
import awacs.ec2
import awacs.iam
import awacs.logs
import awacs.s3
import awacs.sts
import awacs.kms
import troposphere
from troposphere import codepipeline, Ref, iam
from troposphere.s3 import Bucket, VersioningConfiguration

import cumulus.steps.dev_tools
from cumulus.chain import step


class Pipeline(step.Step):
    def __init__(self,
                 name,
                 bucket_name,
                 pipeline_service_role_arn=None,
                 create_bucket=True,
                 pipeline_policies=None,
                 bucket_policy_statements=None,
                 bucket_kms_key_arn=None,
                 ):
        """

        :type pipeline_service_role_arn: basestring Override the pipeline service role. If you pass this
                                                     the pipeline_policies is not used.
        :type create_bucket: bool if False, will not create the bucket. Will attach policies either way.
        :type bucket_name: the name of the bucket that will be created suffixed with the chaincontext instance name
        :type bucket_policy_statements: [awacs.aws.Statement]
        :type pipeline_policies: [troposphere.iam.Policy]
        :type bucket_kms_key_arn: ARN used to decrypt the pipeline artifacts
        """
        step.Step.__init__(self)
        self.name = name
        self.bucket_name = bucket_name
        self.create_bucket = create_bucket
        self.pipeline_service_role_arn = pipeline_service_role_arn
        self.bucket_policy_statements = bucket_policy_statements
        self.pipeline_policies = pipeline_policies or []
        self.bucket_kms_key_arn = bucket_kms_key_arn

    def handle(self, chain_context):
        """
        This step adds in the shell of a pipeline.
         * s3 bucket
         * policies for the bucket and pipeline
         * your next step in the chain MUST be a source stage
        :param chain_context:
        :return:
        """
        if self.create_bucket:
            pipeline_bucket = Bucket(
                "PipelineBucket%s" % self.name,
                BucketName=self.bucket_name,
                VersioningConfiguration=VersioningConfiguration(
                    Status="Enabled"
                )
            )
            chain_context.template.add_resource(pipeline_bucket)

        default_bucket_policies = self.get_default_bucket_policy_statements(self.bucket_name)

        if self.bucket_policy_statements:
            bucket_access_policy = self.get_bucket_policy(
                pipeline_bucket=self.bucket_name,
                bucket_policy_statements=self.bucket_policy_statements,
            )
            chain_context.template.add_resource(bucket_access_policy)

        pipeline_bucket_access_policy = iam.ManagedPolicy(
            "PipelineBucketAccessPolicy",
            Path='/managed/',
            PolicyDocument=awacs.aws.PolicyDocument(
                Version="2012-10-17",
                Id="bucket-access-policy%s" % chain_context.instance_name,
                Statement=default_bucket_policies
            )
        )

        chain_context.metadata[cumulus.steps.dev_tools.META_PIPELINE_BUCKET_NAME] = self.bucket_name
        chain_context.metadata[cumulus.steps.dev_tools.META_PIPELINE_BUCKET_POLICY_REF] = Ref(
            pipeline_bucket_access_policy)

        default_pipeline_role = self.get_default_pipeline_role()
        pipeline_service_role_arn = self.pipeline_service_role_arn or troposphere.GetAtt(default_pipeline_role, "Arn")

        generic_pipeline = codepipeline.Pipeline(
            "Pipeline",
            RoleArn=pipeline_service_role_arn,
            Stages=[],
            ArtifactStore=codepipeline.ArtifactStore(
                Type="S3",
                Location=self.bucket_name,
            )
        )

        if self.bucket_kms_key_arn:
            encryption_config = codepipeline.EncryptionKey(
                "ArtifactBucketKmsKey",
                Id=self.bucket_kms_key_arn,
                Type='KMS',
            )
            generic_pipeline.ArtifactStore.EncryptionKey = encryption_config

        pipeline_output = troposphere.Output(
            "PipelineName",
            Description="Code Pipeline",
            Value=Ref(generic_pipeline),
        )
        pipeline_bucket_output = troposphere.Output(
            "PipelineBucket",
            Description="Name of the input artifact bucket for the pipeline",
            Value=self.bucket_name,
        )

        if not self.pipeline_service_role_arn:
            chain_context.template.add_resource(default_pipeline_role)

        chain_context.template.add_resource(pipeline_bucket_access_policy)
        chain_context.template.add_resource(generic_pipeline)
        chain_context.template.add_output(pipeline_output)
        chain_context.template.add_output(pipeline_bucket_output)

    def get_default_pipeline_role(self):
        # TODO: this can be cleaned up by using a policytype and passing in the pipeline role it should add itself to.
        pipeline_policy = iam.Policy(
            PolicyName="%sPolicy" % self.name,
            PolicyDocument=awacs.aws.PolicyDocument(
                Version="2012-10-17",
                Id="PipelinePolicy",
                Statement=[
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        # TODO: actions here could be limited more
                        Action=[awacs.aws.Action("s3", "*")],
                        Resource=[
                            troposphere.Join('', [
                                awacs.s3.ARN(),
                                self.bucket_name,
                                "/*"
                            ]),
                            troposphere.Join('', [
                                awacs.s3.ARN(),
                                self.bucket_name,
                            ]),
                        ],
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[awacs.aws.Action("kms", "*")],
                        Resource=['*'],
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.aws.Action("cloudformation", "*"),
                            awacs.aws.Action("codebuild", "*"),
                        ],
                        # TODO: restrict more accurately
                        Resource=["*"]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.codecommit.GetBranch,
                            awacs.codecommit.GetCommit,
                            awacs.codecommit.UploadArchive,
                            awacs.codecommit.GetUploadArchiveStatus,
                            awacs.codecommit.CancelUploadArchive
                        ],
                        Resource=["*"]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.iam.PassRole
                        ],
                        Resource=["*"]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.aws.Action("lambda", "*")
                        ],
                        Resource=["*"]
                    ),
                ],
            )
        )

        pipeline_service_role = iam.Role(
            "PipelineServiceRole",
            Path="/",
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
            Policies=[pipeline_policy] + self.pipeline_policies
        )
        return pipeline_service_role

    def get_default_bucket_policy_statements(self, pipeline_bucket):
        bucket_policy_statements = [
            awacs.aws.Statement(
                Effect=awacs.aws.Allow,
                Action=[
                    awacs.s3.ListBucket,
                    awacs.s3.GetBucketVersioning,
                ],
                Resource=[
                    troposphere.Join('', [
                        awacs.s3.ARN(),
                        pipeline_bucket,
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
                        pipeline_bucket,
                        '/*'
                    ]),
                ],
            )
        ]

        return bucket_policy_statements

    def get_bucket_policy(self, pipeline_bucket, bucket_policy_statements):
        policy = troposphere.s3.BucketPolicy(
            "PipelineBucketPolicy",
            Bucket=pipeline_bucket,
            PolicyDocument=awacs.aws.Policy(
                Statement=bucket_policy_statements,
            ),
        )
        return policy
