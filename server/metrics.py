import json
from datetime import datetime
from core.case.callbacks import StepInputValidated, FunctionExecutionSuccess, StepExecutionError, StepInputInvalid, \
    WorkflowShutdown, WorkflowExecutionStart

app_metrics = {}
'''
form of {<app>: {'actions': {<action>: {"success" : {'count': <count>
                                                     'avg_time': <average_execution_time>}
                                        "error": {'count': <count>
                                                  'avg_time': <average_execution_time>}
                 'count': <count>}}
'''
workflow_metrics = {}
'''
form  of {<workflow-name>: {'count': <count>, 'avg_time': <average_execution_time>}}
'''

__action_tmp = {}
__workflow_tmp = {}


@StepInputValidated.connect
def __action_started_callback(sender, **kwargs):
    # TODO: This identifier should be replaced by step id when that happens
    __action_tmp[(sender.app, sender.action)] = datetime.utcnow()


@FunctionExecutionSuccess.connect
def __action_ended_callback(sender, **kwargs):
    __update_success_action_tracker(sender.app, sender.action)


@StepExecutionError.connect
def __action_ended_error_callback(sender, **kwargs):
    step = json.loads(kwargs['data'])
    __update_error_action_tracker(step['app'], step['action'])


def __update_success_action_tracker(app, action):
    __update_action_tracker('success', app, action)


def __update_error_action_tracker(app, action):
    __update_action_tracker('error', app, action)


def __update_action_tracker(form, app, action):
    if (app, action) in __action_tmp:
        execution_time = datetime.utcnow() - __action_tmp[(app, action)]
        if app not in app_metrics:
            app_metrics[app] = {'count': 0, 'actions': {}}
        app_metrics[app]['count'] += 1
        if action not in app_metrics[app]['actions']:
            app_metrics[app]['actions'][action] = {form: {'count': 1, 'avg_time': execution_time}}
        elif form not in app_metrics[app]['actions'][action]:
            app_metrics[app]['actions'][action][form] = {'count': 1, 'avg_time': execution_time}
        else:
            app_metrics[app]['actions'][action][form]['count'] += 1
            app_metrics[app]['actions'][action][form]['avg_time'] = \
                (app_metrics[app]['actions'][action][form]['avg_time'] + execution_time) / 2
        del __action_tmp[(app, action)]


@WorkflowExecutionStart.connect
def __workflow_started_callback(sender, **kwargs):
    # TODO: This identifier should be replaced by step id when that happens
    __workflow_tmp[sender.name] = datetime.utcnow()


@WorkflowShutdown.connect
def __workflow_ended_callback(sender, **kwargs):
    if sender.name in __workflow_tmp:
        execution_time = datetime.utcnow() - __workflow_tmp[sender.name]
        if sender.name not in workflow_metrics:
            workflow_metrics[sender.name] = {'count': 1, 'avg_time': execution_time}
        else:
            workflow_metrics[sender.name]['count'] += 1
            workflow_metrics[sender.name]['avg_time'] = (workflow_metrics[sender.name]['avg_time'] + execution_time) / 2
        del __workflow_tmp[sender.name]
