<script setup lang="ts">
import { computed, onMounted } from "vue";

import { buildReferenceSelectAliasedNodeData } from "@/arches_controlled_lists/datatypes/reference-select/utils.ts";

import type { ReferenceSelectAliasedNodeData } from "@/arches_controlled_lists/datatypes/reference-select/types";

const { aliasedNodeData } = defineProps<{
    aliasedNodeData?: ReferenceSelectAliasedNodeData | null;
}>();

const emit = defineEmits<{
    initialized: [updatedValue: ReferenceSelectAliasedNodeData];
}>();

const displayValue = computed(() => aliasedNodeData?.display_value);

onMounted(() => {
    emit(
        "initialized",
        aliasedNodeData ?? buildReferenceSelectAliasedNodeData(null),
    );
});
</script>

<template>
    <span>{{ displayValue }}</span>
</template>
