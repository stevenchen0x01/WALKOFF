import unittest

import yaml
from jsonschema.exceptions import RefResolutionError

from core.config.paths import walkoff_schema_path
from core.helpers import import_all_apps
from core.validator import *
from tests.apps import *
from tests.config import basic_app_api, test_apps_path


class TestAppApiValidation(unittest.TestCase):
    """
    This test does not validate if the schema is correct, only the functions associated with further validation
    """

    @classmethod
    def setUpClass(cls):
        App.registry = {}
        import_all_apps(path=test_apps_path, reload=True)

    def setUp(self):
        with open(basic_app_api, 'r') as f:
            self.basicapi = yaml.load(f.read())

    def __generate_resolver_dereferencer(self, spec, expected_success=True):
        try:
            walkoff_resolver = validate_spec_json(spec, walkoff_schema_path, '', None)
        except Exception as e:
            if expected_success:
                self.fail('Unexpected invalid app api. Error: {}'.format(e))
            else:
                raise
        self.dereferencer = partial(deref, resolver=walkoff_resolver)

    def test_dereference_correct_reference_in_same_file(self):
        self.basicapi['definitions'] = {'test_def': {'type': 'object'}}
        self.basicapi['actions']['helloWorld']['returns']['Success']['schema'] = {'$ref': '#/definitions/test_def'}
        self.__generate_resolver_dereferencer(self.basicapi)

    def test_dereference_incorrect_reference_in_same_file(self):
        self.basicapi['definitions'] = {'test_def': {'type': 'object'}}
        self.basicapi['actions']['helloWorld']['returns']['Success']['schema'] = {'$ref': '#/definitions/invalid'}
        with self.assertRaises(RefResolutionError):
            self.__generate_resolver_dereferencer(self.basicapi, expected_success=False)

    def test_validate_definition_empty_required_empty_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object', 'required': [], 'properties': {}}
        with self.assertRaises(ValidationError):
            self.__generate_resolver_dereferencer(self.basicapi, expected_success=False)

    def test_validate_definition_no_required_empty_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object', 'properties': {}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definition_no_required_no_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object', 'properties': {}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definition_no_required_with_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'}}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definition_required_all_in_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'required': ['prop1', 'prop2'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definition_some_required_not_in_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'required': ['prop4', 'prop5'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.__generate_resolver_dereferencer(self.basicapi)
        with self.assertRaises(InvalidApi):
            validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definition_required_matches_properties(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'required': ['prop1', 'prop2', 'prop3'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definition(self.basicapi['definitions']['def1'], self.dereferencer)

    def test_validate_definitions_all_valid(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'required': ['prop1', 'prop2', 'prop3'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.basicapi['definitions']['def2'] = {'type': 'object',
                                                'required': ['prop1', 'prop2'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.basicapi['definitions']['def3'] = {'type': 'object',
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'}}}
        self.basicapi['definitions']['def4'] = {'type': 'object', 'properties': {}}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_definitions(self.basicapi['definitions'], self.dereferencer)

    def test_validate_definitions_one_invalid(self):
        self.basicapi['definitions'] = {}
        self.basicapi['definitions']['def1'] = {'type': 'object',
                                                'required': ['prop1', 'prop2', 'prop3'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.basicapi['definitions']['def2'] = {'type': 'object',
                                                'required': ['prop4', 'prop5'],
                                                'properties': {'prop1': {'type': 'integer'},
                                                               'prop2': {'type': 'object'},
                                                               'prop3': {'type': 'string'}}}
        self.__generate_resolver_dereferencer(self.basicapi)
        with self.assertRaises(InvalidApi):
            validate_definitions(self.basicapi['definitions'], self.dereferencer)

    def test_validate_actions_valid_run_no_params(self):
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_actions(self.basicapi['actions'], self.dereferencer, 'HelloWorld')

    def test_validate_actions_invalid_run_no_params(self):
        self.basicapi['actions']['helloWorld']['run'] = 'invalid.invalid'
        self.__generate_resolver_dereferencer(self.basicapi)
        with self.assertRaises(InvalidApi):
            validate_actions(self.basicapi['actions'], self.dereferencer, 'HelloWorld')

    def test_validate_actions_invalid_app_name(self):
        self.__generate_resolver_dereferencer(self.basicapi)
        with self.assertRaises(UnknownApp):
            validate_actions(self.basicapi['actions'], self.dereferencer, 'InvalidApp')

    def test_validate_action_params_no_duplicate_params_matches_signature(self):
        self.basicapi['actions']['Add Three'] = {'run': 'addThree',
                                                 'parameters': [{'name': 'num1',
                                                                 'type': 'number'},
                                                                {'name': 'num2',
                                                                 'type': 'number'},
                                                                {'name': 'num3',
                                                                 'type': 'number'}]}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_action_params(self.basicapi['actions']['Add Three']['parameters'],
                               self.dereferencer,
                               'HelloWorld',
                               'Add Three',
                               get_app_action('HelloWorld', 'addThree'))

    def test_validate_action_params_duplicate_param_name(self):
        self.basicapi['actions']['Add Three'] = {'run': 'addThree',
                                                 'parameters': [{'name': 'num1',
                                                                 'type': 'number'},
                                                                {'name': 'num1',
                                                                 'type': 'string'},
                                                                {'name': 'num2',
                                                                 'type': 'number'}]}
        self.__generate_resolver_dereferencer(self.basicapi, expected_success=False)
        with self.assertRaises(InvalidApi):
            validate_action_params(self.basicapi['actions']['Add Three']['parameters'],
                                   self.dereferencer,
                                   'HelloWorld',
                                   'Add Three',
                                   get_app_action('HelloWorld', 'addThree'))

    def test_validate_action_params_too_many_params_in_api(self):
        self.basicapi['actions']['Add Three'] = {'run': 'addThree',
                                                 'parameters': [{'name': 'num1',
                                                                 'type': 'number'},
                                                                {'name': 'num2',
                                                                 'type': 'number'},
                                                                {'name': 'num3',
                                                                 'type': 'number'},
                                                                {'name': 'num4',
                                                                 'type': 'string'}]}
        self.__generate_resolver_dereferencer(self.basicapi)
        with self.assertRaises(InvalidApi):
            validate_action_params(self.basicapi['actions']['Add Three']['parameters'],
                                   self.dereferencer,
                                   'HelloWorld',
                                   'Add Three',
                                   get_app_action('HelloWorld', 'addThree'))

    def test_validate_action_params_too_few_params_in_api(self):
        self.basicapi['actions']['Add Three'] = {'run': 'addThree',
                                                 'parameters': [{'name': 'num1',
                                                                 'type': 'number'},
                                                                {'name': 'num2',
                                                                 'type': 'number'}]}
        self.__generate_resolver_dereferencer(self.basicapi)
        with self.assertRaises(InvalidApi):
            validate_action_params(self.basicapi['actions']['Add Three']['parameters'],
                                   self.dereferencer,
                                   'HelloWorld',
                                   'Add Three',
                                   get_app_action('HelloWorld', 'addThree'))

    def test_validate_action_params_different_params_in_api(self):
        self.basicapi['actions']['Add Three'] = {'run': 'addThree',
                                                 'parameters': [{'name': 'num1',
                                                                 'type': 'number'},
                                                                {'name': 'num2',
                                                                 'type': 'number'},
                                                                {'name': 'num4',
                                                                 'type': 'number'}]}
        self.__generate_resolver_dereferencer(self.basicapi)
        with self.assertRaises(InvalidApi):
            validate_action_params(self.basicapi['actions']['Add Three']['parameters'],
                                   self.dereferencer,
                                   'HelloWorld',
                                   'Add Three',
                                   get_app_action('HelloWorld', 'addThree'))

    def test_validate_action_params_event(self):
        self.basicapi['actions']['Sample Event'] = {'run': 'sample_event',
                                                    'event': 'Event1',
                                                    'parameters': [{'name': 'arg1',
                                                                    'type': 'number'},
                                                                   ]}
        self.__generate_resolver_dereferencer(self.basicapi)
        validate_action_params(self.basicapi['actions']['Sample Event']['parameters'],
                               self.dereferencer,
                               'HelloWorld',
                               'Sample Event',
                               get_app_action('HelloWorld', 'sample_event'),
                               event='event1')

    def test_validate_return_codes(self):
        return_codes = ['A', 'B', 'Success']
        validate_app_action_return_codes(return_codes, 'app', 'action')

    def test_invalidate_return_codes_with_reserved(self):
        return_codes = ['UnhandledException', 'B', 'Success']
        with self.assertRaises(InvalidApi):
            validate_app_action_return_codes(return_codes, 'app', 'action')