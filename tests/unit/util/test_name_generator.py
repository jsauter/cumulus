import unittest

from troposphere.applicationautoscaling import MetricDimension
from troposphere.autoscaling import AutoScalingGroup

from cumulus.util.DefaultNameTemplate import DefaultNameTemplate
from cumulus.util.name_generator import NameGenerator


class TestNameGenerator(unittest.TestCase):

    def test_should_generate_name(self):
        default_template = DefaultNameTemplate()

        name_generator = NameGenerator(name_generator_template=default_template)

        self.assertTrue(name_generator.create_name(AutoScalingGroup, "mystack") == "Asgmystack")

    def test_should_throw_not_implemented_when_type_not_handled(self):
        default_template = DefaultNameTemplate()

        name_generator = NameGenerator(name_generator_template=default_template)

        self.assertRaises(NotImplementedError, name_generator.create_name, MetricDimension, "mystack")
