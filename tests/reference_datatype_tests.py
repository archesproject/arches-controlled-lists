import uuid
from types import SimpleNamespace
from unittest.mock import Mock

from django.test import TestCase
from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models.tile import Tile
from arches.app.models.models import Node, TileModel
from arches.app.search.elasticsearch_dsl_builder import Bool
from arches_controlled_lists.datatypes.datatypes import (
    Reference,
    ReferenceDataType,
    ReferenceLabel,
)
from arches_controlled_lists.models import List, ListItem, ListItemValue

from tests.test_views import ListTests

# these tests can be run from the command line via
# python manage.py test tests.reference_datatype_tests --settings="tests.test_settings"


class ReferenceDataTypeTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        return ListTests.setUpTestData()

    def get_mock_tile(self):
        node = ListTests.node_using_list1
        list1 = ListTests.list1
        item = list1.list_items.get(sortorder=0)
        tile_repr = [
            {
                k: v
                for k, v in item.serialize().items()
                if k in ["uri", "values", "list_id"]
            }
        ]
        tile_repr[0]["labels"] = tile_repr[0].pop("values")

        return TileModel(
            resourceinstance_id=uuid.UUID("40000000-0000-0000-0000-000000000000"),
            nodegroup=node.nodegroup,
            data={str(node.pk): tile_repr},
        )

    def test_validate(self):
        reference = DataTypeFactory().get_instance("reference")
        mock_node = SimpleNamespace(config={"multiValue": False})

        for value, message in [
            ([{}], "Missing required value(s): 'uri', 'labels', and 'list_id'"),
            (
                [
                    {
                        "uri": "",
                        "labels": [],  # notice [] rather than None
                        "list_id": str(uuid.uuid4()),
                    }
                ],
                "Missing required value(s): 'labels'",
            ),
            (
                [
                    {
                        "uri": "https://www.domain.com/123",
                        "labels": [],
                        "garbage_key": "garbage_value",
                    }
                ],
                "Unexpected value: 'garbage_key'",
            ),
        ]:
            with self.subTest(reference_value=value):
                errors = reference.validate(value, node=mock_node)
                self.assertEqual(len(errors), 1, errors)
                self.assertEqual(errors[0]["message"], message)

        mock_list_item_id = uuid.uuid4()
        data = {
            "uri": "https://www.domain.com/label",
            "labels": [
                {
                    "id": "23b4efbd-2e46-4b3f-8d75-2f3b2bb96af2",
                    "value": "label",
                    "language_id": "en",
                    "list_item_id": str(mock_list_item_id),
                    "valuetype_id": "prefLabel",
                },
                {
                    "id": "e8676242-f0c7-4e3d-b031-fded4960cd86",
                    "language_id": "de",
                    "list_item_id": str(mock_list_item_id),
                    "valuetype_id": "prefLabel",
                },
            ],
            "list_id": uuid.uuid4(),
        }

        # Label missing value property
        errors = reference.validate(value=[data], node=mock_node)
        self.assertEqual(len(errors), 1, errors)

        data["labels"][1]["value"] = "a label"
        data["labels"][1]["language_id"] = "en"

        # Too many prefLabels per language
        errors = reference.validate(value=[data], node=mock_node)
        self.assertEqual(len(errors), 1, errors)

        data["labels"][1]["value"] = "ein label"
        data["labels"][1]["language_id"] = "de"
        data["labels"][1]["list_item_id"] = str(uuid.uuid4())

        # Mixed list_item_id values
        errors = reference.validate(value=[data], node=mock_node)
        self.assertEqual(len(errors), 1, errors)

        data["labels"][1]["list_item_id"] = str(mock_list_item_id)

        # Valid
        errors = reference.validate(value=[data], node=mock_node)
        self.assertEqual(errors, [])

        # None is always valid.
        errors = reference.validate(value=None, node=mock_node)
        self.assertEqual(errors, [])

        # Too many references
        errors = reference.validate(value=[data, data], node=mock_node)
        self.assertEqual(len(errors), 1, errors)

        # User error (missing arguments)
        errors = reference.validate(value=[data])
        self.assertEqual(len(errors), 1, errors)

    def test_tile_clean(self):
        reference = DataTypeFactory().get_instance("reference")
        nodeid = "72048cb3-adbc-11e6-9ccf-14109fd34195"
        resourceinstanceid = "40000000-0000-0000-0000-000000000000"
        data = [
            {
                "uri": "https://www.domain.com/label",
                "labels": [
                    {
                        "id": "23b4efbd-2e46-4b3f-8d75-2f3b2bb96af2",
                        "value": "label",
                        "language_id": "en",
                        "valuetype_id": "prefLabel",
                        "list_item_id": str(uuid.uuid4()),
                    },
                ],
                "list_id": "fd9508dc-2aab-4c46-85ae-dccce1200035",
            }
        ]

        tile_info = {
            "resourceinstance_id": resourceinstanceid,
            "parenttile_id": "",
            "nodegroup_id": nodeid,
            "tileid": "",
            "data": {nodeid: {"en": data}},
        }

        tile1 = Tile(tile_info)
        reference.clean(tile1, nodeid)
        self.assertIsNotNone(tile1.data[nodeid])

        tile1.data[nodeid] = []
        reference.clean(tile1, nodeid)
        self.assertIsNone(tile1.data[nodeid])

    def test_dataclass_roundtrip(self):
        reference = DataTypeFactory().get_instance("reference")
        list1_pk = str(List.objects.get(name="list1").pk)
        config = {"controlledList": list1_pk}
        tile_val = reference.transform_value_for_tile("label1-pref", **config)
        materialized = reference.to_python(tile_val)
        # This transformation will visit the database.
        tile_val_reparsed = reference.transform_value_for_tile(materialized, **config)
        self.assertEqual(tile_val_reparsed, tile_val)
        # This one will not.
        serialized_reference = reference.serialize(materialized)
        self.assertEqual(serialized_reference, tile_val)
        # Also test None.
        self.assertIsNone(reference.serialize(None))

    def test_transform_value_for_tile(self):
        reference = DataTypeFactory().get_instance("reference")
        list1_pk = str(List.objects.get(name="list1").pk)
        config = {"controlledList": list1_pk}

        tile_value1 = reference.transform_value_for_tile("label1-pref", **config)
        self.assertIsInstance(tile_value1, list)
        self.assertIn("uri", tile_value1[0])
        self.assertIn("labels", tile_value1[0])
        self.assertIn("list_id", tile_value1[0])

        self.assertIsNone(reference.transform_value_for_tile(None, **config))

        # Test multiple incoming values (e.g. from csv import)
        tile_value3 = reference.transform_value_for_tile(
            "label1-pref,label3-pref", **config
        )
        self.assertEqual(len(tile_value3), 2)

        # Test deterministic sorting:
        #   Force two items to have the same prefLabel in a list,
        #   expect the list item with lower sortorder to be returned
        expected_list_item_pk = str(
            ListItem.objects.get(
                list_item_values__value="label2-pref", list_id=list1_pk
            ).pk
        )
        ListItemValue.objects.filter(
            value="label3-pref", list_item_id__list_id=list1_pk
        ).update(value="label2-pref")
        tile_value2 = reference.transform_value_for_tile("label2-pref", **config)
        self.assertEqual(
            tile_value2[0]["labels"][0]["list_item_id"], expected_list_item_pk
        )

    def test_to_json(self):
        reference = DataTypeFactory().get_instance("reference")
        node = ListTests.node_using_list1
        mock_tile = self.get_mock_tile()
        representation = reference.to_json(mock_tile, node)

        self.assertEqual(
            representation["@display_value"],
            "label0-pref",
        )

        mock_tile = Tile(data={str(node.pk): None})
        self.assertEqual(reference.to_json(mock_tile, node)["@display_value"], "")

    def test_get_display_value(self):
        reference = DataTypeFactory().get_instance("reference")
        node = ListTests.node_using_list1
        mock_tile1 = self.get_mock_tile()
        labels = mock_tile1.data[str(node.pk)][0]["labels"]
        french_label = {
            **labels[0],
            "language_id": "fr",
            "value": labels[0]["value"] + "-french",
        }
        labels.append(french_label)
        self.assertEqual(reference.get_display_value(mock_tile1, node), "label0-pref")
        self.assertEqual(
            reference.get_display_value(mock_tile1, node, language="fr"),
            "label0-pref-french",
        )

        mock_tile2 = Tile(
            {
                "resourceinstance_id": "50000000-0000-0000-0000-000000000000",
                "nodegroup_id": str(node.nodegroup_id),
                "tileid": "",
                "data": {str(node.pk): None},
            }
        )
        self.assertEqual(reference.get_display_value(mock_tile2, node), "")

    def test_get_display_value_context_in_bulk(self):
        reference = DataTypeFactory().get_instance("reference")
        node = ListTests.node_using_list1
        mock_tile = self.get_mock_tile()
        node_value = mock_tile.data[str(node.pk)]
        five_identical_node_values = [node_value] * 5

        qs = reference.get_display_value_context_in_bulk(five_identical_node_values)
        with self.assertNumQueries(3):
            # 1: list items
            # 2: list item labels
            # 3: children
            self.assertEqual(len(qs), 1)
        with self.assertNumQueries(0):
            qs[0].build_select_option()

    def test_get_details(self):
        reference = DataTypeFactory().get_instance("reference")
        node = ListTests.node_using_list1
        mock_tile = self.get_mock_tile()
        details = reference.get_details(mock_tile.data[str(node.pk)])
        self.assertEqual(
            set(details[0]),
            {
                "list_item_id",
                "list_item_values",
                "display_value",
                "children",
                "sortorder",
                "uri",
            },
        )

    def test_transform_export_values(self):
        reference = DataTypeFactory().get_instance("reference")
        node = ListTests.node_using_list1
        mock_tile = self.get_mock_tile()
        node_value = mock_tile.data[str(node.pk)]

        # Export as URI
        self.assertEqual(
            reference.transform_export_values(
                node_value, concept_export_value_type="id"
            ),
            "https://archesproject.org/0",
        )
        # Export as label
        self.assertEqual(
            reference.transform_export_values(
                node_value, concept_export_value_type="label"
            ),
            "label0-pref",
        )

    def test_collects_multiple_values(self):
        reference = DataTypeFactory().get_instance("reference")
        self.assertIs(reference.collects_multiple_values(), True)

    def test_append_to_document(self):
        datatype = DataTypeFactory().get_instance("reference")
        tile = TileModel(nodegroup_id=uuid.uuid4())
        document = {"references": [], "strings": []}
        list_item_id = uuid.uuid4()
        reference = Reference(
            uri="http://example.com",
            labels=[
                ReferenceLabel(
                    id=uuid.uuid4(),
                    value="Test Label",
                    language_id="en",
                    valuetype_id="prefLabel",
                    list_item_id=list_item_id,
                )
            ],
            list_id=uuid.uuid4(),
        )
        nodevalue = datatype.serialize([reference])

        datatype.append_to_document(document, nodevalue, uuid.uuid4(), tile)

        self.assertEqual(len(document["references"]), 1)
        self.assertEqual(document["references"][0]["uri"], reference.uri)
        self.assertEqual(document["references"][0]["list_id"], reference.list_id)
        self.assertEqual(document["references"][0]["nodegroup_id"], tile.nodegroup_id)
        self.assertFalse(document["references"][0]["provisional"])

        self.assertEqual(len(document["strings"]), 1)
        self.assertEqual(document["strings"][0]["string"], reference.labels[0].value)
        self.assertEqual(document["strings"][0]["nodegroup_id"], tile.nodegroup_id)
        self.assertFalse(document["strings"][0]["provisional"])

    def test_append_search_filters(self):
        mock_node = Mock(Node)
        mock_query = Mock(Bool)
        reference = ReferenceDataType()

        # Test matching query
        mock_query.must = Mock()
        mock_filter_value = [
            {
                "uri": "https://archesproject.org/1",
                "labels": [
                    {
                        "value": "label1-pref",
                        "language_id": "en",
                        "valuetype_id": "prefLabel",
                    }
                ],
            }
        ]
        mock_value = {"op": "eq", "val": mock_filter_value}
        reference.append_search_filters(mock_value, mock_node, mock_query, Mock())
        mock_query.must.assert_called()

        # Test not matching query
        mock_query.reset_mock()
        mock_query.must_not = Mock()
        mock_query.filter = Mock()
        mock_value = {"op": "!eq", "val": mock_filter_value}
        reference.append_search_filters(mock_value, mock_node, mock_query, Mock())
        mock_query.must_not.assert_called()
        mock_query.filter.assert_called()

        # Test in_list_any
        mock_query.reset_mock()
        mock_query.should = Mock()
        mock_value = {"op": "in_list_any", "val": mock_filter_value}
        reference.append_search_filters(mock_value, mock_node, mock_query, Mock())
        mock_query.should.assert_called()

        # Test in_list_all
        mock_query.reset_mock()
        mock_query.must = Mock()
        mock_value = {"op": "in_list_all", "val": mock_filter_value}
        reference.append_search_filters(mock_value, mock_node, mock_query, Mock())
        mock_query.must.assert_called()

        # Test in_list_not
        mock_query.reset_mock()
        mock_query.must_not = Mock()
        mock_value = {"op": "in_list_not", "val": mock_filter_value}
        reference.append_search_filters(mock_value, mock_node, mock_query, Mock())
        mock_query.must_not.assert_called()

        # Test null op
        mock_query.reset_mock()
        mock_query.should = Mock()
        mock_value = {"op": "null", "val": None}
        reference.append_search_filters(mock_value, mock_node, mock_query, Mock())
        mock_query.should.assert_called()
