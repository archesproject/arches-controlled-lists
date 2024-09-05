from arches.app.models.models import CardXNodeXWidget, Node, GraphModel, Value
from arches_references.models import List
from django.core.management.base import BaseCommand
from django.db import models
from django.db.models.expressions import CombinedExpression
from django.db.models.fields.json import KT
from django.db.models.functions import Cast


class Command(BaseCommand):
    """
    Commands for running controlled list operations

    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--operation",
            action="store",
            dest="operation",
            required=True,
            choices=[
                "migrate_collections_to_controlled_lists",
                "migrate_graph_to_reference_datatype",
            ],
            help="The operation to perform",
        )

        parser.add_argument(
            "-co",
            "--collections",
            action="store",
            dest="collections_to_migrate",
            nargs="*",
            help="One or more collections to migrate to controlled lists",
        )

        parser.add_argument(
            "-ho",
            "--host",
            action="store",
            dest="host",
            default="http://localhost:8000/plugins/controlled-list-manager/item/",
            help="Provide a host for URI generation. Default is localhost",
        )

        parser.add_argument(
            "-ow",
            "--overwrite",
            action="store_true",
            dest="overwrite",
            default=False,
            help="Overwrite the entire controlled list and its list items/values. Default false.",
        )

        parser.add_argument(
            "-psl",
            "--preferred_sort_language",
            action="store",
            dest="preferred_sort_language",
            default="en",
            help="The language to use for sorting preferred labels. Default 'en'",
        )

        parser.add_argument(
            "-g",
            "--graph",
            action="store",
            dest="graph",
            help="The graphid which associated concept nodes will be migrated to use the reference datatype",
        )

    def handle(self, *args, **options):
        if options["operation"] == "migrate_collections_to_controlled_lists":
            self.migrate_collections_to_controlled_lists(
                collections_to_migrate=options["collections_to_migrate"],
                host=options["host"],
                overwrite=options["overwrite"],
                preferred_sort_language=options["preferred_sort_language"],
            )
        elif options["operation"] == "migrate_graph_to_reference_datatype":
            self.migrate_graph_to_reference_datatype(options["graph"])

    def migrate_collections_to_controlled_lists(
        self,
        collections_to_migrate,
        host,
        overwrite,
        preferred_sort_language,
    ):
        """
        Uses a postgres function to migrate collections to controlled lists

        Example usage:
            python manage.py controlled_lists
                -o migrate_collections_to_controlled_lists
                -co 'Johns list' 'Getty AAT'
                -ho 'http://localhost:8000/plugins/controlled-list-manager/item/'
                -psl 'fr'
                -ow
        """

        collections_in_db = list(
            Value.objects.filter(
                value__in=collections_to_migrate,
                valuetype__in=["prefLabel", "identifier"],
                concept__nodetype="Collection",
            ).values_list("value", flat=True)
        )

        failed_collections = [
            collection
            for collection in collections_to_migrate
            if collection not in collections_in_db
        ]

        if len(failed_collections) > 0:
            self.stderr.write(
                "Failed to find the following collections in the database: %s"
                % ", ".join(failed_collections)
            )

        if len(collections_in_db) > 0:
            from django.db import connection

            cursor = connection.cursor()
            cursor.execute(
                """
                select * from __arches_migrate_collections_to_clm(
                    ARRAY[%s], %s, %s::boolean, %s
                );
                """,
                [collections_in_db, host, overwrite, preferred_sort_language],
            )
            result = cursor.fetchone()
            self.stdout.write(result[0])

    def migrate_graph_to_reference_datatype(self, graph):
        future_graph = GraphModel.objects.get(source_identifier=graph)
        nodes = (
            Node.objects.filter(
                graph_id=future_graph.graphid,
                datatype__in=["concept", "concept-list"],
                is_immutable=False,
            )
            .annotate(
                collection_id=Cast(
                    KT("config__rdmCollection"),
                    output_field=models.UUIDField(),
                )
            )
            .prefetch_related("cardxnodexwidget_set")
        )

        existing_list_ids = List.objects.all().values_list("id", flat=True)

        errors = []
        for node in nodes:
            if node.collection_id in existing_list_ids:
                if node.datatype == "concept":
                    node.config = {
                        "multiValue": False,
                        "controlledList": node.collection_id.__str__(),
                    }
                elif node.datatype == "concept-list":
                    node.config = {
                        "multiValue": True,
                        "controlledList": node.collection_id.__str__(),
                    }
                node.datatype = "reference"
                node.save()

                cross_records = (
                    node.cardxnodexwidget_set.annotate(
                        config_without_i18n=Cast(
                            models.F("config"),
                            output_field=models.JSONField(),
                        )
                    )
                    .annotate(
                        without_default=CombinedExpression(
                            models.F("config_without_i18n"),
                            "-",
                            models.Value(
                                "defaultValue", output_field=models.CharField()
                            ),
                            output_field=models.JSONField(),
                        )
                    )
                    .annotate(
                        without_default_and_options=CombinedExpression(
                            models.F("without_default"),
                            "-",
                            models.Value("options", output_field=models.CharField()),
                            output_field=models.JSONField(),
                        )
                    )
                )
                for cross_record in cross_records:
                    cross_record.config = cross_record.without_default_and_options
                    cross_record.save()
            elif node.collection_id not in existing_list_ids:
                errors.append(
                    {"node_alias": node.alias, "collection_id": node.collection_id}
                )

        if errors:
            self.stderr.write(
                "The following collections for the associated nodes have not been migrated to controlled lists: {0}".format(
                    errors
                )
            )
        else:
            future_graph.has_unpublished_changes = True
            self.stdout.write(
                "All concept nodes for the {0} graph have been successfully migrated to reference datatype".format(
                    future_graph.name
                )
            )
