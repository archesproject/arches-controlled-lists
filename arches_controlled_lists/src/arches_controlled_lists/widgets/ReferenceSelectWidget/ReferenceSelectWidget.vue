<script setup lang="ts">
import ReferenceSelectWidgetEditor from "@/arches_controlled_lists/widgets/ReferenceSelectWidget/components/ReferenceSelectWidgetEditor.vue";
import ReferenceSelectWidgetViewer from "@/arches_controlled_lists/widgets/ReferenceSelectWidget/components/ReferenceSelectWidgetViewer.vue";

import { EDIT, VIEW } from "@/arches_controlled_lists/widgets/constants.ts";
import type { CardXNodeXWidgetData } from "@/arches_component_lab/types.ts";

import type { WidgetMode } from "@/arches_controlled_lists/widgets/types.ts";
import type { ReferenceSelectFetchedOption } from "@/arches_controlled_lists/widgets/types";

defineProps<{
    mode: WidgetMode;
    nodeAlias: string;
    graphSlug: string;
    cardXNodeXWidgetData: CardXNodeXWidgetData;
    aliasedNodeData: ReferenceSelectFetchedOption[] | undefined;
}>();

const emit = defineEmits(["update:value"]);
</script>

<template>
    <ReferenceSelectWidgetEditor
        v-if="mode === EDIT"
        :card-x-node-x-widget-data="cardXNodeXWidgetData"
        :aliased-node-data="aliasedNodeData"
        @update:value="emit('update:value', $event)"
    />
    <ReferenceSelectWidgetViewer
        v-if="mode === VIEW"    
        :card-x-node-x-widget-data="cardXNodeXWidgetData"
        :aliased-node-data="aliasedNodeData"
    />
</template>
