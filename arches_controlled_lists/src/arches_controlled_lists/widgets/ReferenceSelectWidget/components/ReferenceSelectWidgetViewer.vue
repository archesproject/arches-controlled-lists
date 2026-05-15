<script setup lang="ts">
import type { ReferenceSelectNodeValue } from "@/arches_controlled_lists/datatypes/reference-select/types";

defineProps<{
    value: ReferenceSelectNodeValue[] | null;
}>();
</script>

<template>
    <span>{{
        value
            ?.map((item) => item.labels?.[0]?.value)
            .filter(Boolean)
            .join(", ")
    }}</span>
</template>
