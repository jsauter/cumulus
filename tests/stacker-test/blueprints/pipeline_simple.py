from stacker.blueprints.base import Blueprint

from troposphere.cloudformation import WaitConditionHandle
from troposphere.s3 import Bucket


class PipelineSimple(Blueprint):
    """Touch creates a wait condition handle and nothing else.

    For learning / functional testing.
    """

    def create_template(self):
       t = self.template

       t.add_resource(Bucket(
           "S3Bucket",
           BucketName='bswift-int-test-asdf'
       ))
