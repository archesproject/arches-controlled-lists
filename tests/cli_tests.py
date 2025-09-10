import io
import os

from django.core import management
from django.test import TestCase
from django.test.utils import captured_stdout
from django.core.management.base import CommandError

from arches.app.models.models import Node
from arches_controlled_lists.models import List, ListItem, ListItemValue

from .test_settings import PROJECT_TEST_ROOT


# these tests can be run from the command line via
# python manage.py test tests.cli_tests --settings="tests.test_settings"


class ListExportPackageTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        from tests.test_views import ListTests

        return ListTests.setUpTestData()

    def test_export_controlled_list_xlsx(self):
        export_file_name = "list_xlsx_export"
        file_path = os.path.join(PROJECT_TEST_ROOT, f"{export_file_name}.xlsx")
        self.addCleanup(os.remove, file_path)
        output = io.StringIO()
        # packages command does not yet fully avoid print()
        with captured_stdout():
            management.call_command(
                "packages",
                operation="export_controlled_lists",
                dest_dir=PROJECT_TEST_ROOT,
                file_name=export_file_name,
                controlled_lists="",
                format="xlsx",
                stdout=output,
            )
        self.assertTrue(os.path.exists(file_path))

    def test_export_controlled_list_skos(self):
        export_file_name = "lists_skos_export"
        file_path = os.path.join(PROJECT_TEST_ROOT, f"{export_file_name}.xml")
        self.addCleanup(os.remove, file_path)
        output = io.StringIO()
        # packages command does not yet fully avoid print()
        with captured_stdout():
            management.call_command(
                "packages",
                operation="export_controlled_lists",
                dest_dir=PROJECT_TEST_ROOT,
                file_name=export_file_name,
                controlled_lists="",
                format="skos-rdf",
                stdout=output,
            )
        self.assertTrue(os.path.exists(file_path))


class ListImportPackageTests(TestCase):

    def test_import_controlled_list(self):
        input_file = os.path.join(
            PROJECT_TEST_ROOT, "fixtures", "data", "controlled_lists.xlsx"
        )
        output = io.StringIO()
        # packages command does not yet fully avoid print()
        with captured_stdout():
            management.call_command(
                "packages",
                operation="import_controlled_lists",
                source=input_file,
                stdout=output,
            )

        self.assertEqual(List.objects.count(), 2)
        self.assertEqual(ListItem.objects.count(), 10)
        self.assertEqual(ListItemValue.objects.count(), 21)

    ### TODO Add test for creating new language if language code not in db but found in import file

    def test_import_from_skos(self):
        input_file = os.path.join(
            PROJECT_TEST_ROOT, "fixtures", "data", "skos_rdf_import_example.xml"
        )
        output = io.StringIO()
        # packages command does not yet fully avoid print()
        with captured_stdout():
            management.call_command(
                "packages",
                operation="import_controlled_lists",
                source=input_file,
                overwrite="ignore",
                stdout=output,
            )

        self.assertEqual(List.objects.count(), 1)
        self.assertEqual(ListItem.objects.count(), 17)
        self.assertEqual(ListItemValue.objects.count(), 21)
        # child1 list item should be duplicated
        child1_list_items = ListItem.objects.filter(
            uri="http://localhost:8000/fea17c9d-e9c2-4469-91f9-6519f6692625"
        )
        self.assertEqual(child1_list_items.count(), 2)
        # but those list items will have different parents
        child1_instance_1 = child1_list_items[0]
        child1_instance_2 = child1_list_items[1]
        self.assertNotEqual(child1_instance_1.parent, child1_instance_2.parent)

        # They should have distinct list item values
        self.assertNotEqual(
            child1_instance_1.list_item_values.first().pk,
            child1_instance_2.list_item_values.first().pk,
        )
        # but the values should be the same
        self.assertEqual(
            child1_instance_1.list_item_values.first().value,
            child1_instance_2.list_item_values.first().value,
        )

        # Re-run with overwrite
        with captured_stdout():
            management.call_command(
                "packages",
                operation="import_controlled_lists",
                source=input_file,
                overwrite="overwrite",
                stdout=output,
            )

        self.assertEqual(List.objects.count(), 1)
        self.assertEqual(ListItem.objects.count(), 17)
        self.assertEqual(ListItemValue.objects.count(), 21)

        # Re-run last time with duplicate
        with captured_stdout():
            management.call_command(
                "packages",
                operation="import_controlled_lists",
                source=input_file,
                overwrite="duplicate",
                stdout=output,
            )

        self.assertEqual(List.objects.count(), 2)
        self.assertEqual(ListItem.objects.count(), 34)
        self.assertEqual(ListItemValue.objects.count(), 42)


