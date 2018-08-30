# try:
#     #python 3
#     from unittest.mock import patch
# except:
#     #python 2
#     from mock import patch

import unittest

import troposphere
from troposphere import codepipeline, codebuild

import cumulus
import cumulus.steps.dev_tools.pipeline_stage
from cumulus.chain import chaincontext, step
from cumulus.steps.dev_tools import pipeline, code_build_action
from cumulus.steps.dev_tools.vpc_config import VpcConfig
from cumulus.util.tropo import TemplateQuery


class TestPipelineStep(unittest.TestCase):

    def setUp(self):
        self.context = chaincontext.ChainContext(
            template=troposphere.Template(),
            instance_name='justtestin',
        )
        self.environment = codebuild.Environment(
            ComputeType='BUILD_GENERAL1_SMALL',
            Image='aws/codebuild/python:2.7.12',
            Type='LINUX_CONTAINER',
            EnvironmentVariables=[
                {'Name': 'TEST_VAR', 'Value': 'demo'}
            ],
        )

    def tearDown(self):
        del self.context

    def test_pipeline_records_metadata(self):
        sut = pipeline.Pipeline(
            name='test', bucket_name='testbucket'
        )
        sut.handle(self.context)
        self.assertIsInstance(sut, step.Step)
        self.assertTrue(
            expr=(cumulus.steps.dev_tools.META_PIPELINE_BUCKET_POLICY_REF in self.context.metadata),
            msg="Expected Pipeline would set bucket ref metadata"
        )

    def test_pipeline_step_is_added_to_template(self):

        sut = pipeline.Pipeline(
            name='test', bucket_name='testbucket'
        )
        sut.handle(self.context)
        t = self.context.template

        pipelines = TemplateQuery.get_resource_by_type(t, codepipeline.Pipeline)
        self.assertTrue(len(pipelines), 1)

    def test_codebuild_should_add_stage(self):
        sut = pipeline.Pipeline(
            name='test', bucket_name='testbucket'
        )
        sut.handle(self.context)
        t = self.context.template

        stage = cumulus.steps.dev_tools.pipeline_stage.PipelineStage("SourceStage")
        stage.handle(self.context)

        found_pipeline = TemplateQuery.get_resource_by_type(t, codepipeline.Pipeline)[0]
        stages = found_pipeline.properties['Stages']
        self.assertTrue(len(stages) == 1, msg="Expected Code Build to add a stage to the dev_tools")

    def test_stage_should_add_its_actions_to_template(self):
        sut = pipeline.Pipeline(
            name='test', bucket_name='testbucket'
        )
        sut.handle(self.context)
        t = self.context.template

        stage = cumulus.steps.dev_tools.pipeline_stage.PipelineStage("SourceStage")
        action = cumulus.steps.dev_tools.code_build_action.CodeBuildAction(
            action_name="testaction",
            input_artifact_name="notit.zip",
        )
        stage.add_action(action=action)
        stage.handle(self.context)

        found_pipeline = TemplateQuery.get_resource_by_type(t, codepipeline.Pipeline)[0]
        stages = found_pipeline.properties['Stages']
        self.assertTrue(len(stages) == 1, msg="Expected the chain to add a stage to the pipeline")
        stage_actions = stages[0].Actions
        self.assertTrue(len(stage_actions) == 1, msg="Expected the stage to add an action step")

    def test_code_build_should_not_add_vpc_config(self):

        action = code_build_action.CodeBuildAction(
            action_name="Test",
            stage_name_to_add="the_stage",
            input_artifact_name="no-input",
        )

        project = action.create_project(
            chain_context=self.context,
            codebuild_role='dummy-role',
            codebuild_environment=self.environment,
            name='test',
        )

        self.assertNotIn('VpcConfig', project.to_dict())

    def test_code_build_should_add_vpc_config(self):

        action = code_build_action.CodeBuildAction(
            vpc_config=VpcConfig(
                vpc_id='dummy-vpc',
                subnets=[
                    'dummy-subnet1'
                ]
            ),
            action_name="testAction",
            stage_name_to_add="thestage",
            input_artifact_name="test-input"
        )

        project = action.create_project(
            chain_context=self.context,
            codebuild_role='dummy-role',
            codebuild_environment=self.environment,
            name='test',
        )

        self.assertIn('VpcConfig', project.properties)
