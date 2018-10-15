from cumulus.util.template_query import TemplateQuery

try:
    # python 3
    from unittest.mock import patch # noqa
    from unittest.mock import MagicMock
except:  # noqa
    # python 2
    from mock import patch, MagicMock # noqa

import unittest

import troposphere
from troposphere import codepipeline  # noqa

from cumulus.chain import chaincontext
from cumulus.steps.dev_tools import cloud_formation_action, META_PIPELINE_BUCKET_POLICY_REF
from cumulus.types.cloudformation import action_mode


class TestCloudFormationAction(unittest.TestCase):

    def setUp(self):
        self.context = chaincontext.ChainContext(
            template=troposphere.Template(),
            instance_name='justtestin'
        )
        self.context.metadata[META_PIPELINE_BUCKET_POLICY_REF] = "blah"

        self.pipeline_name = "ThatPipeline"
        self.deploy_stage_name = "DeployIt"
        TestCloudFormationAction._add_pipeline_and_stage_to_template(self.context.template, self.pipeline_name, self.deploy_stage_name)

    def tearDown(self):
        del self.context

    @staticmethod
    def _add_pipeline_and_stage_to_template(template, pipeline_name, deploy_stage_name):
        pipeline = template.add_resource(troposphere.codepipeline.Pipeline(
            pipeline_name,
            Stages=[]
        ))

        # Not worrying about adding a source stage right now, as the tests are not assumed to actually
        # trigger a CloudFormation build of the pipeline

        deploy_stage = template.add_resource(troposphere.codepipeline.Stages(
            Name=deploy_stage_name,
            Actions=[]
        ))
        pipeline.properties['Stages'].append(deploy_stage)

    def test_handle_adds_cloud_formation_action_to_stage(self):
        action = cloud_formation_action.CloudFormationAction(
            action_name="CloudFormation",
            input_artifact_names=["InfraInput"],
            input_template_path="InfraInput::template.json",
            input_template_configuration="InfraInput::myenv.json",
            stage_name_to_add=self.deploy_stage_name,
            stack_name="my-microservice",
            action_mode=action_mode.ActionMode.REPLACE_ON_FAILURE,
            # cfn_action_config_role_arn=troposphere.NoValue,
            # cfn_action_role_arn=troposphere.NoValue
        )

        action.handle(self.context)

        deploy_stage = TemplateQuery.get_resource_by_type(self.context.template, codepipeline.Stages)[0]
        self.assertEqual(len(deploy_stage.Actions), 1)

        test_action = deploy_stage.Actions[0]
        self.assertEqual(test_action.Name, "CloudFormation")
        self.assertEqual(test_action.ActionTypeId.Category, "Deploy")
        self.assertEqual(test_action.ActionTypeId.Provider, "CloudFormation")
        self.assertEqual(test_action.Configuration['TemplatePath'], "InfraInput::template.json")
        self.assertEqual(test_action.Configuration['TemplateConfiguration'], "InfraInput::myenv.json")
        self.assertEqual(test_action.Configuration['ActionMode'], action_mode.ActionMode.REPLACE_ON_FAILURE.value)
        self.assertEquals(len(test_action.InputArtifacts), 1)
        self.assertEquals(test_action.InputArtifacts[0].Name, "InfraInput")
        # By default no output artifact is created
        self.assertFalse(hasattr(test_action, 'OutputArtifacts'))
        self.assertFalse('OutputFileName' in test_action.Configuration)

    def test_raises_error_if_target_stage_does_not_exist(self):
        action = cloud_formation_action.CloudFormationAction(
            action_name="CloudFormation",
            input_artifact_names=["InfraInput"],
            input_template_path="InfraInput::template.json",
            input_template_configuration="InfraInput::myenv.json",
            stage_name_to_add="ThisStageDoesNotExist",
            stack_name="my-microservice",
            action_mode=action_mode.ActionMode.REPLACE_ON_FAILURE
        )
        self.assertRaises(
            ValueError,
            action.handle,
            self.context)

    def test_can_add_multiple_input_artifacts(self):
        action = cloud_formation_action.CloudFormationAction(
            action_name="CloudFormation",
            input_artifact_names=["InfraInput", "ParameterInput"],
            input_template_path="InfraInput::template.json",
            input_template_configuration="ParameterInput::myenv.json",
            stage_name_to_add=self.deploy_stage_name,
            stack_name="my-microservice",
            action_mode=action_mode.ActionMode.REPLACE_ON_FAILURE
        )

        action.handle(self.context)

        deploy_stage = TemplateQuery.get_resource_by_type(self.context.template, codepipeline.Stages)[0]
        self.assertEqual(len(deploy_stage.Actions), 1)

        test_action = deploy_stage.Actions[0]
        self.assertEqual(test_action.Name, "CloudFormation")
        self.assertEqual(test_action.Configuration['TemplatePath'], "InfraInput::template.json")
        self.assertEqual(test_action.Configuration['TemplateConfiguration'], "ParameterInput::myenv.json")
        self.assertEquals(len(test_action.InputArtifacts), 2)
        self.assertEquals(test_action.InputArtifacts[0].Name, "InfraInput")
        self.assertEquals(test_action.InputArtifacts[1].Name, "ParameterInput")

    def test_can_create_output_artifact(self):
        action = cloud_formation_action.CloudFormationAction(
            action_name="CloudFormation",
            input_artifact_names=["InfraInput"],
            input_template_path="InfraInput::template.json",
            input_template_configuration="InfraInput::myenv.json",
            output_artifact_name="AllOfTheThings",
            stage_name_to_add=self.deploy_stage_name,
            stack_name="my-microservice",
            action_mode=action_mode.ActionMode.REPLACE_ON_FAILURE
        )

        action.handle(self.context)

        deploy_stage = TemplateQuery.get_resource_by_type(self.context.template, codepipeline.Stages)[0]
        self.assertEqual(len(deploy_stage.Actions), 1)

        test_action = deploy_stage.Actions[0]
        self.assertEquals(len(test_action.OutputArtifacts), 1)
        self.assertEquals(test_action.OutputArtifacts[0].Name, "AllOfTheThings")
        self.assertEquals(test_action.Configuration['OutputFileName'], "StackOutputs.json")

    def test_sets_role_arn_to_cfn_action(self):
        expected_arn = "im_an_arn"
        action = cloud_formation_action.CloudFormationAction(
            action_name="CloudFormation",
            input_artifact_names=["InfraInput"],
            input_template_path="InfraInput::template.json",
            input_template_configuration="InfraInput::myenv.json",
            output_artifact_name="AllOfTheThings",
            stage_name_to_add=self.deploy_stage_name,
            stack_name="my-microservice",
            action_mode=action_mode.ActionMode.REPLACE_ON_FAILURE,
            cfn_action_role_arn=expected_arn
        )

        action.handle(self.context)

        deploy_stage = TemplateQuery.get_resource_by_type(self.context.template, codepipeline.Stages)[0]
        self.assertEqual(len(deploy_stage.Actions), 1)

        test_action = deploy_stage.Actions[0]
        self.assertEquals(test_action.RoleArn, expected_arn)
        self.assertTrue(hasattr(test_action, 'RoleArn'))

    def test_does_not_set_role_arn_to_cfn_action(self):
        action = cloud_formation_action.CloudFormationAction(
            action_name="CloudFormation",
            input_artifact_names=["InfraInput"],
            input_template_path="InfraInput::template.json",
            input_template_configuration="InfraInput::myenv.json",
            output_artifact_name="AllOfTheThings",
            stage_name_to_add=self.deploy_stage_name,
            stack_name="my-microservice",
            action_mode=action_mode.ActionMode.REPLACE_ON_FAILURE,
        )

        action.handle(self.context)

        deploy_stage = TemplateQuery.get_resource_by_type(self.context.template, codepipeline.Stages)[0]
        self.assertEqual(len(deploy_stage.Actions), 1)

        test_action = deploy_stage.Actions[0]
        self.assertFalse(hasattr(test_action, 'RoleArn'))

    def test_sets_config_role_arn_to_cfn_action_configuration(self):
        expected_arn = 'im_another_arn'
        action = cloud_formation_action.CloudFormationAction(
            action_name="CloudFormation",
            input_artifact_names=["InfraInput"],
            input_template_path="InfraInput::template.json",
            input_template_configuration="InfraInput::myenv.json",
            output_artifact_name="AllOfTheThings",
            stage_name_to_add=self.deploy_stage_name,
            stack_name="my-microservice",
            action_mode=action_mode.ActionMode.REPLACE_ON_FAILURE,
            cfn_action_config_role_arn=expected_arn,
        )

        action.handle(self.context)

        deploy_stage = TemplateQuery.get_resource_by_type(self.context.template, codepipeline.Stages)[0]
        self.assertEqual(len(deploy_stage.Actions), 1)

        test_action = deploy_stage.Actions[0]
        self.assertTrue("RoleArn" in test_action.Configuration)
        self.assertEqual(test_action.Configuration['RoleArn'], expected_arn)
        self.assertFalse(hasattr(test_action, 'RoleArn'))

    def test_uses_default_config_role_arn_to_cfn_action_configuration(self):
        unexpected_arn = 'im_another_arn'
        action = cloud_formation_action.CloudFormationAction(
            action_name="CloudFormation",
            input_artifact_names=["InfraInput"],
            input_template_path="InfraInput::template.json",
            input_template_configuration="InfraInput::myenv.json",
            output_artifact_name="AllOfTheThings",
            stage_name_to_add=self.deploy_stage_name,
            stack_name="my-microservice",
            action_mode=action_mode.ActionMode.REPLACE_ON_FAILURE,
        )

        action.handle(self.context)

        deploy_stage = TemplateQuery.get_resource_by_type(self.context.template, codepipeline.Stages)[0]
        self.assertEqual(len(deploy_stage.Actions), 1)

        test_action = deploy_stage.Actions[0]
        self.assertTrue("RoleArn" in test_action.Configuration)
        self.assertNotEqual(test_action.Configuration['RoleArn'], unexpected_arn)
        self.assertFalse(hasattr(test_action, 'RoleArn'))
        self.assertTrue(test_action.Configuration['RoleArn'].__class__ is troposphere.GetAtt)
