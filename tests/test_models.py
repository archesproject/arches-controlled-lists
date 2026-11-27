import time

from django.conf import settings
from django.test import TestCase

from arches.app.models.models import DValueType, Language
from arches.app.search.elasticsearch_dsl_builder import Query
from arches.app.search.search_engine_factory import SearchEngineInstance
from arches_controlled_lists.models import List, ListItem, ListItemValue

# these tests can be run from the command line via
# python manage.py test tests.test_models --settings="tests.test_settings"


class ListItemTests(TestCase):
    def test_uri_generation_guards_against_failure(self):
        # Don't bother setting up a list.
        item = ListItem(sortorder=0)
        item.id = None

        with self.assertRaises(RuntimeError):
            item.clean()

        item.full_clean(exclude={"list"})
        self.assertIsNotNone(item.uri)


class ListItemGetChildUrisTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.list = List.objects.create(name="Test List")
        cls.parent_item = ListItem.objects.create(
            list=cls.list, sortorder=0, uri="http://example.com/parent"
        )
        cls.child_item_1 = ListItem.objects.create(
            list=cls.list,
            parent=cls.parent_item,
            sortorder=1,
            uri="http://example.com/child1",
        )
        cls.child_item_2 = ListItem.objects.create(
            list=cls.list,
            parent=cls.parent_item,
            sortorder=2,
            uri="http://example.com/child2",
        )

    def test_get_child_uris_includes_parent_and_children(self):
        uris = self.parent_item.get_child_uris()
        self.assertIn(self.parent_item.uri, uris)
        self.assertIn(self.child_item_1.uri, uris)
        self.assertIn(self.child_item_2.uri, uris)

    def test_get_child_uris_empty_for_item_without_children(self):
        uris = self.child_item_1.get_child_uris()
        self.assertEqual(uris, [self.child_item_1.uri])


class ListItemBuildSelectOptionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pref_label = DValueType.objects.get(valuetype="prefLabel")
        cls.first_language = Language.objects.first()

        cls.list = List.objects.create(name="Test List")

        cls.guide_item = ListItem.objects.create(
            list=cls.list,
            sortorder=0,
            uri="http://example.com/guide",
            guide=True,
        )
        ListItemValue.objects.create(
            list_item=cls.guide_item,
            valuetype=cls.pref_label,
            language=cls.first_language,
            value="Section Header",
        )

        cls.selectable_item = ListItem.objects.create(
            list=cls.list,
            sortorder=1,
            uri="http://example.com/selectable",
            guide=False,
        )
        ListItemValue.objects.create(
            list_item=cls.selectable_item,
            valuetype=cls.pref_label,
            language=cls.first_language,
            value="Selectable Option",
        )

        cls.child_item = ListItem.objects.create(
            list=cls.list,
            parent=cls.guide_item,
            sortorder=0,
            uri="http://example.com/child",
            guide=False,
        )
        ListItemValue.objects.create(
            list_item=cls.child_item,
            valuetype=cls.pref_label,
            language=cls.first_language,
            value="Child Option",
        )

    def test_guide_item_includes_guide_true(self):
        result = self.guide_item.build_select_option()
        self.assertIn("guide", result)
        self.assertTrue(result["guide"])

    def test_selectable_item_includes_guide_false(self):
        result = self.selectable_item.build_select_option()
        self.assertIn("guide", result)
        self.assertFalse(result["guide"])

    def test_children_also_include_guide_field(self):
        result = self.guide_item.build_select_option()
        self.assertEqual(len(result["children"]), 1)
        child = result["children"][0]
        self.assertIn("guide", child)
        self.assertFalse(child["guide"])

    def test_required_fields_present(self):
        result = self.selectable_item.build_select_option()
        for field in (
            "list_item_id",
            "uri",
            "guide",
            "list_item_values",
            "display_value",
            "sortorder",
            "children",
        ):
            self.assertIn(field, result)


class ListIndexTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.list = List.objects.create(name="Test List", searchable=True)
        cls.list_item = ListItem.objects.create(
            list=cls.list, sortorder=0, uri="http://example.com/item"
        )
        cls.preflabel_value = ListItemValue.objects.create(
            list_item=cls.list_item,
            valuetype=DValueType.objects.get(valuetype="prefLabel"),
            language_id="en",
            value="Test PrefLabel",
        )
        cls.altlabel_value = ListItemValue.objects.create(
            list_item=cls.list_item,
            valuetype=DValueType.objects.get(valuetype="altLabel"),
            language_id="en",
            value="Test AltLabel",
        )

    def test_index_list_called_on_save(self):
        self.list.save()
        time.sleep(2)  # Allow time for indexing to complete
        query = Query(SearchEngineInstance)
        count = query.se.count(index=settings.REFERENCES_INDEX_NAME)
        self.assertEqual(count, 2)

    def test_delete_list_index_called_on_delete(self):
        self.list.save()
        time.sleep(2)  # Allow time for indexing to complete
        query = Query(SearchEngineInstance)
        count = query.se.count(index=settings.REFERENCES_INDEX_NAME)
        self.assertEqual(count, 2)
        self.list.delete()
        time.sleep(2)  # Allow time for index deletion to complete
        query = Query(SearchEngineInstance)
        count = query.se.count(index=settings.REFERENCES_INDEX_NAME)
        self.assertEqual(count, 0)

    def test_delete_list_item_index_called_on_delete(self):
        self.list.save()
        time.sleep(2)  # Allow time for indexing to complete
        query = Query(SearchEngineInstance)
        count = query.se.count(index=settings.REFERENCES_INDEX_NAME)
        self.assertEqual(count, 2)
        self.list_item.delete()
        time.sleep(2)  # Allow time for index deletion to complete
        query = Query(SearchEngineInstance)
        count = query.se.count(index=settings.REFERENCES_INDEX_NAME)
        self.assertEqual(count, 0)

    def test_delete_list_item_value_index_called_on_delete(self):
        self.list.save()
        time.sleep(2)  # Allow time for indexing to complete
        query = Query(SearchEngineInstance)
        count = query.se.count(index=settings.REFERENCES_INDEX_NAME)
        self.assertEqual(count, 2)
        self.altlabel_value.delete()
        time.sleep(2)  # Allow time for index deletion to complete
        query = Query(SearchEngineInstance)
        count = query.se.count(index=settings.REFERENCES_INDEX_NAME)
        self.assertEqual(count, 1)
