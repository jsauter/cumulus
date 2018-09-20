try:
    # python 3
    from unittest.mock import patch # noqa
    from unittest.mock import MagicMock
except:  # noqa
    # python 2
    from mock import patch, MagicMock # noqa

import unittest

import troposphere

from cumulus.chain import chaincontext, step
from cumulus.chain import chain


class MockStepWithRequiredParam(step.Step):

    def handle(self, chain_context):
        """
        A sample handle event, showing how parameters should be implemented.
        :type chain_context: chaincontext.ChainContext
        """
        if not chain_context.auto_param_creation:
            chain_context.required_params.add("NumberOfMinions")
            chain_context.required_params.add("NumberOfEyeballs")

        if chain_context.auto_param_creation:
            chain_context.template.add_parameter(troposphere.Parameter("NumberOfMinions", Type="String"))
            chain_context.template.add_parameter(troposphere.Parameter("NumberOfEyeballs", Type="String"))


class TestRequiredParams(unittest.TestCase):

    def setUp(self):
        self.context = chaincontext.ChainContext(
            template=troposphere.Template(),
            instance_name='justtestin',
            auto_param_creation=False
        )

    def tearDown(self):
        del self.context

    def test_should_call_validate_when_chain_runs(self):
        the_chain = chain.Chain()

        the_chain.validate_template = MagicMock
        the_chain.run(self.context)
        self.assertTrue(the_chain.validate_template.called)

    def test_should_throw_error_with_unsatisfied_required_params(self):
        the_chain = chain.Chain()
        mock_step = MockStepWithRequiredParam()
        the_chain.add(mock_step)

        self.assertRaisesRegexp(
            AssertionError,
            '.*Minions.*\n.*Eyeballs.*',
            the_chain.run,
            self.context
        )

    def test_should_validate_template_with_missing_params(self):
        """
        This tests the same functionality as test_should_throw_error_with_unsatisfied_required_params
        however, it doesn't use the example code.  The idea was to keep example code even though
        it's less of a unit test.. to show how you would use params.  Tests as documentation :)
        :return:
        """
        the_chain = chain.Chain()

        self.context.required_params.add("ImARequiredParam")

        self.assertRaisesRegexp(
            AssertionError,
            'ImARequiredParam',
            the_chain.validate_template,
            self.context
        )

    def test_should_validate_template_without_any_required_params(self):
        the_chain = chain.Chain()
        the_chain.run(self.context)

    def test_should_build_template_with_required_parameters_added_externally(self):
        the_chain = chain.Chain()
        mock_step = MockStepWithRequiredParam()
        the_chain.add(mock_step)

        self.context = chaincontext.ChainContext(
            template=troposphere.Template(),
            instance_name='wont_generate_parameters',
            auto_param_creation=False
        )

        self.context.template.add_parameter(troposphere.Parameter(
            "NumberOfMinions",
            Type="String"
        ))

        self.context.template.add_parameter(troposphere.Parameter(
            "NumberOfEyeballs",
            Type="String"
        ))

        the_chain.run(self.context)

    def test_should_build_template_with_required_parameters_added_automatically(self):
        the_chain = chain.Chain()
        mock_step = MockStepWithRequiredParam()
        the_chain.add(mock_step)

        self.context = chaincontext.ChainContext(
            template=troposphere.Template(),
            instance_name='will_generate_parameters',
            auto_param_creation=True
        )

        the_chain.run(self.context)
