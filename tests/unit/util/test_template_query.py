# try:
#     #python 3
#     from unittest.mock import patch
# except:
#     #python 2
#     from mock import patch

import unittest

import troposphere
import troposphere.s3

from cumulus.util.template_query import TemplateQuery


class TestTemplateQuery(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass
        # del self.context

    def test_should_find_resource_by_title(self):
        t = troposphere.Template()

        resource_name_to_lookup = "TestingTheNameLookup"
        t.add_resource(troposphere.s3.Bucket(
            resource_name_to_lookup
        ))

        resource = TemplateQuery.get_resource_by_title(
            template=t,
            title=resource_name_to_lookup
        )

        self.assertIsNotNone(resource)
        self.assertIsInstance(resource, troposphere.s3.Bucket)

        self.assertEqual(resource.title, resource_name_to_lookup)

    def test_should_not_find_resource_by_title(self):
        t = troposphere.Template()

        resource_name_to_lookup = "TestingTheNameLookup"
        t.add_resource(troposphere.s3.Bucket(
            resource_name_to_lookup
        ))

        self.assertRaises(
            ValueError,
            TemplateQuery.get_resource_by_title,
            template=t,
            title="TestingTheNameLookups",
        )

        self.assertRaisesRegexp(
            ValueError,
            "Expected to find.+TestingTheNameLookup",
            callable_obj=TemplateQuery.get_resource_by_title,
            template=t,
            title="TestingTheNameLookups",
        )

    def test_should_find_resource_by_type(self):
        t = troposphere.Template()

        t.add_resource(troposphere.s3.Bucket(
            "whoCares"
        ))

        found = TemplateQuery.get_resource_by_type(
            template=t,
            type_to_find=troposphere.s3.Bucket
        )

        self.assertIsNotNone(found)
        self.assertIsInstance(found, list)
        self.assertIsInstance(found[0], troposphere.s3.Bucket)

    def test_should_not_find_resource_by_type(self):
        t = troposphere.Template()

        t.add_resource(troposphere.s3.Bucket(
            "thebucket"
        ))

        results = TemplateQuery.get_resource_by_type(t, troposphere.s3.Policy)

        self.assertTrue(results.count(results) == 0)