class RDMToControlledListsETLTests(TestCase):
    fixtures = ["polyhierarchical_collections"]

    def test_migrate_collections_to_controlled_lists(self):
        output = io.StringIO()
        management.call_command(
            "controlled_lists",
            operation="migrate_collections_to_controlled_lists",
            # Migrate all collections with empty string param
            collections_to_migrate=[""],
            host="http://localhost:8000/plugins/controlled-list-manager/item/",
            preferred_sort_language="en",
            overwrite=False,
            stdout=output,
        )

        imported_list = List.objects.get(name="Polyhierarchical Collection Test")
        imported_items = (
            imported_list.list_items.all().with_list_item_labels().order_by("sortorder")
        )
        self.assertEqual(len(imported_items), 3)

        imported_item_values = ListItemValue.objects.filter(
            list_item__in=imported_items
        )
        self.assertQuerySetEqual(
            imported_item_values.values_list("value", flat=True).order_by("value"),
            [
                "French Test Concept 1",
                "French Test Concept 2",
                "French Test Concept 3",
                "Test Concept 1",
                "Test Concept 2",
                "Test Concept 3",
            ],
        )

        # Check that sortorder was calculated correctly based on sortorder value coming from RDM
        # Test Concept 3 has sortorder 0,
        # Test Concept 2 has sortorder 1,
        # and Test Concept 1 has no provided sortorder, so will fall back to alpha order
        # after those with a provided sortorder.
        self.assertIn(
            imported_items[0].list_item_labels[0].value,
            ["Test Concept 3", "French Test Concept 3"],
        )
        self.assertIn(
            imported_items[1].list_item_labels[0].value,
            ["Test Concept 2", "French Test Concept 2"],
        )
        self.assertIn(
            imported_items[2].list_item_labels[0].value,
            ["Test Concept 1", "French Test Concept 1"],
        )

        imported_list_2 = List.objects.get(name="Polyhierarchy Collection 2")
        imported_items_2 = imported_list_2.list_items.all()
        imported_item_values_2 = ListItemValue.objects.filter(
            list_item__in=imported_items_2
        )

        # Check that new uuids were generated for polyhierarchical concepts
        self.assertNotEqual(
            imported_item_values.filter(value="Test Concept 1"),
            imported_item_values_2.filter(value="Test Concept 1"),
        )

        # Check that items with multiple prefLabels in different languages have same listitemid
        self.assertEqual(
            imported_item_values.get(value="Test Concept 1").list_item_id,
            imported_item_values.get(value="French Test Concept 1").list_item_id,
        )

        # But that items with prefLabels in different languages have different listitemvalue ids
        self.assertNotEqual(
            imported_item_values.get(value="Test Concept 1").pk,
            imported_item_values.get(value="French Test Concept 1").pk,
        )

    def test_no_matching_collection_error(self):
        expected_output = "Failed to find the following collections in the database: Collection That Doesn't Exist"
        output = io.StringIO()
        management.call_command(
            "controlled_lists",
            operation="migrate_collections_to_controlled_lists",
            collections_to_migrate=["Collection That Doesn't Exist"],
            host="http://localhost:8000/plugins/controlled-list-manager/item/",
            preferred_sort_language="en",
            overwrite=False,
            stderr=output,
        )
        self.assertIn(expected_output, output.getvalue().strip())

    def test_no_matching_language_error(self):
        expected_output = (
            "The preferred sort language, nonexistent, does not exist in the database."
        )
        output = io.StringIO()
        with self.assertRaises(CommandError) as e:
            management.call_command(
                "controlled_lists",
                operation="migrate_collections_to_controlled_lists",
                collections_to_migrate=["Polyhierarchical Collection Test"],
                host="http://localhost:8000/plugins/controlled-list-manager/item/",
                preferred_sort_language="nonexistent",
                overwrite=False,
                stderr=output,
            )
        self.assertEqual(expected_output, str(e.exception))


