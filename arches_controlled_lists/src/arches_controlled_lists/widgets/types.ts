import type { TreeNode } from "primevue/treenode";
import type { AliasedNodeData } from "@/arches_component_lab/types.ts";

export type WidgetMode = "edit" | "view";

export interface ReferenceNodeValue extends AliasedNodeData {
    display_value: string;
    node_value: ReferenceSelectFetchedOption[] | null;
    details: { display_value: string; resource_id: string }[];
}

export interface ReferenceSelectFetchedOption {
    list_item_id: string;
    display_value: string;
    sort_order: number;
    children: ReferenceSelectFetchedOption[];
}

export interface ReferenceSelectTreeNode extends TreeNode {
    key: string;
    label: string;
    children: ReferenceSelectTreeNode[];
    data: ReferenceSelectFetchedOption;
}
