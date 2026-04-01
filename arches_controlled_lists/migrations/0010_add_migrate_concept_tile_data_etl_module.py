from django.db import migrations
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ("arches_controlled_lists", "0009_reconfigure_migration_for_polyhierarchies"),
    ]

    def add_etl_module(apps, schema_editor):
        ETLModule = apps.get_model("models", "ETLModule")

        ETLModule.objects.update_or_create(
            etlmoduleid="a1c48dba-7e6c-4a3a-b7e5-3cc5de4439b1",
            defaults={
                "name": _("Migrate Concept Tile Data to References"),
                "description": _(
                    "Updates existing tile data from concept/concept-list format "
                    "to reference datatype format after node migration"
                ),
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
            },
        )

    def remove_etl_module(apps, schema_editor):
        ETLModule = apps.get_model("models", "ETLModule")
        ETLModule.objects.filter(
            etlmoduleid="a1c48dba-7e6c-4a3a-b7e5-3cc5de4439b1"
        ).delete()

    operations = [
        migrations.RunPython(add_etl_module, remove_etl_module),
    ]
