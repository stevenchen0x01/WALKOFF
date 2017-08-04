import unittest
from core.decorators import *
from apps import Event
import socket
try:
    from importlib import reload
except ImportError:
    from imp import reload
from gevent import monkey, sleep, spawn
from timeit import default_timer


class TestDecorators(unittest.TestCase):

    def test_action_decorator_is_tagged(self):

        @action
        def add_three(a,  b, c):
            return a+b+c

        self.assertTrue(getattr(add_three, 'action'))

    def test_action_decorator_has_arg_names(self):
        @action
        def add_three(a, b, c):
            return a + b + c

        self.assertListEqual(getattr(add_three, '__arg_names'), ['a', 'b', 'c'])

    def test_action_wraps_execution_return_not_specified(self):
        @action
        def add_three(a, b, c):
            return a + b + c

        self.assertTupleEqual(add_three(1, 2, 3), ActionResult(6, 'Success'))

    def test_action_wraps_execution_return_specified(self):
        @action
        def add_three(a, b, c):
            return a + b + c, 'Custom'

        self.assertTupleEqual(add_three(1, 2, 3), ActionResult(6, 'Custom'))

    def test_flag_decorator_is_tagged(self):

        @flag
        def is_even(x):
            return x % 2 == 0

        self.assertTrue(getattr(is_even, 'flag'))
        self.assertTrue(is_even(2))

    def test_filter_decorator_is_tagged(self):
        @datafilter
        def add_one(x):
            return x+1

        self.assertTrue(getattr(add_one, 'filter'))
        self.assertEqual(add_one(1), 2)


class TestEventDecorator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        monkey.patch_socket()

    @classmethod
    def tearDownClass(cls):
        reload(socket)

    def test_event_is_tagged_as_action(self):
        event1 = Event()

        class TestClass(object):
            @event(event1)
            def ev(self, data):
                return data

        self.assertTrue(getattr(TestClass.ev, 'action'))

    def test_event_has_arg_names(self):
        event1 = Event()

        class TestClass(object):
            @event(event1)
            def ev(self, data, a):
                return data

        self.assertListEqual(getattr(TestClass.ev, '__arg_names'), ['self', 'data', 'a'])

    def test_event_raises_with_too_few_args(self):
        event1 = Event()
        with self.assertRaises(InvalidApi):
            class TestClass(object):
                @event(event1)
                def ev(self):
                    return 1

    def test_event_execution(self):
        event1 = Event('Event1')

        class TestClass(object):
            @event(event1)
            def ev(self, data):
                return data

        b = TestClass()
        test_data = {1: 2}

        def sender():
            sleep(0.1)
            event1.trigger(test_data)

        start = default_timer()
        spawn(sender)
        result = b.ev()
        duration = default_timer() - start
        self.assertTupleEqual(result, (test_data, 'Success'))
        self.assertSetEqual(event1.receivers, set())
        self.assertGreater(duration, 0.1)

    def test_event_execution_with_timeout(self):
        event1 = Event('Event1')

        class TestClass(object):
            @event(event1, timeout=0)
            def ev(self, data):
                return data

        b = TestClass()
        test_data = {1: 2}

        def sender():
            sleep(0.1)
            event1.trigger(test_data)

        spawn(sender)
        result = b.ev()
        self.assertEqual(result, ('Getting event Event1 timed out at 0 seconds', 'EventTimedOut'))
        self.assertSetEqual(event1.receivers, set())