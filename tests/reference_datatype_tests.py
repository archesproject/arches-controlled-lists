import uuid
from types import SimpleNamespace

from django.test import TestCase
from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models.tile import Tile
from arches_controlled_lists.models import List, ListItem, ListItemValue

from tests.test_views import ListTests

# these tests can be run from the command line via
# python manage.py test tests.reference_datatype_tests --settings="tests.test_settings"


class ReferenceDataTypeTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        return ListTests.setUpTestData()

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

    def test_to_representation(self):
        reference = DataTypeFactory().get_instance("reference")
        list_item_value = ListItemValue.objects.get(
            value="label1-pref", list_item__list__name="list1"
        )
        config = {"controlledList": str(list_item_value.list_item.list_id)}
        tile_val = reference.transform_value_for_tile("label1-pref", **config)

        representation = reference.to_representation(tile_val)

        self.assertEqual(
            representation,
            [
                {
                    "list_item_id": str(list_item_value.list_item.pk),
                    "display_value": "label1-pref",
                }
            ],
        )

        self.assertIsNone(reference.to_representation(None))

    def test_get_display_value(self):
        reference = DataTypeFactory().get_instance("reference")
        mock_node = SimpleNamespace(nodeid="72048cb3-adbc-11e6-9ccf-14109fd34195")
        mock_tile1 = Tile(
            {
                "resourceinstance_id": "40000000-0000-0000-0000-000000000000",
                "parenttile_id": "",
                "nodegroup_id": "72048cb3-adbc-11e6-9ccf-14109fd34195",
                "tileid": "",
                "data": {
                    "72048cb3-adbc-11e6-9ccf-14109fd34195": [
                        {
                            "uri": "https://lingo.dev.fargeo.com/plugins/controlled-list-manager/item/9baf3cd5-33d4-4fbc-b1d1-a2d218732f1e",
                            "labels": [
                                {
                                    "id": "ea5c8af7-9933-4356-b537-0330c9da4690",
                                    "value": "identifier",
                                    "language_id": "en",
                                    "list_item_id": "d8ba08f9-b265-4288-9412-857c77fe2581",
                                    "valuetype_id": "prefLabel",
                                },
                                {
                                    "id": "ea5c8af7-9933-4356-b537-0330c9da4690",
                                    "value": "identificateur",
                                    "language_id": "fr",
                                    "list_item_id": "d8ba08f9-b265-4288-9412-857c77fe2692",
                                    "valuetype_id": "prefLabel",
                                },
                            ],
                            "list_id": "a8da34eb-575b-498c-ada7-161ee745fd16",
                        }
                    ]
                },
            }
        )
        self.assertEqual(
            reference.get_display_value(mock_tile1, mock_node), "identifier"
        )
        self.assertEqual(
            reference.get_display_value(mock_tile1, mock_node, language="fr"),
            "identificateur",
        )

        mock_tile2 = Tile(
            {
                "resourceinstance_id": "50000000-0000-0000-0000-000000000000",
                "parenttile_id": "",
                "nodegroup_id": "72048cb3-adbc-11e6-9ccf-14109fd34195",
                "tileid": "",
                "data": {"72048cb3-adbc-11e6-9ccf-14109fd34195": None},
            }
        )
        self.assertEqual(reference.get_display_value(mock_tile2, mock_node), "")

    def test_collects_multiple_values(self):
        reference = DataTypeFactory().get_instance("reference")
        self.assertIs(reference.collects_multiple_values(), True)

    def test_append_to_document(self):
        datatype = DataTypeFactory().get_instance("reference")
        tile = type("Tile", (object,), {"nodegroup_id": uuid.uuid4()})
        document = {"references": [], "strings": []}
        list_item_id = uuid.uuid4()
        reference = {
            "uri": "http://example.com",
            "labels": [
                {
                    "id": uuid.uuid4(),
                    "value": "Test Label",
                    "language_id": "en",
                    "valuetype_id": "prefLabel",
                    "list_item_id": list_item_id,
                }
            ],
            "list_id": uuid.uuid4(),
        }
        nodevalue = [reference]

        datatype.append_to_document(document, nodevalue, uuid.uuid4(), tile)

        self.assertEqual(len(document["references"]), 1)
        self.assertEqual(document["references"][0]["uri"], reference["uri"])
        self.assertEqual(document["references"][0]["list_id"], reference["list_id"])
        self.assertEqual(document["references"][0]["nodegroup_id"], tile.nodegroup_id)

        self.assertEqual(len(document["strings"]), 1)
        self.assertEqual(
            document["strings"][0]["string"], reference["labels"][0]["value"]
        )
        self.assertEqual(document["strings"][0]["nodegroup_id"], tile.nodegroup_id)
        self.assertFalse(document["strings"][0]["provisional"])
