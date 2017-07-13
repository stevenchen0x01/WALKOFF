import flaskserver
import server.workflowresults
import server.blueprints.workflowresult
import server.metrics


def receive():
    while True:

        flaskserver.running_context.wf_res_cond.acquire()
        while flaskserver.running_context.wf_res_queue.empty():
            flaskserver.running_context.wf_res_cond.wait()
        name, data = flaskserver.running_context.wf_res_queue.get()
        flaskserver.running_context.wf_res_cond.release()

        if name is None:
            break

        if name == 'Workflow Shutdown':
            server.workflowresults.workflow_ended_callback(data['uid'])
            if 'accumulator' in data:
                server.blueprints.workflowresult.workflow_ended_callback(data['name'], data['accumulator'])
            else:
                server.blueprints.workflowresult.workflow_ended_callback(data['name'])
            server.metrics.workflow_ended_callback(data['name'])

        elif name == 'Workflow Execution Start':
            server.workflowresults.workflow_started_callback(data['uid'], data['name'])
            server.metrics.workflow_started_callback(data['name'])

        elif name == 'Step Execution Success':
            server.workflowresults.step_execution_success_callback(data['uid'], data['step_data'])

        elif name == 'Step Execution Error':
            server.workflowresults.step_execution_error_callback(data['uid'], data['step_data'])
            server.blueprints.workflowresult.step_error_callback(data['name'], data['step_data'])
            server.metrics.action_ended_error_callback(data['step_data']['app'], data['step_data']['action'])

        elif name == 'Function Execution Success':
            server.blueprints.workflowresult.step_ended_callback(data['input'], data['name'], data['result'])
            server.metrics.action_ended_callback(data['app'], data['action'])

        elif name == 'Step Input Validated':
            server.metrics.action_started_callback(data['app'], data['action'])
