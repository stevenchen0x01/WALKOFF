from collections import OrderedDict
from datetime import datetime
import json

max_results = 50

results = OrderedDict()


def workflow_ended_callback(uid):
    global results
    if uid in results:
        results[uid]['completed_at'] = str(datetime.utcnow())
        results[uid]['status'] = 'completed'


def workflow_started_callback(uid, workflow_name):
    results[uid] = {'name': workflow_name,
                           'started_at': str(datetime.utcnow()),
                           'status': 'running',
                           'results': []}


def __append_step_result(uid, data, step_type):
    global results
    result = {'name': data['name'],
              'result': data['result'],
              'input': data['input'],
              'type': step_type,
              'timestamp': str(datetime.utcnow())}
    results[uid]['results'].append(result)


def step_execution_success_callback(uid, step_data):
    global results
    if uid in results:
        __append_step_result(uid, step_data, 'SUCCESS')


def step_execution_error_callback(uid, step_data):
    global results
    if uid in results:
        __append_step_result(uid, step_data, 'ERROR')
