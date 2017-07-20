import unittest
from core.helpers import *
import types
import sys
from os.path import join
from os import sep
from tests.config import test_workflows_path, test_apps_path, function_api_path
import core.config.paths
from core.config.config import initialize
from tests.util.assertwrappers import orderless_list_compare


class TestHelperFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_all_apps(path=test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=function_api_path)

    def setUp(self):
        self.original_apps_path = core.config.paths.apps_path
        core.config.paths.apps_path = test_apps_path

    def tearDown(self):
        core.config.paths.apps_path = self.original_apps_path

    # TODO: Figure out replacement test
    # def test_load_app_function(self):
    #
    #     app = 'HelloWorld'
    #     with server.running_context.flask_app.app_context():
    #         instance = Instance.create(app, 'default_device_name')
    #     existing_actions = {'helloWorld': instance().helloWorld,
    #                         'repeatBackToMe': instance().repeatBackToMe,
    #                         'returnPlusOne': instance().returnPlusOne}
    #     for action, function in existing_actions.items():
    #         self.assertEqual(load_app_function(instance(), action), function)

    # def test_load_app_function_invalid_function(self):
    #     with server.running_context.flask_app.app_context():
    #         instance = Instance.create('HelloWorld', 'default_device_name')
    #     self.assertIsNone(load_app_function(instance(), 'JunkFunctionName'))

    def test_locate_workflows(self):
        expected_workflows = ['basicWorkflowTest.playbook',
                              'DailyQuote.playbook',
                              'dataflowTest.playbook',
                              'dataflowTestStepNotExecuted.playbook',
                              'loopWorkflow.playbook',
                              'multiactionWorkflowTest.playbook',
                              'pauseWorkflowTest.playbook',
                              'multistepError.playbook',
                              'simpleDataManipulationWorkflow.playbook',
                              'templatedWorkflowTest.playbook',
                              'testExecutionWorkflow.playbook',
                              'testScheduler.playbook',
                              'tieredWorkflow.playbook']
        received_workflows = locate_workflows_in_directory(test_workflows_path)
        orderless_list_compare(self, received_workflows, expected_workflows)

        self.assertListEqual(locate_workflows_in_directory('.'), [])

    def test_get_workflow_names_from_file(self):
        workflows = get_workflow_names_from_file(os.path.join(test_workflows_path, 'basicWorkflowTest.playbook'))
        self.assertListEqual(workflows, ['helloWorldWorkflow'])

        workflows = get_workflow_names_from_file(os.path.join(test_workflows_path, 'tieredWorkflow.playbook'))
        self.assertListEqual(workflows, ['parentWorkflow', 'childWorkflow'])

        workflows = get_workflow_names_from_file(os.path.join(test_workflows_path, 'junkfileName.playbook'))
        self.assertIsNone(workflows)

    def test_list_apps(self):
        expected_apps = ['HelloWorld', 'DailyQuote']
        orderless_list_compare(self, expected_apps, list_apps())

    def test_list_widgets(self):
        orderless_list_compare(self, list_widgets('HelloWorld'), ['testWidget', 'testWidget2'])
        self.assertListEqual(list_widgets('JunkApp'), [])

    def test_construct_workflow_name_key(self):
        input_output = {('', ''): '-',
                        ('', 'test_workflow'): '-test_workflow',
                        ('test_playbook', 'test_workflow'): 'test_playbook-test_workflow',
                        ('-test_playbook', 'test_workflow'): 'test_playbook-test_workflow'}
        for (playbook, workflow), expected_result in input_output.items():
            self.assertEqual(construct_workflow_name_key(playbook, workflow), expected_result)

    def test_extract_workflow_name(self):
        wx = construct_workflow_name_key('www', 'xxx')
        xy = construct_workflow_name_key('xxx', 'yyy')
        yz = construct_workflow_name_key('yyy', 'zzz')
        xyyz = construct_workflow_name_key(xy, yz)
        input_output = {(wx, ''): 'xxx',
                        (wx, 'www'): 'xxx',
                        (wx, 'xxx'): 'xxx',
                        (xyyz, ''): '{0}'.format(construct_workflow_name_key('yyy', yz)),
                        (xyyz, 'xxx'): '{0}'.format(construct_workflow_name_key('yyy', yz)),
                        (xyyz, xy): yz}
        for (workflow_key, playbook_name), expected_workflow in input_output.items():
            self.assertEqual(extract_workflow_name(workflow_key, playbook_name=playbook_name), expected_workflow)

    def test_import_py_file(self):
        module_name = 'tests.apps.HelloWorld'
        imported_module = import_py_file(module_name,
                                         os.path.join(core.config.paths.apps_path, 'HelloWorld', 'main.py'))
        self.assertIsInstance(imported_module, types.ModuleType)
        self.assertEqual(imported_module.__name__, module_name)
        self.assertIn(module_name, sys.modules)
        self.assertEqual(sys.modules[module_name], imported_module)

    def test_import_py_file_invalid(self):
        error_type = IOError if sys.version_info[0] == 2 else OSError
        with self.assertRaises(error_type):
            import_py_file('some.module.name', os.path.join(core.config.paths.apps_path, 'InvalidAppName', 'main.py'))

    def test_import_app_main(self):
        module_name = 'tests.apps.HelloWorld.main'
        imported_module = import_app_main('HelloWorld')
        self.assertIsInstance(imported_module, types.ModuleType)
        self.assertEqual(imported_module.__name__, module_name)
        self.assertIn(module_name, sys.modules)
        self.assertEqual(sys.modules[module_name], imported_module)

    def test_import_app_main_invalid_app(self):
        self.assertIsNone(import_app_main('InvalidAppName'))

    def test_construct_module_name_from_path(self):
        input_output = {join('.', 'aaa', 'bbb', 'ccc'): 'aaa.bbb.ccc',
                        join('aaa', 'bbb', 'ccc'): 'aaa.bbb.ccc',
                        join('aaa', '..', 'bbb', 'ccc'): 'aaa.bbb.ccc',
                        '{0}{1}'.format(join('aaa', 'bbb', 'ccc'), sep): 'aaa.bbb.ccc'}
        for input_path, expected_output in input_output.items():
            self.assertEqual(construct_module_name_from_path(input_path), expected_output)

    def test_import_submodules(self):
        from tests import testpkg
        base_name = 'tests.testpkg'
        results = import_submodules(testpkg)
        expected_names = ['{0}.{1}'.format(base_name, module_name) for module_name in ['a', 'b', 'subpkg']]
        self.assertEqual(len(results.keys()), len(expected_names))
        for name in expected_names:
            self.assertIn(name, results.keys())
            self.assertIn(name, sys.modules.keys())

    def test_import_submodules_recursive(self):
        from tests import testpkg
        base_name = 'tests.testpkg'
        results = import_submodules(testpkg, recursive=True)
        expected_names = ['{0}.{1}'.format(base_name, module_name)
                          for module_name in ['a', 'b', 'subpkg', 'subpkg.c', 'subpkg.d']]
        self.assertEqual(len(results.keys()), len(expected_names))
        for name in expected_names:
            self.assertIn(name, results.keys())
            self.assertIn(name, sys.modules.keys())

    def test_subclass_registry(self):
        from six import with_metaclass

        class Sub(with_metaclass(SubclassRegistry, object)):
            pass

        self.assertDictEqual(Sub.registry, {'Sub': Sub})

        class Sub1(Sub):
            pass

        class Sub2(Sub):
            pass

        class Sub3(Sub):
            pass

        class Sub1(Sub):
            pass

        orderless_list_compare(self, Sub.registry.keys(), ['Sub', 'Sub1', 'Sub2', 'Sub3'])
        orderless_list_compare(self, Sub.registry.values(), [Sub, Sub1, Sub2, Sub3])

    def test_format_db_path(self):
        self.assertEqual(format_db_path('sqlite', 'aa.db'), 'sqlite:///aa.db')
        self.assertEqual(format_db_path('postgresql', 'aa.db'), 'postgresql://aa.db')

    def test_import_and_find_tags(self):
        import tests.util.flagsfilters
        from tests.util.flagsfilters import sub1, mod1
        from tests.util.flagsfilters.sub1 import mod2
        filter_tags = import_and_find_tags('tests.util.flagsfilters', 'filter')
        expected_filters = {'top_level_filter': tests.util.flagsfilters.top_level_filter,
                            'filter1': tests.util.flagsfilters.filter1,
                            'length': tests.util.flagsfilters.length,
                            'json_select': tests.util.flagsfilters.json_select,
                            'mod1.filter1': tests.util.flagsfilters.mod1.filter1,
                            'mod1.filter2': tests.util.flagsfilters.mod1.filter2,
                            'sub1.sub1_top_filter': tests.util.flagsfilters.sub1.sub1_top_filter,
                            'sub1.mod2.filter1': tests.util.flagsfilters.sub1.mod2.filter1,
                            'sub1.mod2.complex_filter': tests.util.flagsfilters.sub1.mod2.complex_filter,
                            'sub1.mod2.filter3': tests.util.flagsfilters.sub1.mod2.filter3}
        flag_tags = import_and_find_tags('tests.util.flagsfilters', 'flag')
        expected_flags = {'top_level_flag': tests.util.flagsfilters.top_level_flag,
                          'regMatch': tests.util.flagsfilters.regMatch,
                          'count': tests.util.flagsfilters.count,
                          'mod1.flag1': tests.util.flagsfilters.mod1.flag1,
                          'mod1.flag2': tests.util.flagsfilters.mod1.flag2,
                          'sub1.sub1_top_flag': tests.util.flagsfilters.sub1.sub1_top_flag,
                          'sub1.mod2.flag1': tests.util.flagsfilters.sub1.mod2.flag1,
                          'sub1.mod2.flag2': tests.util.flagsfilters.sub1.mod2.flag2}
        self.assertDictEqual(filter_tags, expected_filters)
        self.assertDictEqual(flag_tags, expected_flags)

    def test_import_all_flags(self):
        self.assertDictEqual(import_all_flags('tests.util.flagsfilters'),
                             import_and_find_tags('tests.util.flagsfilters', 'flag'))

    def test_import_all_flags_invalid_flag_package(self):
        with self.assertRaises(ImportError):
            import_all_flags('invalid.package')

    def test_import_all_filters(self):
        self.assertDictEqual(import_all_filters('tests.util.flagsfilters'),
                             import_and_find_tags('tests.util.flagsfilters', 'filter'))

    def test_import_all_filters_invalid_filter_package(self):
        with self.assertRaises(ImportError):
            import_all_flags('invalid.package')

    def test_get_app_action_api_valid(self):
        api = get_app_action_api('HelloWorld', 'pause')
        expected = ('pause',
                    [{'required': True,
                      'type': 'number',
                      'name': 'seconds',
                      'description': 'Seconds to pause'}])
        self.assertEqual(len(api), 2)
        self.assertEqual(api[0], expected[0])
        self.assertEqual(len(api[1]), 1)
        self.assertDictEqual(api[1][0], expected[1][0])

    def test_get_app_action_api_invalid_app(self):
        with self.assertRaises(UnknownApp):
            get_app_action_api('InvalidApp', 'pause')

    def test_get_app_action_api_invalid_action(self):
        with self.assertRaises(UnknownAppAction):
            get_app_action_api('HelloWorld', 'invalid')

    def assert_params_tuple_equal(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(len(actual), 2)
        self.assertDictEqual(actual[1], expected[1])
        self.assertEqual(len(actual[0]), len(expected[0]))
        for actual_param in actual[0]:
            self.assertIn(actual_param, expected[0])

    def test_get_flag_api_valid(self):
        api = get_flag_api('regMatch')
        expected = (
            [{'required': True, 'type': 'string', 'name': 'regex', 'description': 'The regular expression to match'}],
            {'required': True, 'type': 'string', 'name': 'value', 'description': 'The input value'}
        )
        self.assert_params_tuple_equal(api, expected)

    def test_get_flag_api_invalid(self):
        with self.assertRaises(UnknownFlag):
            get_flag_api('invalid')

    def test_get_filter_api_valid(self):
        api = get_filter_api('length')
        expected = ([], {'required': True, 'type': 'string', 'name': 'value', 'description': 'The input collection'})

        self.assert_params_tuple_equal(api, expected)

    def test_get_filter_api_invalid(self):
        with self.assertRaises(UnknownFilter):
            get_filter_api('invalid')

    def test_get_flag_valid(self):
        from tests.util.flagsfilters import count
        self.assertEqual(get_flag('count'), count)

    def test_get_flag_invalid(self):
        with self.assertRaises(UnknownFlag):
            get_flag('invalid')

    def test_get_filter_valid(self):
        from tests.util.flagsfilters import length
        self.assertEqual(get_filter('length'), length)

    def test_get_filter_invalid(self):
        with self.assertRaises(UnknownFilter):
            get_filter('invalid')

    def test_input_xml_to_dict(self):
        from xml.etree.cElementTree import fromstring
        xml = """<inputs>
                <a1>val1</a1>
                <a3>val3</a3>
                <a2>val2</a2>
                <a5>val5</a5>
                <a4>
                    <a44>
                        <a442>
                            <item>val442-0</item>
                            <item>val442-1</item>
                        </a442>
                        <a441>val441</a441>
                    </a44>
                    <a42>val42</a42>
                    <a43>
                        <item>
                            <a432>val432</a432>
                            <a431>
                                <item>1</item>
                                <item>1</item>
                                <item>2</item>
                                <item>3</item>
                            </a431>
                        </item>
                        <item>
                            <a431>
                                <item>2</item>
                                <item>2</item>
                                <item>3</item>
                                <item>4</item>
                            </a431>
                        </item>
                    </a43>
                    <a41>val41</a41>
                </a4>
            </inputs>"""
        expected = {'a1': 'val1', 'a2': 'val2', 'a3': 'val3',
                    'a4': {'a41': 'val41', 'a42': 'val42',
                           'a43': [{'a431': ['1', '1', '2', '3'], 'a432': 'val432'},
                                   {'a431': ['2', '2', '3', '4']}],
                           'a44': {'a441': 'val441', 'a442': ['val442-0', 'val442-1']}},
                    'a5': 'val5'}
        xml = fromstring(xml)
        converted = inputs_xml_to_dict(xml)
        self.assertDictEqual(converted, expected)

    def test_input_dict_to_from_xml(self):
        inputs = {
            'a1': 'val1',
                  'a2': 'val2',
                  'a3': 'val3',
                  'a5': 'val5',
                  'a4': {'a41': 'val41',
                         'a42': 'val42',
                         'a43': [{'a431': ['1', '1', '2', '3'],
                                  'a432': 'val432'},
                                 {'a431': ['2', '2', '3', '4']}],
                         'a44': {'a441': 'val441',
                                 'a442': ['val442-0', 'val442-1']}}}
        xml = inputs_to_xml(inputs)
        converted = inputs_xml_to_dict(xml)
        self.assertDictEqual(converted, inputs)

    def test_dereference_step_routing(self):
        inputs = {'a': 1, 'b': '@step1', 'c': '@step2', 'd': 'test'}
        accumulator = {'step1': '2', 'step2': 3}
        output = {'a': 1, 'b': '2', 'c': 3, 'd': 'test'}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_extra_steps(self):
        inputs = {'a': 1, 'b': '@step1', 'c': '@step2', 'd': 'test'}
        accumulator = {'step1': '2', 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': 3, 'd': 'test'}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_no_referenced(self):
        inputs = {'a': 1, 'b': '2', 'c': 3, 'd': 'test'}
        accumulator = {'step1': '2', 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': 3, 'd': 'test'}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_step_not_found(self):
        inputs = {'a': 1, 'b': '@step2', 'c': '@invalid', 'd': 'test'}
        accumulator = {'step1': '2', 'step2': 3, 'step3': 5}
        with self.assertRaises(InvalidInput):
            dereference_step_routing(inputs, accumulator, 'message')

    def test_dereference_step_routing_with_nested_inputs(self):
        inputs = {'a': 1, 'b': '2', 'c': '@step1', 'd': {'e': 3, 'f': '@step2'}}
        accumulator = {'step1': '2', 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': '2', 'd': {'e': 3, 'f': 3}}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_with_ref_to_array(self):
        inputs = {'a': 1, 'b': '2', 'c': '@step1', 'd': {'e': 3, 'f': '@step2'}}
        accumulator = {'step1': [1, 2, 3], 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': [1, 2, 3], 'd': {'e': 3, 'f': 3}}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_with_arrays_of_refs(self):
        inputs = {'a': 1, 'b': '2', 'c': ['@step1', '@step2', '@step3'], 'd': {'e': 3, 'f': '@step2'}}
        accumulator = {'step1': 1, 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': [1, 3, 5], 'd': {'e': 3, 'f': 3}}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_dereference_step_routing_with_arrays_of_objects(self):
        inputs = {'a': 1, 'b': '2', 'c': [{'a': '@step1', 'b': '@step2'}, {'a': 10, 'b': '@step3'}],
                  'd': {'e': 3, 'f': '@step2'}}
        accumulator = {'step1': 1, 'step2': 3, 'step3': 5}
        output = {'a': 1, 'b': '2', 'c': [{'a': 1, 'b': 3}, {'a': 10, 'b': 5}], 'd': {'e': 3, 'f': 3}}
        self.assertDictEqual(dereference_step_routing(inputs, accumulator, 'message'), output)

    def test_get_arg_names_no_args(self):
        def x(): pass

        self.assertListEqual(get_function_arg_names(x), [])

    def test_get_arg_names(self):
        def x(a, b, c): pass

        self.assertListEqual(get_function_arg_names(x), ['a', 'b', 'c'])

    def test_format_exception_message_no_exception_message(self):
        class CustomError(Exception):
            pass

        try:
            raise CustomError
        except CustomError as e:
            self.assertEqual(format_exception_message(e), 'CustomError')

    def test_format_exception_message_with_exception_message(self):
        class CustomError(Exception):
            pass

        try:
            raise CustomError('test')
        except CustomError as e:
            self.assertEqual(format_exception_message(e), 'CustomError: test')