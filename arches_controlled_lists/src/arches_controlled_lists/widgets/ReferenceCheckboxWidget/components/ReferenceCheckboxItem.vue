<script setup lang="ts">
import { computed } from "vue";

import Checkbox from "primevue/checkbox";
import RadioButton from "primevue/radiobutton";

// Self-import for recursive rendering.
import ReferenceCheckboxItem from "@/arches_controlled_lists/widgets/ReferenceCheckboxWidget/components/ReferenceCheckboxItem.vue";

import type { ReferenceSelectTreeNode } from "@/arches_controlled_lists/datatypes/reference-select/types.ts";

const props = defineProps<{
    item: ReferenceSelectTreeNode;
    multiple: boolean;
    selectedIds: Set<string>;
    /** Shared radio-group name so browsers group all radios in one widget. */
    radioGroupName: string;
    /** Optional note valuetype_id (e.g. "definition") to show instead of prefLabel. */
    labelValueType?: string | null;
}>();

const emit = defineEmits<{
    "update:selectedIds": [ids: Set<string>];
}>();

const isChecked = computed(() => props.selectedIds.has(props.item.key));

/** For radio mode: the single selected key, or null. */
const radioModelValue = computed(() => [...props.selectedIds][0] ?? null);

/**
 * Display label: use the first note_value matching labelValueType when
 * configured, otherwise fall back to the prefLabel-derived item.label.
 */
const displayLabel = computed(() => {
    if (!props.labelValueType) return props.item.label;
    const match = props.item.data.note_values?.find(
        (v) => v.valuetype_id === props.labelValueType,
    );
    return match?.value ?? props.item.label;
});

function onCheckboxChange(checked: boolean) {
    const next = new Set(props.selectedIds);
    if (checked) {
        next.add(props.item.key);
    } else {
        next.delete(props.item.key);
    }
    emit("update:selectedIds", next);
}

function onRadioSelect(_value: string) {
    emit("update:selectedIds", new Set([props.item.key]));
}

function onChildUpdate(newIds: Set<string>) {
    emit("update:selectedIds", newIds);
}
</script>

<template>
    <!-- Guide item: non-interactive section label -->
    <div
        v-if="item.data.guide"
        class="reference-checkbox-section"
    >
        <span class="reference-checkbox-section-label">{{ item.label }}</span>
        <div
            v-if="item.children?.length"
            class="reference-checkbox-children"
        >
            <ReferenceCheckboxItem
                v-for="child in item.children"
                :key="child.key"
                :item="child"
                :multiple="multiple"
                :selected-ids="selectedIds"
                :radio-group-name="radioGroupName"
                :label-value-type="labelValueType"
                @update:selected-ids="onChildUpdate"
            />
        </div>
    </div>

    <!-- Selectable item: checkbox or radio + indented children -->
    <div
        v-else
        class="reference-checkbox-item"
    >
        <div class="reference-checkbox-control">
            <Checkbox
                v-if="multiple"
                :input-id="`ref-cb-${item.key}`"
                :binary="true"
                :model-value="isChecked"
                @update:model-value="onCheckboxChange"
            />
            <RadioButton
                v-else
                :input-id="`ref-rb-${item.key}`"
                :value="item.key"
                :model-value="radioModelValue"
                :pt="{ input: { name: radioGroupName } }"
                @update:model-value="onRadioSelect"
            />
            <label
                :for="multiple ? `ref-cb-${item.key}` : `ref-rb-${item.key}`"
            >
                {{ displayLabel }}
            </label>
        </div>
        <div
            v-if="item.children?.length"
            class="reference-checkbox-children reference-checkbox-indented"
        >
            <ReferenceCheckboxItem
                v-for="child in item.children"
                :key="child.key"
                :item="child"
                :multiple="multiple"
                :selected-ids="selectedIds"
                :radio-group-name="radioGroupName"
                :label-value-type="labelValueType"
                @update:selected-ids="onChildUpdate"
            />
        </div>
    </div>
</template>

<style scoped>
.reference-checkbox-section-label {
    display: block;
    font-weight: 600;
    margin-top: 0.5rem;
    margin-bottom: 0.25rem;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--p-text-muted-color, #6c757d);
}

.reference-checkbox-control {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0;
}

.reference-checkbox-control label {
    all: unset;
    cursor: pointer;
}

.reference-checkbox-indented {
    padding-left: 1.5rem;
}
</style>
