<script setup lang="ts">
import ReferenceSelectWidgetEditor from "@/arches_controlled_lists/widgets/ReferenceSelectWidget/components/ReferenceSelectWidgetEditor.vue";
import ReferenceSelectWidgetViewer from "@/arches_controlled_lists/widgets/ReferenceSelectWidget/components/ReferenceSelectWidgetViewer.vue";

import { EDIT, VIEW } from "@/arches_component_lab/widgets/constants.ts";

import type { WidgetMode } from "@/arches_component_lab/widgets/types.ts";

import type {
    ReferenceSelectDatatypeCardXNodeXWidgetData,
    ReferenceSelectNodeValue,
} from "@/arches_controlled_lists/datatypes/reference-select/types.ts";

const { mode, nodeAlias, graphSlug, cardXNodeXWidgetData, nodeValue } =
    defineProps<{
        mode: WidgetMode;
        nodeAlias: string;
        graphSlug: string;
        cardXNodeXWidgetData: ReferenceSelectDatatypeCardXNodeXWidgetData;
        nodeValue: ReferenceSelectNodeValue[] | null;
    }>();

const emit = defineEmits(["update:value"]);
</script>

<template>
    <ReferenceSelectWidgetEditor
        v-if="mode === EDIT"
        :card-x-node-x-widget-data="cardXNodeXWidgetData"
        :node-value="nodeValue"
        :graph-slug="graphSlug"
        :node-alias="nodeAlias"
        @update:value="emit('update:value', $event)"
    />
    <ReferenceSelectWidgetViewer
        v-if="mode === VIEW"
        :node-value="nodeValue"
    />
</template>
