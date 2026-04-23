"""MCP tools for arches-controlled-lists.

Registered automatically by :class:`ArchesControlledListsConfig.register_mcp_tools`
when the Arches MCP server starts.  All tools are read-only.

Tools
-----
* ``list_controlled_lists``   — paginated list of all controlled lists.
* ``get_controlled_list``     — one list with its full item hierarchy.
* ``search_list_items``       — find items by label text.
"""

from __future__ import annotations

from typing import Any, Optional

from arches.mcp.helpers import (
    async_orm_tool,
    build_list_envelope,
    clamp_limit,
    coerce_uuid,
    DEFAULT_LIMIT,
)


# --------------------------------------------------------------------------- #
#  Serialisers (private to this module)                                        #
# --------------------------------------------------------------------------- #


def _serialize_list(lst) -> dict[str, Any]:
    return {
        "id": str(lst.id),
        "name": lst.name,
        "dynamic": lst.dynamic,
        "searchable": lst.searchable,
    }


def _serialize_list_item_value(v) -> dict[str, Any]:
    return {
        "id": str(v.id),
        "valuetype": v.valuetype_id,
        "language": v.language_id,
        "value": v.value,
    }


def _serialize_list_item(item, *, include_children: bool = True) -> dict[str, Any]:
    """Serialise a ListItem.

    When *include_children* is True the children are recursively serialised so
    the caller gets the full hierarchy in one call.  Set it to False when the
    caller is already iterating over a flat queryset.
    """
    data: dict[str, Any] = {
        "id": str(item.id),
        "list_id": str(item.list_id),
        "uri": item.uri,
        "sortorder": item.sortorder,
        "guide": item.guide,
        "parent_id": str(item.parent_id) if item.parent_id else None,
        "values": [
            _serialize_list_item_value(v)
            for v in item.list_item_values.all()
            if v.valuetype_id != "image"
        ],
    }
    if include_children:
        data["children"] = [
            _serialize_list_item(child, include_children=True)
            for child in item.children.all()
        ]
    return data


# --------------------------------------------------------------------------- #
#  Tool registration                                                            #
# --------------------------------------------------------------------------- #


def register(server) -> None:
    """Register all arches-controlled-lists MCP tools on *server*."""

    @server.tool()
    @async_orm_tool
    def list_controlled_lists(
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List all controlled lists defined in this Arches instance.

        Returns a paginated collection of list metadata (id, name, dynamic,
        searchable).  Use ``get_controlled_list`` to fetch a specific list
        with its full item hierarchy.
        """
        from arches_controlled_lists.models import List as ControlledList

        qs = ControlledList.objects.order_by("name")
        total = qs.count()
        _limit = clamp_limit(limit)
        qs = qs[offset : offset + _limit]
        return build_list_envelope(
            total, offset, _limit, "lists", [_serialize_list(lst) for lst in qs]
        )

    @server.tool()
    @async_orm_tool
    def get_controlled_list(list_id: str) -> dict[str, Any]:
        """Return a controlled list together with its full item hierarchy.

        ``list_id`` is a UUID string.  Use ``list_controlled_lists`` first if
        you do not know the id.

        Items are returned as a tree: each item has a ``children`` key
        containing its child items recursively.  Items with ``guide=True``
        are organisational nodes that cannot be selected as values.
        """
        from arches_controlled_lists.models import List as ControlledList, ListItem

        lid = coerce_uuid(list_id, "list_id")
        lst = ControlledList.objects.get(pk=lid)

        # Prefetch values and children for the whole tree in two queries.
        root_items = (
            ListItem.objects.filter(list_id=lid, parent__isnull=True)
            .prefetch_related(
                "list_item_values",
                "children__list_item_values",
                "children__children__list_item_values",
                "children__children__children__list_item_values",
            )
            .order_by("sortorder")
        )

        return {
            "list": _serialize_list(lst),
            "items": [_serialize_list_item(item) for item in root_items],
        }

    @server.tool()
    @async_orm_tool
    def search_list_items(
        text: str,
        list_id: Optional[str] = None,
        language: Optional[str] = None,
        valuetype: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search controlled-list items by label text.

        Performs a case-insensitive substring match against ``ListItemValue``
        records.  Optionally restrict the search to a specific list
        (``list_id``), language code (e.g. ``"en"``), or value type
        (e.g. ``"prefLabel"``).

        Each result includes the matched value, its item id, the item's
        parent id, and the list id so callers can navigate to the full item
        via ``get_controlled_list``.
        """
        from arches_controlled_lists.models import ListItemValue

        qs = ListItemValue.objects.filter(value__icontains=text).select_related(
            "list_item"
        )
        if list_id:
            qs = qs.filter(list_item__list_id=coerce_uuid(list_id, "list_id"))
        if language:
            qs = qs.filter(language_id=language)
        if valuetype:
            qs = qs.filter(valuetype_id=valuetype)
        else:
            # Exclude image-type values from search results by default.
            qs = qs.exclude(valuetype_id="image")

        qs = qs.order_by("value")
        total = qs.count()
        _limit = clamp_limit(limit)
        qs = qs[offset : offset + _limit]
        return build_list_envelope(
            total,
            offset,
            _limit,
            "matches",
            [
                {
                    "value": v.value,
                    "valuetype": v.valuetype_id,
                    "language": v.language_id,
                    "item_id": str(v.list_item_id),
                    "list_id": str(v.list_item.list_id),
                    "parent_id": (
                        str(v.list_item.parent_id) if v.list_item.parent_id else None
                    ),
                }
                for v in qs
            ],
        )
