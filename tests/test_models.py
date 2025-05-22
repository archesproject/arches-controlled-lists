from django.test import TestCase

from arches_controlled_lists.models import List, ListItem

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
    def setUp(self):
        self.list = List.objects.create(name="Test List")
        self.parent_item = ListItem.objects.create(
            list=self.list, sortorder=0, uri="http://example.com/parent"
        )
        self.child_item_1 = ListItem.objects.create(
            list=self.list,
            parent=self.parent_item,
            sortorder=1,
            uri="http://example.com/child1",
        )
        self.child_item_2 = ListItem.objects.create(
            list=self.list,
            parent=self.parent_item,
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
