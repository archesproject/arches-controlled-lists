<script setup lang="ts">
import type { ReferenceSelectNodeValue } from "@/arches_controlled_lists/datatypes/reference-select/types";

defineProps<{
    nodeValue: ReferenceSelectNodeValue[] | null;
}>();
</script>

<template>
    <span>{{
        nodeValue
            ?.map((item) => item.labels?.[0]?.value)
            .filter(Boolean)
            .join(", ")
    }}</span>
</template>
