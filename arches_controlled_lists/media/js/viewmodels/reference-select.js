import $ from 'jquery';
import ko from 'knockout';
import koMapping from 'knockout-mapping';
import arches from 'arches';
import WidgetViewModel from 'viewmodels/widget';

export default function(params) {
    const NAME_LOOKUP = {};
    var self = this;

    params.configKeys = ['placeholder', 'defaultValue'];
    this.multiple = !!ko.unwrap(params.node.config.multiValue);
    this.displayName = ko.observable('');
    this.selectionValue = ko.observable([]); // formatted version of this.value that select2 can use
    this.activeLanguage = arches.activeLanguage;

    WidgetViewModel.apply(this, [params]);

    this.getPrefLabel = function(labels){
        return koMapping.toJS(labels)?.find(
            label => label.language_id === arches.activeLanguage && label.valuetype_id === 'prefLabel'
        )?.value || arches.translations.unlabeledItem;
    }; 

    this.isLabel = function (value) {
        return ['prefLabel', 'altLabel'].includes(value.valuetype_id);
    };

    this.displayValue = ko.computed(function() {
        const val = self.value();
        let name = null;
        if (val) {
            name = val.map(item => self.getPrefLabel(item.labels)).join(", ");
        }
        return name;
    });

    this.valueAndSelectionDiffer = function(value, selection) {
        if (!(ko.unwrap(value) instanceof Array)) {
            return true;
        }
        const valueUris = ko.unwrap(value).map(val=>ko.unwrap(val.uri));
        return JSON.stringify(selection) !== JSON.stringify(valueUris);
    };

    this.selectionValue.subscribe(selection => {
        if (selection) {
            if (!(selection instanceof Array)) { selection = [selection]; }
            if (self.valueAndSelectionDiffer(self.value, selection)) {
                const newItem = selection.map(uri => {
                    return {
                        "labels": NAME_LOOKUP[uri].labels,
                        "list_id": NAME_LOOKUP[uri]["list_id"],
                        "uri": uri
                    };
                });
                self.value(newItem);
            }
        } else {
            self.value(null);
        }
    });

    this.value.subscribe(val => {
        if (val?.length) {
            self.selectionValue(val.map(item=>ko.unwrap(item.uri)));
        } else {
            self.selectionValue(null);
        }
    });

    this.select2Config = {
        value: self.selectionValue,
        clickBubble: true,
        multiple: this.multiple,
        closeOnSelect: true,
        placeholder: self.placeholder,
        allowClear: true,
        ajax: {
            url: arches.urls.controlled_list(ko.unwrap(params.node.config.controlledList)),
            dataType: 'json',
            quietMillis: 250,
            data: function(requestParams) {

                return {
                    flat: true
                };
            },
            processResults: function(data) {
                const items = data.items; 
                items.forEach(item => {
                    item["list_id"] = item.id;
                    item.id = item.uri;
                    item.disabled = item.guide;
                    item.labels = item.values.filter(val => self.isLabel(val));
                });
                return {
                    "results": items,
                    "pagination": {
                        "more": false
                    }
                };
            }
        },
        templateResult: function(item) {
            let indentation = '';
            for (let i = 0; i < item.depth; i++) {
                indentation += '&nbsp;&nbsp;&nbsp;&nbsp;';
            }

            if (item.uri) {
                const text = self.getPrefLabel(item.labels) || arches.translations.searching + '...';
                NAME_LOOKUP[item.uri] = {"prefLabel": text, "labels": item.labels, "list_id": item.list_id};
                return indentation + text;
            }
        },
        templateSelection: function(item) {
            if (!item.uri) { // option has a different shape when coming from initSelection vs templateResult
                return item.text; 
            } else {
                return NAME_LOOKUP[item.uri]["prefLabel"];
            }
        },
        escapeMarkup: function(markup) { return markup; },
        initComplete: false,
        initSelection: function(el, callback) {

            const setSelectionData = function(data) {
                const valueData = koMapping.toJS(self.value());
                valueData.forEach(function(value) {
                    NAME_LOOKUP[value.uri] = {
                            "prefLabel": self.getPrefLabel(value.labels),
                            "labels": value.labels,
                            "list_id": value.list_id,
                        };
                });
    
                if(!self.select2Config.initComplete){
                    valueData.forEach(function(data) {
                        const option = new Option(
                            self.getPrefLabel(data.labels),
                            data.uri,
                            true, 
                            true
                        );
                        $(el).append(option);
                        self.selectionValue().push(data.uri);
                    });
                    self.select2Config.initComplete = true;
                }
                callback(valueData);
            };

            if (self.value()?.length) {
                setSelectionData();
            } else {
                callback([]);
            }

        }
    };

};