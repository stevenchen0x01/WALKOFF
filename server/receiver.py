import server.workflowresults
import server.blueprints.workflowresult
import server.metrics
import threading
import core.controller


t = None
running = False


def receive():
    print("receiver started")
    while True:

        core.controller.workflow_results_condition.acquire()
        while core.controller.workflow_results_queue.empty():
            print("queue is empty, receiver waiting on condition")
            core.controller.workflow_results_condition.wait(timeout=1)
        callback, data = core.controller.workflow_results_queue.get()
        core.controller.workflow_results_condition.release()

        if callback is None:
            break

        if 'data' in data:
            callback.send()
        else:
            callback.send(data=data['data'])

        if name == 'Workflow Shutdown':
            server.workflowresults.workflow_ended_callback(data['uid'])
            if 'data' in data:
                server.blueprints.workflowresult.workflow_ended_callback(data['name'], data['data'])
            else:
                server.blueprints.workflowresult.workflow_ended_callback(data['name'])
            server.metrics.workflow_ended_callback(data['name'])

        elif name == 'Workflow Execution Start':
            server.workflowresults.workflow_started_callback(data['uid'], data['name'])
            server.metrics.workflow_started_callback(data['name'])

        elif name == 'Step Execution Success':
            server.workflowresults.step_execution_success_callback(data['uid'], data['data'])

        elif name == 'Step Execution Error':
            server.workflowresults.step_execution_error_callback(data['uid'], data['data'])
            server.blueprints.workflowresult.step_error_callback(data['name'], data['data'])
            server.metrics.action_ended_error_callback(data['data']['app'], data['data']['action'])

        elif name == 'Function Execution Success':
            server.blueprints.workflowresult.step_ended_callback(data['input'], data['name'], data['data']['result'])
            server.metrics.action_ended_callback(data['app'], data['action'])

        elif name == 'Step Input Validated':
            server.metrics.action_started_callback(data['app'], data['action'])

    print("receiver returning")
    return


def start_receiver():
    global t
    global running

    if not running:
        running = True
        t = threading.Thread(target=receive)
        t.start()


def stop_receiver():
    global t
    global running

    if running:
        running = False
        core.controller.workflow_results_condition.acquire()
        core.controller.workflow_results_queue.put((None, None))
        core.controller.workflow_results_condition.notify()
        core.controller.workflow_results_condition.release()

        t.join()
