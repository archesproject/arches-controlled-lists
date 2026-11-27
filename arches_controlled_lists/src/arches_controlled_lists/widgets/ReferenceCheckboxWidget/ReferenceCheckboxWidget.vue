<script setup lang="ts">
import { computed, onMounted, ref, watch, watchEffect } from "vue";

import { useGettext } from "vue3-gettext";

import ReferenceCheckboxWidgetEditor from "@/arches_controlled_lists/widgets/ReferenceCheckboxWidget/components/ReferenceCheckboxWidgetEditor.vue";
import ReferenceCheckboxWidgetViewer from "@/arches_controlled_lists/widgets/ReferenceCheckboxWidget/components/ReferenceCheckboxWidgetViewer.vue";

import { EDIT, VIEW } from "@/arches_vue_components/widgets/constants.ts";
import { useLanguageStore } from "@/arches_vue_components/stores/useLanguageStore.ts";
import { buildReferenceSelectAliasedNodeData } from "@/arches_controlled_lists/datatypes/reference-select/utils.ts";

import type { Language } from "@/arches_vue_components/types";
import type {
    ReferenceSelectAliasedNodeData,
    ReferenceSelectNodeValue,
} from "@/arches_controlled_lists/datatypes/reference-select/types";
import type { ReferenceCheckboxWidgetProps } from "@/arches_controlled_lists/widgets/ReferenceCheckboxWidget/types.ts";

const { aliasedNodeData, mode, value } =
    defineProps<ReferenceCheckboxWidgetProps>();

const emit = defineEmits<{
    "update:isLoading": [isLoading: boolean];
    "update:value": [updatedValue: ReferenceSelectNodeValue[]];
    "update:aliasedNodeData": [updatedValue: ReferenceSelectAliasedNodeData];
    initialized: [updatedValue: ReferenceSelectAliasedNodeData];
    ready: [];
}>();

const { current: preferredLanguageCode } = useGettext();
const languageStore = useLanguageStore();

const systemLanguageCode = computed(
    () =>
        languageStore.languages.find((lang: Language) => lang.isdefault)
            ?.code ?? preferredLanguageCode,
);

const isEditorLoading = ref(false);

const resolvedAliasedNodeData = computed(() => {
    if (aliasedNodeData) {
        return aliasedNodeData;
    }
    return buildReferenceSelectAliasedNodeData(
        value ?? null,
        preferredLanguageCode,
        systemLanguageCode.value,
    );
});

watchEffect(() => {
    languageStore.fetchAllLanguages();
});

watch(isEditorLoading, (isLoading) => emit("update:isLoading", isLoading));

onMounted(() => {
    emit("initialized", resolvedAliasedNodeData.value);
    if (mode === VIEW) {
        emit("ready");
    }
});

function onUpdateAliasedNodeData(
    updatedAliasedNodeData: ReferenceSelectAliasedNodeData,
) {
    emit("update:aliasedNodeData", updatedAliasedNodeData);
    emit("update:value", updatedAliasedNodeData.node_value ?? []);
}
</script>

<template>
    <ReferenceCheckboxWidgetEditor
        v-if="mode === EDIT"
        :card-x-node-x-widget-data="cardXNodeXWidgetData"
        :aliased-node-data="resolvedAliasedNodeData"
        :graph-slug="graphSlug"
        :node-alias="nodeAlias"
        :system-language-code="systemLanguageCode"
        @update:is-loading="isEditorLoading = $event"
        @update:aliased-node-data="onUpdateAliasedNodeData"
        @ready="emit('ready')"
    />
    <ReferenceCheckboxWidgetViewer
        v-if="mode === VIEW"
        :aliased-node-data="resolvedAliasedNodeData"
    />
</template>
