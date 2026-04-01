import ko from 'knockout';
import $ from 'jquery';
import uuid from 'uuid';
import arches from 'arches';
import JsonErrorAlertViewModel from 'viewmodels/alert-json';
import migrateConceptTileDataTemplate from 'templates/views/components/etl_modules/migrate-concept-tile-data.htm';


const MigrateConceptTileDataViewModel = function(params) {
    const self = this;

    this.config = params.config;
    this.state = params.state;
    this.editHistoryUrl = `${arches.urls.edit_history}?transactionid=${ko.unwrap(params.selectedLoadEvent)?.loadid}`;
    this.loadDetails = params.load_details || ko.observable();
    this.loadId = params.loadId || uuid.generate();
    this.moduleId = params.etlmoduleid;
    this.formData = new window.FormData();

    // Graph and node selection
    this.graphs = ko.observableArray();
    this.selectedGraph = ko.observable();
    this.referenceNodes = ko.observableArray();
    this.selectedNodeIds = ko.observableArray();
    this.migrateAll = ko.observable(false);

    // UI state
    this.loading = ko.observable(false);
    this.formatTime = params.formatTime;
    this.timeDifference = params.timeDifference;
    this.selectedLoadEvent = params.selectedLoadEvent || ko.observable();
    this.statusDetails = this.selectedLoadEvent()?.load_description?.split("|");
    this.alert = params.alert || ko.observable();

    this.ready = ko.computed(function() {
        return !!self.selectedGraph() &&
            (self.migrateAll() || self.selectedNodeIds().length > 0) &&
            !self.loading();
    });

    this.nodeSelectionLabel = ko.computed(function() {
        if (self.migrateAll()) {
            return self.referenceNodes().length + ' node(s) will be migrated';
        }
        return self.selectedNodeIds().length + ' node(s) selected';
    });

    // When migrateAll is toggled on, select all nodes
    this.migrateAll.subscribe(function(selectAll) {
        if (selectAll) {
            const allIds = self.referenceNodes().map(function(node) {
                return node.nodeid;
            });
            self.selectedNodeIds(allIds);
        } else {
            self.selectedNodeIds([]);
        }
    });

    // When graph changes, fetch reference nodes
    this.selectedGraph.subscribe(function(graphid) {
        self.referenceNodes([]);
        self.selectedNodeIds([]);
        self.migrateAll(false);
        if (!graphid) return;

        self.loading(true);
        self.submit('get_reference_nodes').then(function(data) {
            const nodes = data.result.map(function(node) {
                const cardName = JSON.parse(node.card_name)[arches.activeLanguage];
                const widgetLabel = JSON.parse(node.widget_label)[arches.activeLanguage];
                const config = JSON.parse(node.config);
                return {
                    nodeid: node.nodeid,
                    label: cardName + ' - ' + widgetLabel,
                    alias: node.alias,
                    controlledList: config.controlledList,
                    nodegroupid: node.nodegroupid,
                };
            });
            self.referenceNodes(nodes);
        }).fail(function(err) {
            self.alert(
                new JsonErrorAlertViewModel(
                    'ep-alert-red',
                    err.responseJSON?.data || {title: 'Error', message: 'Failed to load nodes'},
                    null,
                    function() {}
                )
            );
        }).always(function() {
            self.loading(false);
        });
    });

    // Fetch graphs on initialization
    this.fetchGraphs = function() {
        self.loading(true);
        self.graphs([]);
        self.submit('get_graphs').then(function(data) {
            data.result.forEach(function(graph) {
                self.graphs.push({
                    graphName: graph.name,
                    graphid: graph.graphid,
                });
            });
        }).fail(function(err) {
            self.alert(
                new JsonErrorAlertViewModel(
                    'ep-alert-red',
                    err.responseJSON?.data || {title: 'Error', message: 'Failed to load graphs'},
                    null,
                    function() {}
                )
            );
        }).always(function() {
            self.loading(false);
        });
    };

    this.write = function() {
        if (!self.ready()) return;

        self.loading(true);
        params.activeTab("import");
        self.submit('write').then(function(data) {
            // Success - the status tab will update via polling
        }).fail(function(err) {
            self.alert(
                new JsonErrorAlertViewModel(
                    'ep-alert-red',
                    err.responseJSON?.data || {title: 'Error', message: 'Migration failed'},
                    null,
                    function() {}
                )
            );
        }).always(function() {
            self.loading(false);
        });
    };

    this.submit = function(action) {
        self.formData = new window.FormData();
        self.formData.append('action', action);
        self.formData.append('load_id', self.loadId);
        self.formData.append('module', self.moduleId);
        if (self.selectedGraph()) {
            self.formData.append('graphid', self.selectedGraph());
        }
        if (self.migrateAll()) {
            self.formData.append('migrate_all', 'true');
        }
        if (self.selectedNodeIds().length > 0) {
            self.formData.append('node_ids', JSON.stringify(self.selectedNodeIds()));
        }
        return $.ajax({
            type: "POST",
            url: arches.urls.etl_manager,
            data: self.formData,
            cache: false,
            processData: false,
            contentType: false,
        });
    };

    this.fetchGraphs();
};


ko.components.register('migrate-concept-tile-data', {
    viewModel: MigrateConceptTileDataViewModel,
    template: migrateConceptTileDataTemplate,
});

export default MigrateConceptTileDataViewModel;
