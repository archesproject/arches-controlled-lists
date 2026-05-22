import type {
    ReferenceSelectAliasedNodeData,
    ReferenceSelectNodeValue,
} from "@/arches_controlled_lists/datatypes/reference-select/types.ts";

export function buildReferenceSelectAliasedNodeData(
    nodeValue: ReferenceSelectNodeValue[] | null,
): ReferenceSelectAliasedNodeData {
    return {
        node_value: nodeValue,
        display_value:
            nodeValue
                ?.map((item) => item.labels?.[0]?.value)
                .filter(Boolean)
                .join(", ") ?? "",
        details: nodeValue ?? [],
    };
}
