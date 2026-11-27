<script setup lang="ts">
import { computed, ref, watch, watchEffect } from "vue";

import { useGettext } from "vue3-gettext";

import ReferenceCheckboxItem from "@/arches_controlled_lists/widgets/ReferenceCheckboxWidget/components/ReferenceCheckboxItem.vue";
import { useReferenceSelectOptionsStore } from "@/arches_controlled_lists/stores/useReferenceSelectOptionsStore.ts";
import { buildReferenceSelectAliasedNodeData } from "@/arches_controlled_lists/datatypes/reference-select/utils.ts";

import type {
    ReferenceCheckboxDatatypeCardXNodeXWidgetData,
    ReferenceSelectAliasedNodeData,
    ReferenceSelectDetails,
    ReferenceSelectNodeValue,
    ReferenceSelectTreeNode,
} from "@/arches_controlled_lists/datatypes/reference-select/types.ts";

const {
    aliasedNodeData,
    cardXNodeXWidgetData,
    graphSlug,
    nodeAlias,
    systemLanguageCode,
} = defineProps<{
    aliasedNodeData?: ReferenceSelectAliasedNodeData | null;
    cardXNodeXWidgetData?: ReferenceCheckboxDatatypeCardXNodeXWidgetData;
    graphSlug?: string;
    nodeAlias?: string;
    systemLanguageCode: string;
}>();

const emit = defineEmits<{
    (event: "update:isLoading", isLoading: boolean): void;
    (
        event: "update:aliasedNodeData",
        updatedValue: ReferenceSelectAliasedNodeData,
    ): void;
    (event: "ready"): void;
}>();

const { current: preferredLanguageCode } = useGettext();

const options = ref<ReferenceSelectTreeNode[]>();
const isLoading = ref(false);
const optionsLoaded = ref(false);
const optionsError = ref<string | null>(null);

const multiple = computed(() => !!cardXNodeXWidgetData?.node.config.multiValue);

/** Optional note value type to display instead of the prefLabel. */
const labelValueType = computed(
    () => cardXNodeXWidgetData?.config.labelValueType ?? null,
);

/** Unique radio-group name so browsers group all radios in one widget. */
const radioGroupName = computed(
    () => `ref-rb-${nodeAlias ?? graphSlug ?? "checkbox"}`,
);

/** Derive a Set of selected list_item_ids from the current tile value. */
const selectedIds = computed<Set<string>>(() => {
    if (!aliasedNodeData?.node_value?.length) return new Set();
    const ids = new Set<string>();
    for (const nodeValue of aliasedNodeData.node_value) {
        const firstLabel = nodeValue.labels?.[0];
        if (firstLabel?.list_item_id) {
            ids.add(firstLabel.list_item_id);
        }
    }
    return ids;
});

watchEffect(() => {
    getOptions();
});

watch(isLoading, (newValue) => {
    emit("update:isLoading", newValue);
});

/**
 * Transform raw API items (shaped like ReferenceSelectDetails) into proper
 * ReferenceSelectTreeNode objects with key/label/data populated.
 */
function rawToNode(raw: ReferenceSelectTreeNode): ReferenceSelectTreeNode {
    const details = raw as unknown as ReferenceSelectDetails;
    return {
        key: details.list_item_id,
        label: details.display_value ?? "",
        children: (raw.children ?? []).map(rawToNode),
        data: details,
    };
}

function findOptionById(
    id: string,
    nodes: ReferenceSelectTreeNode[],
): ReferenceSelectTreeNode | undefined {
    for (const node of nodes) {
        if (node.key === id) return node;
        if (node.children?.length) {
            const found = findOptionById(id, node.children);
            if (found) return found;
        }
    }
    return undefined;
}

async function getOptions() {
    try {
        if (optionsLoaded.value) return;
        if (!graphSlug || !nodeAlias) return;

        isLoading.value = true;
        const rawOptions =
            await useReferenceSelectOptionsStore().fetchWidgetOptions(
                graphSlug,
                nodeAlias,
            );
        options.value = rawOptions.map(rawToNode);
    } catch (error) {
        optionsError.value = (error as Error).message;
    } finally {
        isLoading.value = false;
        if (!optionsLoaded.value) {
            emit("ready");
        }
        optionsLoaded.value = true;
    }
}

function onSelectionChange(newIds: Set<string>) {
    const nodeValue: ReferenceSelectNodeValue[] = [];

    for (const id of newIds) {
        const option = findOptionById(id, options.value ?? []);
        if (!option) continue;

        // list_id construction mirrors ReferenceSelectWidgetEditor for consistency.
        const listId = option.data.list_item_values.find(
            (item) => item.list_item_id === id,
        )?.id;

        nodeValue.push({
            list_id: listId!,
            labels: option.data.list_item_values,
            uri: option.data.uri,
        });
    }

    emit(
        "update:aliasedNodeData",
        buildReferenceSelectAliasedNodeData(
            nodeValue.length ? nodeValue : null,
            preferredLanguageCode,
            systemLanguageCode,
        ),
    );
}
</script>

<template>
    <div class="reference-checkbox-editor">
        <div
            v-if="optionsError"
            class="reference-checkbox-error"
        >
            {{ optionsError }}
        </div>
        <div
            v-else
            class="reference-checkbox-options"
        >
            <ReferenceCheckboxItem
                v-for="item in options"
                :key="item.key"
                :item="item"
                :multiple="multiple"
                :selected-ids="selectedIds"
                :radio-group-name="radioGroupName"
                :label-value-type="labelValueType"
                @update:selected-ids="onSelectionChange"
            />
        </div>
    </div>
</template>

<style scoped>
.reference-checkbox-options {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
}
</style>
