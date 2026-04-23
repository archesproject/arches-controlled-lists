from django.apps import AppConfig, apps


class ArchesControlledListsConfig(AppConfig):
    name = "arches_controlled_lists"
    verbose_name = "Arches Controlled Lists"
    is_arches_application = True

    def ready(self):
        if apps.get_app_config("arches_querysets"):
            from arches_controlled_lists.datatypes.datatypes import (
                ReferenceField,
                ReferenceSerializer,
            )
            from arches_querysets.rest_framework.serializers import (
                TileAliasedDataSerializer,
            )

            TileAliasedDataSerializer.register_custom_datatype_field(
                ReferenceField, ReferenceSerializer
            )

    def register_mcp_tools(self, server) -> None:
        """Register arches-controlled-lists MCP tools on *server*.

        Called automatically by :func:`arches.mcp.server.register_extensions`
        when the Arches MCP server starts.
        """
        from arches_controlled_lists.mcp import register

        register(server)
