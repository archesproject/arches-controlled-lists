from unittest.mock import MagicMock, patch
from django.test import TestCase

from arches_controlled_lists.search.references_es_mapping_modifier import (
    ReferencesEsMappingModifier,
)
from arches.app.search.elasticsearch_dsl_builder import Bool, Match, Nested, Terms


class TestReferencesEsMappingModifier(TestCase):

    @patch("arches_controlled_lists.models.ListItem.objects.get")
    def test_add_search_filter(self, mock_get):
        # Mock ListItem and its methods
        mock_item = MagicMock()
        mock_item.get_child_uris.return_value = ["uri1", "uri2"]
        mock_get.return_value = mock_item

        # Mock search_query
        search_query = MagicMock()

        # Test data
        term = {"type": "reference", "value": "test_value", "inverted": False}
        permitted_nodegroups = ["nodegroup1", "nodegroup2"]
        include_provisional = False

        # Call the method
        ReferencesEsMappingModifier.add_search_filter(
            search_query, term, permitted_nodegroups, include_provisional
        )

        # Assertions
        mock_get.assert_called_once_with(pk="test_value")
        mock_item.get_child_uris.assert_called_once_with(uris=[])
        search_query.filter.assert_called()
        search_query.must_not.assert_not_called()

    def test_get_mapping_property(self):
        self.assertEqual(
            ReferencesEsMappingModifier.get_mapping_property(), "references"
        )

    def test_get_mapping_definition(self):
        expected_definition = {
            "type": "nested",
            "properties": {
                "id": {"type": "keyword"},
                "uri": {"type": "keyword"},
                "list_id": {"type": "keyword"},
                "nodegroup_id": {"type": "keyword"},
            },
        }
        self.assertEqual(
            ReferencesEsMappingModifier.get_mapping_definition(), expected_definition
        )

    @patch("arches_controlled_lists.models.ListItem.objects.get")
    def test_add_search_filter_inverted(self, mock_get):
        # Mock ListItem and its methods
        mock_item = MagicMock()
        mock_item.get_child_uris.return_value = ["uri1", "uri2"]
        mock_get.return_value = mock_item

        # Mock search_query
        search_query = MagicMock()

        # Test data
        term = {"type": "reference", "value": "test_value", "inverted": True}
        permitted_nodegroups = ["nodegroup1", "nodegroup2"]
        include_provisional = False

        # Call the method
        ReferencesEsMappingModifier.add_search_filter(
            search_query, term, permitted_nodegroups, include_provisional
        )

        # Assertions
        mock_get.assert_called_once_with(pk="test_value")
        mock_item.get_child_uris.assert_called_once_with(uris=[])
        search_query.must_not.assert_called()
        search_query.filter.assert_not_called()
