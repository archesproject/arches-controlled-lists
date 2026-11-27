import $ from "jquery";
import ko from "knockout";
import koMapping from "knockout-mapping";
import arches from "arches";
import WidgetViewModel from "viewmodels/widget";

export default function (params) {
    var self = this;

    params.configKeys = ["placeholder", "defaultValue", "labelValueType"];
    this.multiple = !!ko.unwrap(params.node.config.multiValue);
    this.listId = ko.unwrap(params.node.config.controlledList);
    this.items = ko.observableArray([]);
    this.isLoading = ko.observable(true);
    this.activeLanguage = arches.activeLanguage;

    // selectedIds: list_item_id strings currently checked.
    // selectedId:  single list_item_id for radio (single-value) mode.
    this.selectedIds = ko.observableArray([]);
    this.selectedId = ko.observable(null);

    WidgetViewModel.apply(this, [params]);

    var syncInProgress = false;

    // ------------------------------------------------------------------ helpers

    // Options shown in the config-form dropdown.
    // The empty string means "use the preferred label" (default behaviour).
    this.labelValueTypeOptions = [
        { value: "", label: arches.translations.prefLabel || "Preferred Label" },
        { value: "scopeNote", label: "Scope Note" },
        { value: "definition", label: "Definition" },
        { value: "example", label: "Example" },
        { value: "historyNote", label: "History Note" },
        { value: "editorialNote", label: "Editorial Note" },
        { value: "changeNote", label: "Change Note" },
        { value: "note", label: "Note" },
        { value: "description", label: "Description" },
    ];

    this.isLabel = function (val) {
        return ["prefLabel", "altLabel", "hiddenLabel"].includes(
            val.valuetype_id,
        );
    };

    this.getPrefLabel = function (values) {
        var labels = Array.isArray(values) ? values : koMapping.toJS(values) || [];
        return (
            labels.find(function (v) {
                return (
                    v.valuetype_id === "prefLabel" &&
                    v.language_id === arches.activeLanguage
                );
            })?.value ||
            labels.find(function (v) {
                return v.valuetype_id === "prefLabel";
            })?.value ||
            arches.translations.unlabeledItem
        );
    };

    /**
     * Returns the display label for a list item's values array.
     * Uses the configured labelValueType note when set, falling back to prefLabel.
     */
    this.getDisplayLabel = function (values) {
        var valueType = ko.unwrap(self.labelValueType);
        var allValues = Array.isArray(values) ? values : koMapping.toJS(values) || [];
        if (valueType) {
            var match = allValues.find(function (v) {
                return v.valuetype_id === valueType;
            });
            if (match) return match.value;
        }
        return self.getPrefLabel(allValues);
    };

    // Flatten the nested items tree for ID → item lookup when building tile values.
    function flattenItems(items) {
        var flat = [];
        (items || []).forEach(function (item) {
            flat.push(item);
            if (item.children && item.children.length) {
                flat = flat.concat(flattenItems(item.children));
            }
        });
        return flat;
    }

    // Pre-process tree into a flat, hierarchically-ordered list with depth
    // so the template can render with CSS indentation without recursion.
    this.flatItems = ko.computed(function () {
        function walk(items, depth) {
            var result = [];
            (items || []).forEach(function (item) {
                result.push({
                    id: item.id,
                    list_id: item.list_id,
                    uri: item.uri,
                    guide: item.guide,
                    values: item.values,
                    depth: depth,
                });
                if (item.children && item.children.length) {
                    result = result.concat(walk(item.children, depth + 1));
                }
            });
            return result;
        }
        return walk(self.items(), 0);
    });

    // displayValue shown in the report block.
    this.displayValue = ko.computed(function () {
        var val = self.value();
        if (!val || !val.length) return "";
        return val
            .map(function (item) {
                return self.getPrefLabel(item.labels);
            })
            .join(", ");
    });

    // ------------------------------------------------------------------ sync

    function buildTileEntry(item) {
        return {
            list_id: item.list_id,
            uri: item.uri,
            labels: item.values.filter(self.isLabel),
        };
    }

    function syncToValue(ids) {
        if (syncInProgress) return;
        syncInProgress = true;

        if (!ids || !ids.length) {
            self.value(null);
        } else {
            var allFlat = flattenItems(self.items());
            var newValue = ids
                .map(function (id) {
                    var item = allFlat.find(function (i) {
                        return i.id === id;
                    });
                    return item ? buildTileEntry(item) : null;
                })
                .filter(Boolean);
            self.value(newValue.length ? newValue : null);
        }

        syncInProgress = false;
    }

    function syncFromValue(val) {
        if (syncInProgress) return;
        syncInProgress = true;

        if (val && val.length) {
            var ids = val
                .map(function (item) {
                    var labels = koMapping.toJS(item.labels) || [];
                    return labels[0]?.list_item_id || null;
                })
                .filter(Boolean);
            self.selectedIds(ids);
            self.selectedId(ids[0] || null);
        } else {
            self.selectedIds([]);
            self.selectedId(null);
        }

        syncInProgress = false;
    }

    // Initialise from existing tile value (e.g. editing a saved tile).
    syncFromValue(ko.unwrap(self.value));

    // Wire up bidirectional sync.
    self.selectedIds.subscribe(function (ids) {
        if (!self.multiple) return;
        syncToValue(ids);
    });

    self.selectedId.subscribe(function (id) {
        if (self.multiple) return;
        syncToValue(id ? [id] : []);
    });

    self.value.subscribe(function (val) {
        syncFromValue(val);
    });

    // ------------------------------------------------------------------ load

    $.getJSON(arches.urls.controlled_list(self.listId))
        .then(function (data) {
            self.items(data.items || []);
        })
        .always(function () {
            self.isLoading(false);
        });
}
