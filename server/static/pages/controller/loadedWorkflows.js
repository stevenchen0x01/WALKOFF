function formatPlaybooksForJSTree(playbook_data){
    var result = [];
    var x = 1;
    for(playbook in playbook_data){
        entry = {"id":x.toString(), "text":playbook, "type":"playbook"};
        var workflows = [];
        for(workflow in playbook_data[playbook]){
            x++;
            workflows.push({"id":x.toString(), "text":playbook_data[playbook][workflow], icon: "jstree-file", "type":"workflow"})
        }
        entry["children"] = workflows;
        result.push(entry);
        x++;
    }
    return result;
}

function executeWorkflow(currentPlaybook, currentWorkflow){
    $.ajax({
        'async': false,
        'type': "POST",
        'global': false,
        'headers':{"Authentication-Token":authKey},
        'url': "playbooks/" + currentPlaybook + "/workflows/" + currentWorkflow + "/execute",
        'success': function (data) {
            $.notify(currentWorkflow + ' is scheduled to execute.', 'success');
            //$("#eventList").append("<li>" + currentWorkflow + " is scheduled to execute.</li>");
            //notifyMe();
        },
        'error': function (jqXHR, status, error) {
            $.notify(currentWorkflow + ' has failed to be scheduled.', 'error');
            //$("#eventList").append("<li>" + currentWorkflow + " has failed to be scheduled.</li>");
        }
    });
}

function customMenu(node){
    var items = {
        executeItem: {
            label: "Execute Workflow",
            action: function () {
                var playbook = $("#loadedPlaybooksTree").jstree(true).get_node(node.parents[0]).text;
                var workflow = node.text;
                executeWorkflow(playbook, workflow);
            }
        },
        // addCase: {
        //     label: "Add Case",
        //     action: function () {
        //         var playbook = $("#loadedPlaybooksTree").jstree(true).get_node(node.parents[0]).text;
        //         addCaseDialog.dialog("open");

        //     }
        // },

    };
    if (node.original.type != "workflow") {
        delete items.executeItem;
        //delete items.addCase;
    }

    return items;
}



$("#loadedPlaybooksTree").jstree({
    'core':{
        'data': formatPlaybooksForJSTree(loadedWorkflows)
    },
    'plugins':['contextmenu'],
    'contextmenu':{
        items: customMenu
    }
}).on('loaded.jstree', function(){
    $("#loadedPlaybooksTree").jstree("open_all");
});