class MigrateConceptNodesToReferenceDatatypeTests(TestCase):
    # Test data has three models:
    # - `Concept Node Migration Test`, with four concept nodes
    # - `Collection Not Migrated`, with one concept node but the collection hasn't been migrated
    # - `No concept nodes`, only has a string and a number node
    # Contains a Collection "Top Concept", which has been migrated to a controlled list

    # To create test fixtures run:
    # python manage.py dumpdata models.CardModel models.CardComponent models.CardXNodeXWidget models.Concept models.Edge models.GraphModel models.GraphXPublishedGraph models.PublishedGraphEdit models.Language models.NodeGroup models.Node models.Relation models.ResourceXResource models.ResourceInstance models.TileModel models.Value models.Widget arches_controlled_lists.List arches_controlled_lists.ListItem arches_controlled_lists.ListItemValue --format json --output concept_node_migration_test_data.json
    fixtures = ["concept_node_migration_test_data"]

    def test_migrate_concept_nodes_to_reference_datatype(self):
        output = io.StringIO()
        TEST_GRAPH_ID = "8f7cfa3c-d0e0-4a66-8608-43dd726a1b81"

        management.call_command(
            "controlled_lists",
            operation="migrate_concept_nodes_to_reference_datatype",
            graph=TEST_GRAPH_ID,
            stdout=output,
        )

        nodes = Node.objects.filter(graph_id=TEST_GRAPH_ID).prefetch_related(
            "cardxnodexwidget_set"
        )
        reference_nodes = nodes.filter(datatype="reference")

        self.assertEqual(len(nodes.filter(datatype__in=["concept", "concept-list"])), 0)
        self.assertEqual(len(reference_nodes), 4)

        expected_node_config_keys = ["multiValue", "controlledList"]
        expected_widget_config_keys = [
            "label",
            "placeholder",
            "defaultValue",
            "i18n_properties",
        ]
        for node in reference_nodes:
            self.assertEqual(expected_node_config_keys, list(node.config.keys()))
            for widget in node.cardxnodexwidget_set.all():
                self.assertEqual(
                    expected_widget_config_keys, list(widget.config.keys())
                )

    def test_no_matching_graph_error(self):
        output = io.StringIO()
        expected_output = "Graph matching query does not exist."

        with self.assertRaises(CommandError) as e:
            management.call_command(
                "controlled_lists",
                operation="migrate_concept_nodes_to_reference_datatype",
                graph="00000000-0000-0000-0000-000000000000",
                stderr=output,
            )
        self.assertEqual(str(e.exception), expected_output)

    def test_no_concept_nodes_error(self):
        output = io.StringIO()
        expected_output = (
            "No concept/concept-list nodes found for the No concept nodes graph"
        )

        with self.assertRaises(CommandError) as e:
            management.call_command(
                "controlled_lists",
                operation="migrate_concept_nodes_to_reference_datatype",
                graph="fc46b399-c824-45e5-86e2-5b992b8fa619",
                stderr=output,
            )
        self.assertEqual(str(e.exception), expected_output)

    def test_collections_not_migrated_error(self):
        output = io.StringIO()
        expected_output = "The following collections for the associated nodes have not been migrated to controlled lists:\nNode alias: concept_not_migrated, Collection ID: 00000000-0000-0000-0000-000000000005"

        management.call_command(
            "controlled_lists",
            operation="migrate_concept_nodes_to_reference_datatype",
            graph="b974103f-73bb-4f2a-bffb-8303227ba0da",
            stderr=output,
        )
        self.assertEqual(output.getvalue().strip(), expected_output)
