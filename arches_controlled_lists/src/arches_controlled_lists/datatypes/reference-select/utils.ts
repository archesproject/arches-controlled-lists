import type { AliasedNodeData } from "@/arches_component_lab/types.ts";
import type { ReferenceSelectNodeValue } from "@/arches_controlled_lists/datatypes/reference-select/types.ts";

export function buildReferenceSelectAliasedNodeData(
    nodeValue: ReferenceSelectNodeValue[] | null,
): AliasedNodeData {
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
