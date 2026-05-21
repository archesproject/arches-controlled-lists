import { defineStore } from "pinia";

import arches from "arches";

import type { ReferenceSelectTreeNode } from "@/arches_controlled_lists/datatypes/reference-select/types.ts";

export const useReferenceSelectOptionsStore = defineStore(
    "referenceSelectOptions",
    () => {
        const inflightFetches = new Map<
            string,
            Map<string, Promise<ReferenceSelectTreeNode[]>>
        >();

        function getNodeAliasCache(
            graphSlug: string,
        ): Map<string, Promise<ReferenceSelectTreeNode[]>> {
            if (!inflightFetches.has(graphSlug)) {
                inflightFetches.set(graphSlug, new Map());
            }
            return inflightFetches.get(graphSlug)!;
        }

        function fetchWidgetOptions(
            graphSlug: string,
            nodeAlias: string,
        ): Promise<ReferenceSelectTreeNode[]> {
            const nodeAliasCache = getNodeAliasCache(graphSlug);
            if (!nodeAliasCache.has(nodeAlias)) {
                const queryParams = new URLSearchParams({
                    graph_slug: graphSlug,
                    node_alias: nodeAlias,
                });
                nodeAliasCache.set(
                    nodeAlias,
                    (async () => {
                        const response = await fetch(
                            `${arches.urls.controlled_list_options}?${queryParams}`,
                        );
                        const parsed = await response.json();
                        if (!response.ok) {
                            throw new Error(
                                parsed.message || response.statusText,
                            );
                        }
                        return parsed;
                    })(),
                );
            }
            return nodeAliasCache.get(nodeAlias)!;
        }

        return { fetchWidgetOptions };
    },
);
