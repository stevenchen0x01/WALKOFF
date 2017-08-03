import unittest
import core.config.config
from core.case import database
from core.case import subscription
import core.controller
from core.controller import Controller, initialize_threading, shutdown_pool
from core.helpers import construct_workflow_name_key, import_all_flags, import_all_filters, import_all_apps
from tests import config
from tests.util.assertwrappers import orderless_list_compare
from tests.util.case_db_help import *
from tests.apps import App
from server.receiver import start_receiver, stop_receiver
from core.case.callbacks import FunctionExecutionSuccess
import threading


class TestSimpleWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        App.registry = {}
        import_all_apps(path=config.test_apps_path, reload=True)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=config.function_api_path)
        core.controller.NUM_PROCESSES = 1

    def setUp(self):
        case_database.initialize()
        self.controller = Controller(workflows_path=config.test_workflows_path)
        self.start = datetime.utcnow()

        initialize_threading()
        start_receiver()

    def tearDown(self):
        database.case_db.tear_down()
        subscription.clear_subscriptions()
        stop_receiver()

    def test_simple_workflow_execution(self):
        workflow_name = construct_workflow_name_key('basicWorkflowTest', 'helloWorldWorkflow')
        setup_subscriptions_for_step(workflow_name, ['start'])
        self.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        shutdown_pool()
        stop_receiver()

        steps = executed_steps('defaultController', workflow_name, self.start, datetime.utcnow())

        self.assertEqual(len(steps), 1)
        step = steps[0]
        ancestry = step['ancestry'].split(',')
        self.assertEqual(ancestry[-1], "start")
        result = step['data']
        self.assertDictEqual(result['result'], {'result': "REPEATING: Hello World", 'status': 'Success'})

    def test_multi_action_workflow(self):
        workflow_name = construct_workflow_name_key('multiactionWorkflowTest', 'multiactionWorkflow')
        step_names = ['start', '1']
        setup_subscriptions_for_step(workflow_name, step_names)
        self.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')

        shutdown_pool()
        stop_receiver()

        steps = executed_steps('defaultController', workflow_name, self.start, datetime.utcnow())
        self.assertEqual(len(steps), 2)
        names = [step['ancestry'].split(',')[-1] for step in steps]
        orderless_list_compare(self, names, step_names)
        name_result = {'start': {'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                       '1': {'result': "REPEATING: Hello World", 'status': 'Success'}}
        for step in steps:
            name = step['ancestry'].split(',')[-1]
            self.assertIn(name, name_result)
            result = step['data']
            if type(name_result[name]) == dict:
                self.assertDictEqual(result['result'], name_result[name])
            else:
                self.assertEqual(result['result'], name_result[name])

    def test_error_workflow(self):
        workflow_name = construct_workflow_name_key('multistepError', 'multiactionErrorWorkflow')
        step_names = ['start', '1', 'error']
        setup_subscriptions_for_step(workflow_name, step_names)
        self.controller.execute_workflow('multistepError', 'multiactionErrorWorkflow')

        shutdown_pool()
        stop_receiver()

        steps = executed_steps('defaultController', workflow_name, self.start, datetime.utcnow())
        self.assertEqual(len(steps), 2)
        names = [step['ancestry'].split(',')[-1] for step in steps]
        orderless_list_compare(self, names, ['start', 'error'])
        name_result = {'start': {'result': {"message": "HELLO WORLD"}, 'status': 'Success'},
                       'error': {'status': 'Success', 'result': 'REPEATING: Hello World'}}
        for step in steps:
            name = step['ancestry'].split(',')[-1]
            self.assertIn(name, name_result)
            result = step['data']
            self.assertDictEqual(result['result'], name_result[name])

    def test_workflow_with_dataflow(self):
        workflow_name = construct_workflow_name_key('dataflowTest', 'dataflowWorkflow')
        step_names = ['start', '1', '2']
        setup_subscriptions_for_step(workflow_name, step_names)
        self.controller.execute_workflow('dataflowTest', 'dataflowWorkflow')
        steps = []
        lock = threading.Lock()

        @FunctionExecutionSuccess.connect
        def xx(sender, **kwargs):
            lock.acquire()
            steps.append(sender.name)
            lock.release()

        shutdown_pool()
        stop_receiver()

        self.assertListEqual(steps, step_names)

    def test_workflow_with_dataflow_step_not_executed(self):
        self.controller.execute_workflow('dataflowTestStepNotExecuted', 'dataflowWorkflow')

        steps = []
        lock = threading.Lock()

        @FunctionExecutionSuccess.connect
        def xx(sender, **kwargs):
            lock.acquire()
            steps.append(sender.name)
            lock.release()

        shutdown_pool()
        stop_receiver()

        self.assertEqual(steps, ['start'])
