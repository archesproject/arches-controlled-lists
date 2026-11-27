import uuid

from django.db import migrations


CHECKBOX_WIDGET_ID = "1cce9f4a-5ba2-4f7e-8d1c-b6a8294e3f10"


def create_reference_checkbox_widget(apps, schema_editor):
    schema_editor.execute(
        """
        INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
        VALUES (
            %s,
            'reference-checkbox-widget',
            'views/components/widgets/reference-checkbox',
            'reference',
            '{"placeholder": "", "i18n_properties": ["placeholder"]}'
        )
        ON CONFLICT DO NOTHING;
        """,
        [CHECKBOX_WIDGET_ID],
    )

    WidgetMapping = apps.get_model("arches_vue_components", "WidgetMapping")
    WidgetMapping.objects.create(
        id=uuid.uuid4(),
        widget_id=CHECKBOX_WIDGET_ID,
        component="arches_controlled_lists/widgets/ReferenceCheckboxWidget/ReferenceCheckboxWidget.vue",
    )


def revert_reference_checkbox_widget(apps, schema_editor):
    WidgetMapping = apps.get_model("arches_vue_components", "WidgetMapping")
    WidgetMapping.objects.filter(widget_id=CHECKBOX_WIDGET_ID).delete()

    schema_editor.execute(
        "DELETE FROM widgets WHERE widgetid = %s;",
        [CHECKBOX_WIDGET_ID],
    )


class Migration(migrations.Migration):
    dependencies = [
        ("arches_controlled_lists", "0012_fix_whitespace_v2"),
        ("arches_vue_components", "0002_populate_widget_mappings"),
    ]

    operations = [
        migrations.RunPython(
            create_reference_checkbox_widget,
            revert_reference_checkbox_widget,
        ),
    ]
