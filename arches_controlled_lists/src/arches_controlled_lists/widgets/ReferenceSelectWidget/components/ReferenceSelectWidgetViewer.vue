<script setup lang="ts">
import { computed } from "vue";

import type { AliasedNodeData } from "@/arches_component_lab/types.ts";
import type { ReferenceSelectNodeValue } from "@/arches_controlled_lists/datatypes/reference-select/types";

const { value, aliasedNodeData } = defineProps<{
    value?: ReferenceSelectNodeValue[] | null;
    aliasedNodeData?: AliasedNodeData | null;
}>();

const displayValue = computed(
    () =>
        aliasedNodeData?.display_value ||
        value
            ?.map((item) => item.labels?.[0]?.value)
            .filter(Boolean)
            .join(", "),
);
</script>

<template>
    <span>{{ displayValue }}</span>
</template>
