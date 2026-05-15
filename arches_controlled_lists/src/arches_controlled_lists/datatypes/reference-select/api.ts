import arches from "arches";

import type { ReferenceSelectTreeNode } from "@/arches_controlled_lists/datatypes/reference-select/types.ts";

const controlledListWidgetOptionsCache = new Map<
    string,
    Promise<ReferenceSelectTreeNode[]>
>();

export const fetchWidgetOptions = (
    graphSlug: string,
    nodeAlias: string,
): Promise<ReferenceSelectTreeNode[]> => {
    const cacheKey = `${graphSlug}:${nodeAlias}`;
    if (!controlledListWidgetOptionsCache.has(cacheKey)) {
        const queryParams = new URLSearchParams({
            graph_slug: graphSlug,
            node_alias: nodeAlias,
        });
        controlledListWidgetOptionsCache.set(
            cacheKey,
            fetch(`${arches.urls.controlled_list_options}?${queryParams}`)
                .then(async (response) => {
                    const parsed = await response.json();
                    if (!response.ok)
                        throw new Error(parsed.message || response.statusText);
                    return parsed;
                })
                .catch((err) => {
                    controlledListWidgetOptionsCache.delete(cacheKey);
                    throw err;
                }),
        );
    }
    return controlledListWidgetOptionsCache.get(cacheKey)!;
};
