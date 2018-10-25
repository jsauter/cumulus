import awacs
import troposphere
from awacs.aws import PolicyDocument  # noqa
from troposphere.iam import Policy  # noqa


class PolicyMutator:
    def __init__(self):
        pass

    @staticmethod
    def add_statement_to_policy(policy, statement):
        """

        :type policy: troposphere.iam.Policy
        :type statement: awacs.aws.Statement
        """
        if type(policy) is not troposphere.iam.Policy:
            raise AssertionError("Expected to find troposphere.iam.Policy but found: %s" % type(policy))

        if not isinstance(policy.PolicyDocument, awacs.aws.PolicyDocument):
            msg = "Expected policy.PolicyDocument to be awacs.aws.PolicyDocument but found: %s" \
                  % type(policy.PolicyDocument)
            raise AssertionError(msg)

        if not isinstance(statement, awacs.aws.Statement):
            msg = "Expected statement to be awacs.aws.Statement but found: %s " % type(statement)
            raise AssertionError(msg)

        policy.PolicyDocument.Statement.append(statement)
        return policy
