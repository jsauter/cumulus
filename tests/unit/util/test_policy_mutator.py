# try:
#     #python 3
#     from unittest.mock import patch
# except:
#     #python 2
#     from mock import patch

import unittest

import awacs
from awacs import aws  # noqa
import troposphere
from troposphere import iam

from cumulus.util.policy_mutator import PolicyMutator

DEFAULT_STATEMENT_NAME = "DefaultStatement"


class TestPolicyMutator(unittest.TestCase):

    def setUp(self):
        pass
        self.simple_policy = iam.Policy(
            PolicyName="TestPolicy",
            PolicyDocument=awacs.aws.PolicyDocument(
                Version="2012-10-17",
                Id="PipelinePolicy",
                Statement=[
                    awacs.aws.Statement(
                        Sid=("%s" % DEFAULT_STATEMENT_NAME),
                        Effect=awacs.aws.Allow,
                        Action=[awacs.aws.Action("s3", "*")],
                        Resource=['*'],
                    ),
                ],
            )
        )

        self.dummy_statement = awacs.aws.Statement()

    def tearDown(self):
        pass
        del self.simple_policy

    def test_should_raise_assertion_error_on_wrong_policy_type(self):
        policy = "not what you want"
        self.assertRaises(
            AssertionError,
            PolicyMutator.add_statement_to_policy,
            policy,
            self.dummy_statement,
        )

    def test_should_raise_assertion_error_if_policydocument_is_not_awacs(self):
        policy = troposphere.iam.Policy(
            PolicyDocument={}
        )
        self.assertRaises(
            AssertionError,
            PolicyMutator.add_statement_to_policy,
            policy,
            self.dummy_statement,
        )

    def test_should_raise_assertion_error_on_wrong_statement_type(self):
        policy = self.simple_policy
        self.assertRaises(
            AssertionError,
            PolicyMutator.add_statement_to_policy,
            policy,
            {"statment": "is wrong"},
        )

    def test_should_add_statement_to_existing_policy(self):
        pass
        policy = self.simple_policy
        lambda_policy_name = 'LambdaPolicy'
        statement = awacs.aws.Statement(
            Sid=('%s' % lambda_policy_name),
            Effect=awacs.aws.Allow,
            Action=[
                awacs.aws.Action("lambda", "*")
            ],
            Resource=["*"]
        )

        found_default = list(filter(lambda x: x.Sid == DEFAULT_STATEMENT_NAME, policy.PolicyDocument.Statement))
        self.assertTrue(found_default, "Did not find the statement I was looking for")
        self.assertIsInstance(found_default[0], awacs.aws.Statement)

        policy = PolicyMutator.add_statement_to_policy(policy, statement)

        found_sut = list(filter(lambda x: x.Sid == lambda_policy_name, policy.PolicyDocument.Statement))
        self.assertTrue(found_sut, "Did not find the statement I was looking for")
        self.assertIsInstance(found_default[0], awacs.aws.Statement)
