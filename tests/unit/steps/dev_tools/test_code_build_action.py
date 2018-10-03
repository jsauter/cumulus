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
from cumulus.steps.dev_tools import META_PIPELINE_BUCKET_POLICY_REF, META_PIPELINE_BUCKET_NAME


class TestCodeBuildAction(unittest.TestCase):

    def setUp(self):
        self.context = chaincontext.ChainContext(
            template=troposphere.Template(),
            instance_name='justtestin'
        )
        self.context.metadata[META_PIPELINE_BUCKET_POLICY_REF] = "blah"
        self.context.metadata[META_PIPELINE_BUCKET_NAME] = troposphere.Ref("notabucket")

        self.pipeline_name = "ThatPipeline"
        self.deploy_stage_name = "DeployIt"
        self.source_stage_name = "SourceIt"

        TestCodeBuildAction._add_pipeline_and_stage_to_template(self.context.template, self.pipeline_name, self.deploy_stage_name)

    def tearDown(self):
        del self.context

    @staticmethod
    def _add_pipeline_and_stage_to_template(template, pipeline_name, deploy_stage_name):
        pipeline = template.add_resource(troposphere.codepipeline.Pipeline(
            pipeline_name,
            Stages=[]
        ))

        deploy_stage = template.add_resource(troposphere.codepipeline.Stages(
            Name=deploy_stage_name,
            Actions=[]
        ))
        pipeline.properties['Stages'].append(deploy_stage)
