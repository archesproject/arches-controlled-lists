import uuid
import re
from collections import defaultdict
from django.db.models import Q, prefetch_related_objects
from django.db import transaction
from rdflib import Namespace, RDF
from rdflib.namespace import SKOS, DCTERMS
from rdflib.graph import Graph
from arches.app.models import models
from arches.app.models.system_settings import settings
from arches.app.utils.skos import SKOSReader
from arches_controlled_lists.models import List, ListItem, ListItemValue

# define the ARCHES namespace
ARCHES = Namespace(settings.ARCHES_NAMESPACE_FOR_DATA_EXPORT)


class SKOSReader(SKOSReader):
    def __init__(self):
        super().__init__()
        self.lists = {}
        self.list_items = {}
        self.list_item_values = []
        self.relations = defaultdict(list)  # dict of list_item: [parent, ...]

    """
    This class extends the SKOSReader to import RDF graphs into Arches controlled lists.
    It ingests SKOS ConceptSchemes as Lists, Concepts as ListItems, and their relationships
    as ListItem parent-child relationships. It also handles ListItemValues for notes and labels.
    """

    def save_controlled_lists_from_skos(
        self,
        graph,
        overwrite_options="overwrite",  # options: ignore, duplicate, overwrite
    ):
        baseuuid = uuid.uuid4()
        allowed_languages = {}
        for lang in models.Language.objects.all():
            allowed_languages[lang.code] = lang
        default_lang = allowed_languages[settings.LANGUAGE_CODE]

        existing_lists = List.objects.all()
        existing_list_ids = [list.pk for list in existing_lists]
        existing_list_items = ListItem.objects.all()
        existing_list_item_ids = [item.pk for item in existing_list_items]
        existing_lists_to_delete = []

        # if the graph is of the type rdflib.graph.Graph
        if isinstance(graph, Graph):

            ### Lists ###
            # Search for ConceptSchemes first - these will become Lists
            for scheme, v, o in graph.triples((None, RDF.type, SKOS.ConceptScheme)):
                list_id = self.generate_uuidv5_from_subject(baseuuid, scheme)

                if list_id in existing_list_ids and overwrite_options == "ignore":
                    continue
                elif list_id in existing_list_ids and overwrite_options == "duplicate":
                    new_list = List(uuid.uuid4())
                elif list_id in existing_list_ids and overwrite_options == "overwrite":
                    existing_lists_to_delete.append(list_id)
                    new_list = List(id=list_id)
                else:
                    new_list = List(id=list_id)

                for predicate, object in graph.predicate_objects(subject=scheme):
                    # Get List name from a ConceptScheme's title element
                    if predicate == DCTERMS.title:

                        if not self.language_exists(object, allowed_languages):
                            for lang in models.Language.objects.all():
                                allowed_languages[lang.code] = lang

                        val = self.unwrapJsonLiteral(object)
                        new_list.name = val["value"]

                self.lists[scheme] = new_list

            # Create lookups for valuetypes used during Concept processing
            value_types = models.DValueType.objects.all()
            skos_value_types = value_types.filter(
                Q(namespace="skos") | Q(namespace="arches")
            )
            skos_note_and_label_types = skos_value_types.filter(
                Q(category="note") | Q(category="label")
            )
            skos_value_types = {
                valuetype.valuetype: valuetype for valuetype in skos_value_types
            }
            skos_note_and_label_types = {
                valuetype.valuetype: valuetype
                for valuetype in skos_note_and_label_types
            }

            ### List items & values ###
            # Concepts become ListItems & ListItemValues
            for concept, v, o in graph.triples((None, RDF.type, SKOS.Concept)):
                list_item_id = self.generate_uuidv5_from_subject(baseuuid, concept)

                if (
                    list_item_id in existing_list_item_ids
                    and overwrite_options == "ignore"
                ):
                    continue
                elif (
                    list_item_id in existing_list_item_ids
                    and overwrite_options == "duplicate"
                ):
                    list_item = ListItem(uuid.uuid4())
                else:
                    list_item = ListItem(id=list_item_id)

                # rdf:about is fallback URI for a concept, unless it has dcterms:identifier
                uri = self.unwrapJsonLiteral(str(concept))["value"]

                # not-null placeholder to differentiate between items with no sortorder
                # & those with sortorder in skos file
                sortorder = 999999

                for predicate, object in graph.predicate_objects(subject=concept):
                    if predicate == DCTERMS.identifier:
                        uri = self.unwrapJsonLiteral(str(object))["value"]

                    elif predicate == SKOS.inScheme:
                        list_item.list = self.lists[object]

                    elif any(
                        type in predicate for type in skos_note_and_label_types.keys()
                    ):
                        if not self.language_exists(object, allowed_languages):
                            for lang in models.Language.objects.all():
                                allowed_languages[lang.code] = lang

                        object_language = (
                            allowed_languages[object.language] or default_lang
                        )
                        relation_or_value_type = predicate.replace(SKOS, "").replace(
                            ARCHES, ""
                        )
                        list_item_value = ListItemValue(
                            list_item=list_item,
                            valuetype=skos_value_types.get(relation_or_value_type),
                            language=object_language,
                            value=self.unwrapJsonLiteral(str(object))["value"],
                        )
                        self.list_item_values.append(list_item_value)

                    elif predicate == SKOS.broader:
                        parent = self.generate_uuidv5_from_subject(baseuuid, object)
                        self.relations[list_item].append(parent)
                    elif predicate == SKOS.narrower:
                        child = self.generate_uuidv5_from_subject(baseuuid, object)
                        self.relations[child].append(list_item)

                    elif predicate == ARCHES.sortorder:
                        sortorder = int(self.unwrapJsonLiteral(str(object))["value"])

                list_item.uri = uri
                list_item.sortorder = sortorder
                self.list_items[list_item_id] = list_item

            with transaction.atomic():
                List.objects.filter(pk__in=existing_lists_to_delete).delete()

                List.objects.bulk_create(self.lists.values())
                new_list_items = ListItem.objects.bulk_create(self.list_items.values())
                ListItemValue.objects.bulk_create(self.list_item_values)

                duplicate_list_items = []
                duplicate_list_items_values = []
                list_items_to_update = []

                ### Relationships ###
                for child, parents in self.relations.items():
                    if not isinstance(child, ListItem):
                        child = self.list_items[child]
                    parents = [
                        (
                            self.list_items[parent]
                            if not isinstance(parent, ListItem)
                            else parent
                        )
                        for parent in parents
                    ]
                    if len(parents) >= 1:
                        child.parent = parents[0]
                        list_items_to_update.append(child)

                        if len(parents) > 1:
                            new_children, new_children_values = (
                                child.duplicate_under_new_parent(parents[1:])
                            )
                            duplicate_list_items.extend(new_children)
                            duplicate_list_items_values.extend(new_children_values)

                ListItem.objects.bulk_update(list_items_to_update, ["parent"])
                new_list_items.extend(
                    ListItem.objects.bulk_create(duplicate_list_items)
                )
                ListItemValue.objects.bulk_create(duplicate_list_items_values)

                ### Sort order ###
                prefetch_related_objects(
                    new_list_items, "children", "children__list_item_values"
                )

                list_items_to_update = []
                root_items = []
                for parent in new_list_items:
                    list_items_to_update.extend(parent.sort_children(default_lang.code))
                    if parent.parent is None:
                        root_items.append(parent)

                if root_items:
                    list_items_to_update.extend(
                        root_items[0].sort_siblings(default_lang.code, root_items)
                    )

                ListItem.objects.bulk_update(list_items_to_update, ["sortorder"])

    def generate_uuidv5_from_subject(self, baseuuid, subject):
        uuidregx = re.compile(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        )
        matches = uuidregx.search(str(subject))
        if matches:
            return uuid.UUID(matches.group(0))
        else:
            return uuid.uuid5(baseuuid, str(subject))
