from datetime import datetime
import json
import logging
import uuid

from django.db import connection
from django.utils.translation import gettext as _

from arches.app.etl_modules.base_data_editor import BaseBulkEditor
from arches.app.models.models import GraphModel, Node, Value
from arches.app.models.system_settings import settings
from arches.app.utils.db_utils import dictfetchall

from arches_controlled_lists.models import ListItem

logger = logging.getLogger(__name__)


details = {
    "etlmoduleid": "a1c48dba-7e6c-4a3a-b7e5-3cc5de4439b1",
    "name": "Migrate Concept Tile Data to References",
    "description": "Updates existing tile data from concept/concept-list format to reference datatype format after node migration",
    "etl_type": "edit",
    "component": "views/components/etl_modules/migrate-concept-tile-data",
    "componentname": "migrate-concept-tile-data",
    "modulename": "migrate_concept_tile_data.py",
    "classname": "MigrateConceptTileData",
    "config": {"bgColor": "#4a8c6f", "circleColor": "#6bb38a"},
    "icon": "fa fa-exchange",
    "slug": "migrate-concept-tile-data",
    "helpsortorder": 10,
    "helptemplate": "migrate-concept-tile-data-help",
    "reversible": False,
}


class MigrateConceptTileData(BaseBulkEditor):
    def __init__(self, request=None, loadid=None):
        super().__init__(request=request, loadid=loadid)

    def get_graphs(self, request):
        """Return graphs that have reference datatype nodes (i.e. already migrated)."""
        graph_name_i18n = "name__" + settings.LANGUAGE_CODE
        graphs = (
            GraphModel.objects.filter(
                node__datatype="reference",
                isresource=True,
                source_identifier__isnull=True,
            )
            .exclude(pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID)
            .distinct()
            .order_by(graph_name_i18n)
        )
        return {"success": True, "data": graphs}

    def get_reference_nodes(self, request):
        """Return reference datatype nodes for the selected graph."""
        graphid = request.POST.get("graphid")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT n.nodeid,
                       n.alias,
                       n.config,
                       n.nodegroupid,
                       c.name AS card_name,
                       w.label AS widget_label
                FROM nodes n
                JOIN cards c ON n.nodegroupid = c.nodegroupid AND c.graphid = n.graphid
                JOIN cards_x_nodes_x_widgets w ON n.nodeid = w.nodeid AND w.cardid = c.cardid
                WHERE n.datatype = 'reference'
                  AND n.graphid = %s
                ORDER BY c.name, w.label
                """,
                [graphid],
            )
            nodes = dictfetchall(cursor)
        return {"success": True, "data": nodes}

    def _build_valueid_to_listitem_lookup(self, node_ids, controlled_list_ids):
        """
        Build a lookup dict mapping concept valueid -> ListItem tile value.

        Strategy:
        1. Get all Value records for concept valueids found in tile data
           for the given nodes. Each Value has a conceptid.
        2. For each conceptid, check if a ListItem exists with that id
           (the happy path from migrate_collections_to_controlled_lists
           where conceptid is preserved as list_item_id).
        3. If no direct match, fall back to label-based lookup using the
           Value's text and the node's controlled list.

        Returns: dict[str, list[dict]] mapping valueid -> reference tile value
        """
        # Step 1: Get all distinct concept valueids referenced in tile data
        # for these nodes. We query tiles directly.
        valueid_set = set()
        str_node_ids = [str(nid) for nid in node_ids]

        with connection.cursor() as cursor:
            for node_id in str_node_ids:
                # concept nodes store a single UUID string
                # concept-list nodes store a JSON array of UUID strings
                # After migration to reference, nodes are 'reference' datatype,
                # but we're looking for tiles that still have OLD concept data.
                # The tiledata value will be either a string UUID or list of UUID strings.
                cursor.execute(
                    """
                    SELECT DISTINCT val.value AS valueid
                    FROM tiles t,
                         jsonb_array_elements_text(
                            CASE jsonb_typeof(t.tiledata -> %(node_id)s)
                                WHEN 'array' THEN t.tiledata -> %(node_id)s
                                WHEN 'string' THEN jsonb_build_array(t.tiledata -> %(node_id)s)
                                ELSE '[]'::jsonb
                            END
                         ) AS val(value)
                    WHERE t.tiledata ? %(node_id)s
                      AND t.tiledata -> %(node_id)s IS NOT NULL
                      AND jsonb_typeof(t.tiledata -> %(node_id)s) IN ('string', 'array')
                      AND t.nodegroupid IN (
                          SELECT nodegroupid FROM nodes WHERE nodeid = %(node_id_uuid)s
                      )
                    """,
                    {"node_id": node_id, "node_id_uuid": node_id},
                )
                for row in cursor.fetchall():
                    try:
                        uuid.UUID(row[0])
                        valueid_set.add(row[0])
                    except (ValueError, TypeError):
                        continue

        if not valueid_set:
            return {}

        # Step 2: Bulk-fetch Value records for all valueids
        value_records = Value.objects.filter(
            valueid__in=valueid_set,
            valuetype__valuetype="prefLabel",
        ).select_related("concept")

        # Build conceptid -> Value mapping
        valueid_to_concept = {}
        valueid_to_text = {}
        for value_record in value_records:
            vid = str(value_record.valueid)
            valueid_to_concept[vid] = str(value_record.concept_id)
            valueid_to_text[vid] = value_record.value

        # For valueids not found as prefLabels, try any valuetype
        missing_valueids = valueid_set - set(valueid_to_concept.keys())
        if missing_valueids:
            fallback_records = Value.objects.filter(
                valueid__in=missing_valueids
            ).select_related("concept")
            for value_record in fallback_records:
                vid = str(value_record.valueid)
                valueid_to_concept[vid] = str(value_record.concept_id)
                valueid_to_text[vid] = value_record.value

        # Step 3: Bulk-fetch ListItems by conceptid (the happy path)
        all_concept_ids = set(valueid_to_concept.values())

        # Also need to know which controlled list each node points to
        node_config_lookup = {}
        for node_id in node_ids:
            node = Node.objects.get(nodeid=node_id)
            controlled_list_id = node.config.get("controlledList")
            node_config_lookup[str(node_id)] = controlled_list_id

        # Fetch all ListItems whose id matches a conceptid
        matching_list_items = (
            ListItem.objects.filter(id__in=all_concept_ids)
            .prefetch_related("list_item_values")
        )
        conceptid_to_listitem = {
            str(item.id): item for item in matching_list_items
        }

        # Step 4: Build the final lookup: valueid -> reference tile value
        valueid_to_tile_value = {}
        unresolved_valueids = []

        for valueid in valueid_set:
            concept_id = valueid_to_concept.get(valueid)
            if not concept_id:
                logger.warning(
                    "No Value record found for valueid %s", valueid
                )
                continue

            list_item = conceptid_to_listitem.get(concept_id)
            if list_item:
                valueid_to_tile_value[valueid] = list_item.build_tile_value()
            else:
                unresolved_valueids.append(valueid)

        # Step 5: Fallback - label-based lookup for unresolved valueids
        if unresolved_valueids:
            # Group unresolved by controlled list to batch lookups
            all_controlled_list_ids = set(node_config_lookup.values())
            # Bulk-fetch list items with their values for all relevant lists
            list_items_by_label = {}
            for list_id in all_controlled_list_ids:
                if not list_id:
                    continue
                items = (
                    ListItem.objects.filter(
                        list_id=list_id,
                    )
                    .prefetch_related("list_item_values")
                )
                for item in items:
                    for item_value in item.list_item_values.all():
                        key = (list_id, item_value.value)
                        if key not in list_items_by_label:
                            list_items_by_label[key] = item

            for valueid in unresolved_valueids:
                text_value = valueid_to_text.get(valueid)
                if not text_value:
                    logger.warning(
                        "Cannot resolve valueid %s: no text value found",
                        valueid,
                    )
                    continue

                # Try to find this value in any of the relevant controlled lists
                found = False
                for list_id in all_controlled_list_ids:
                    if not list_id:
                        continue
                    key = (list_id, text_value)
                    item = list_items_by_label.get(key)
                    if item:
                        valueid_to_tile_value[valueid] = item.build_tile_value()
                        found = True
                        break

                if not found:
                    logger.warning(
                        "Could not resolve valueid %s (text: '%s') to any ListItem",
                        valueid,
                        text_value,
                    )

        return valueid_to_tile_value

    def _transform_tile_data_for_node(self, tile_data, node_id, valueid_lookup):
        """
        Transform a single node's value in tile data from concept format
        to reference format.

        Concept format: "valueid-string" or ["valueid1", "valueid2"]
        Reference format: [{"uri": "...", "labels": [...], "list_id": "..."}]

        Returns the transformed value, or None if no transformation was possible.
        """
        node_id_str = str(node_id)
        current_value = tile_data.get(node_id_str)

        if current_value is None:
            return None

        # Already in reference format (list of dicts with 'uri' key)
        if isinstance(current_value, list) and current_value:
            if isinstance(current_value[0], dict) and "uri" in current_value[0]:
                return current_value

        # Normalize to list of valueid strings
        if isinstance(current_value, str):
            valueid_list = [current_value]
        elif isinstance(current_value, list):
            valueid_list = current_value
        else:
            return None

        reference_values = []
        for valueid in valueid_list:
            valueid_str = str(valueid)
            tile_value = valueid_lookup.get(valueid_str)
            if tile_value:
                reference_values.append(tile_value)
            else:
                logger.warning(
                    "Skipping valueid %s: not found in lookup", valueid_str
                )

        return reference_values if reference_values else None

    def write(self, request):
        """Execute the tile data migration (non-Celery path for now)."""
        graphid = request.POST.get("graphid")
        node_ids_raw = request.POST.get("node_ids")
        migrate_all = request.POST.get("migrate_all", "false") == "true"

        if not graphid:
            return {
                "success": False,
                "data": {
                    "title": _("Error"),
                    "message": _("No graph selected."),
                },
            }

        if migrate_all:
            target_nodes = Node.objects.filter(
                graph_id=graphid, datatype="reference"
            )
            node_ids = [str(node.nodeid) for node in target_nodes]
        elif node_ids_raw:
            node_ids = json.loads(node_ids_raw)
        else:
            return {
                "success": False,
                "data": {
                    "title": _("Error"),
                    "message": _("No nodes selected for migration."),
                },
            }

        graph_name = str(GraphModel.objects.get(pk=graphid).name)
        node_aliases = list(
            Node.objects.filter(nodeid__in=node_ids).values_list("alias", flat=True)
        )
        load_details = {
            "graph": graph_name,
            "nodes": ", ".join(node_aliases),
            "node_count": len(node_ids),
        }

        with connection.cursor() as cursor:
            event_created = self.create_load_event(cursor, load_details)
            if not event_created["success"]:
                self.log_event(cursor, "failed")
                return {"success": False, "data": event_created["message"]}

        response = self.run_load_task(
            self.userid,
            self.loadid,
            graphid,
            node_ids,
        )
        return response

    def run_load_task(self, userid, loadid, graphid, node_ids):
        """Perform the actual tile data migration."""
        with connection.cursor() as cursor:
            try:
                self.log_event_details(cursor, "done|Building value lookup...")

                # Collect controlled list IDs for the target nodes
                controlled_list_ids = set()
                for node_id in node_ids:
                    node = Node.objects.get(nodeid=node_id)
                    list_id = node.config.get("controlledList")
                    if list_id:
                        controlled_list_ids.add(list_id)

                valueid_lookup = self._build_valueid_to_listitem_lookup(
                    node_ids, controlled_list_ids
                )

                if not valueid_lookup:
                    self.log_event_details(
                        cursor,
                        "done|No concept values found requiring migration.",
                    )
                    cursor.execute(
                        """UPDATE load_event
                           SET status = %s, complete = %s, load_end_time = %s,
                               load_details = load_details::jsonb || %s::jsonb
                           WHERE loadid = %s""",
                        (
                            "indexed",
                            True,
                            datetime.now(),
                            json.dumps({"tiles_updated": 0, "nodes_processed": len(node_ids)}),
                            loadid,
                        ),
                    )
                    return {"success": True, "data": "done"}

                self.log_event_details(
                    cursor,
                    "done|Migrating tile data for %d node(s)..." % len(node_ids),
                )

                total_tiles_updated = 0

                for node_id in node_ids:
                    node_id_str = str(node_id)

                    # Find all tiles that have concept-style data for this node
                    # (string or array of strings, NOT already in reference format)
                    cursor.execute(
                        """
                        SELECT tileid, tiledata
                        FROM tiles
                        WHERE tiledata ? %(node_id)s
                          AND tiledata -> %(node_id)s IS NOT NULL
                          AND nodegroupid IN (
                              SELECT nodegroupid FROM nodes WHERE nodeid = %(node_id_uuid)s
                          )
                          AND (
                              jsonb_typeof(tiledata -> %(node_id)s) = 'string'
                              OR (
                                  jsonb_typeof(tiledata -> %(node_id)s) = 'array'
                                  AND jsonb_array_length(tiledata -> %(node_id)s) > 0
                                  AND jsonb_typeof(tiledata -> %(node_id)s -> 0) = 'string'
                              )
                          )
                        """,
                        {"node_id": node_id_str, "node_id_uuid": node_id_str},
                    )
                    tiles_to_update = cursor.fetchall()

                    for tileid, tile_data in tiles_to_update:
                        new_value = self._transform_tile_data_for_node(
                            tile_data, node_id, valueid_lookup
                        )
                        if new_value is not None:
                            tile_data[node_id_str] = new_value
                            cursor.execute(
                                """UPDATE tiles SET tiledata = %s WHERE tileid = %s""",
                                (json.dumps(tile_data), tileid),
                            )
                            total_tiles_updated += 1

                self.log_event_details(
                    cursor,
                    "done|Updated %d tile(s)." % total_tiles_updated,
                )

                cursor.execute(
                    """UPDATE load_event
                       SET status = %s, complete = %s, load_end_time = %s,
                           load_details = load_details::jsonb || %s::jsonb
                       WHERE loadid = %s""",
                    (
                        "indexed",
                        True,
                        datetime.now(),
                        json.dumps({
                            "tiles_updated": total_tiles_updated,
                            "nodes_processed": len(node_ids),
                        }),
                        loadid,
                    ),
                )

                return {"success": True, "data": "done"}

            except Exception as exc:
                logger.error(exc, exc_info=True)
                self.log_event(cursor, "failed")
                return {
                    "success": False,
                    "data": {
                        "title": _("Error"),
                        "message": str(exc),
                    },
                }


