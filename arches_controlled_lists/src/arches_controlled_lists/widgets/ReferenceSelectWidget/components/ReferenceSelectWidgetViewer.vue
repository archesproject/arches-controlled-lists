<script setup lang="ts">
import { computed, onMounted } from "vue";

import { useGettext } from "vue3-gettext";

import arches from "arches";

import { buildReferenceSelectAliasedNodeData } from "@/arches_controlled_lists/datatypes/reference-select/utils.ts";

import type { Language } from "@/arches_controlled_lists/types.ts";
import type { ReferenceSelectAliasedNodeData } from "@/arches_controlled_lists/datatypes/reference-select/types";

const { aliasedNodeData } = defineProps<{
    aliasedNodeData?: ReferenceSelectAliasedNodeData | null;
}>();

const emit = defineEmits<{
    initialized: [updatedValue: ReferenceSelectAliasedNodeData];
}>();

const { current: preferredLanguageCode } = useGettext();
const systemLanguageCode =
    (arches.languages as Language[]).find((lang) => lang.isdefault)?.code ??
    preferredLanguageCode;

const displayValue = computed(() => aliasedNodeData?.display_value);

onMounted(() => {
    emit(
        "initialized",
        aliasedNodeData ??
            buildReferenceSelectAliasedNodeData(
                null,
                preferredLanguageCode,
                systemLanguageCode,
            ),
    );
});
</script>

<template>
    <span>{{ displayValue }}</span>
</template>
