import threading
import core.controller
from core.case import callbacks

t = None
running = False


def send_callback(callback, sender, data):
    if 'data' in data:
        callback.send(sender, data=data['data'])
    else:
        callback.send(sender)


def receive():
    print("receiver started")
    while True:

        core.controller.workflow_results_condition.acquire()
        while core.controller.workflow_results_queue.empty():
            print("queue is empty, receiver waiting on condition")
            core.controller.workflow_results_condition.wait(timeout=1)
        callback, sender, data = core.controller.workflow_results_queue.get()
        core.controller.workflow_results_condition.release()

        if callback is None:
            break

        print("Receiver popped "+callback+" off queue")

        if callback == "Workflow Execution Start":
            send_callback(callbacks.WorkflowExecutionStart, sender, data)
        elif callback == "Next Step Found":
            send_callback(callbacks.NextStepFound, sender, data)
        elif callback == "App Instance Created":
            send_callback(callbacks.AppInstanceCreated, sender, data)
        elif callback == "Workflow Shutdown":
            send_callback(callbacks.WorkflowShutdown, sender, data)
        elif callback == "Workflow Input Validated":
            send_callback(callbacks.WorkflowInputValidated, sender, data)
        elif callback == "Workflow Input Invalid":
            send_callback(callbacks.WorkflowInputInvalid, sender, data)
        elif callback == "Step Execution Success":
            send_callback(callbacks.StepExecutionSuccess, sender, data)
        elif callback == "Step Execution Error":
            send_callback(callbacks.StepExecutionError, sender, data)
        elif callback == "Step Input Validated":
            send_callback(callbacks.StepInputValidated, sender, data)
        elif callback == "Function Execution Success":
            send_callback(callbacks.FunctionExecutionSuccess, sender, data)
        elif callback == "Step Input Invalid":
            send_callback(callbacks.StepInputInvalid, sender, data)
        elif callback == "Conditionals Executed":
            send_callback(callbacks.ConditionalsExecuted, sender, data)

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
        core.controller.workflow_results_queue.put((None, None, None))
        core.controller.workflow_results_condition.notify()
        core.controller.workflow_results_condition.release()

        t.join()
