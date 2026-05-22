<script setup lang="ts">
import { computed } from "vue";

import ReferenceSelectWidgetEditor from "@/arches_controlled_lists/widgets/ReferenceSelectWidget/components/ReferenceSelectWidgetEditor.vue";
import ReferenceSelectWidgetViewer from "@/arches_controlled_lists/widgets/ReferenceSelectWidget/components/ReferenceSelectWidgetViewer.vue";

import { EDIT, VIEW } from "@/arches_component_lab/widgets/constants.ts";

import type { WidgetMode } from "@/arches_component_lab/widgets/types.ts";
import type {
    ReferenceSelectAliasedNodeData,
    ReferenceSelectDatatypeCardXNodeXWidgetData,
    ReferenceSelectNodeValue,
} from "@/arches_controlled_lists/datatypes/reference-select/types.ts";

const { aliasedNodeData, value } = defineProps<{
    mode: WidgetMode;
    nodeAlias?: string;
    graphSlug?: string;
    cardXNodeXWidgetData?: ReferenceSelectDatatypeCardXNodeXWidgetData;
    aliasedNodeData?: ReferenceSelectAliasedNodeData | null;
    value?: ReferenceSelectNodeValue[] | null;
}>();

const emit = defineEmits<{
    "update:isLoading": [isLoading: boolean];
    "update:value": [updatedValue: ReferenceSelectNodeValue[]];
    "update:aliasedNodeData": [updatedValue: ReferenceSelectAliasedNodeData];
}>();

// aliasedNodeData !== undefined means the caller passed it (even if null);
// undefined means the prop was omitted, so fall back to the raw value.
const resolvedNodeValue = computed<ReferenceSelectNodeValue[] | null>(() => {
    if (aliasedNodeData !== undefined) {
        return aliasedNodeData?.node_value ?? null;
    }
    return value ?? null;
});
</script>

<template>
    <ReferenceSelectWidgetEditor
        v-if="mode === EDIT"
        :card-x-node-x-widget-data="cardXNodeXWidgetData"
        :value="resolvedNodeValue"
        :graph-slug="graphSlug"
        :node-alias="nodeAlias"
        @update:is-loading="emit('update:isLoading', $event)"
        @update:value="emit('update:value', $event)"
        @update:aliased-node-data="emit('update:aliasedNodeData', $event)"
    />
    <ReferenceSelectWidgetViewer
        v-if="mode === VIEW"
        :value="resolvedNodeValue"
        :aliased-node-data="aliasedNodeData"
    />
</template>
