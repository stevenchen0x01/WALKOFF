import json
from flask import Blueprint, Response
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context
from gevent.event import Event, AsyncResult

events_page = Blueprint('events_page', __name__)

__case_event_json = AsyncResult()
__sync_signal = Event()


def __case_event_stream():
    while True:
        data = __case_event_json.get()
        yield 'data: %s\n\n' % data
        __sync_signal.wait()


def __push_to_case_stream(sender, **kwargs):
    out = {'name': sender.name,
           'ancestry': sender.ancestry}
    if 'data' in kwargs:
        out['data'] = kwargs['data']
    __case_event_json.set(json.dumps(out))
    __sync_signal.set()
    __sync_signal.clear()


def setup_case_stream():
    from blinker import NamedSignal
    import core.case.callbacks as callbacks
    signals = [getattr(callbacks, field) for field in dir(callbacks) if (not field.startswith('__')
                                                                             and isinstance(getattr(callbacks, field),
                                                                                            NamedSignal))]
    for signal in signals:
        signal.connect(__push_to_case_stream)


@events_page.route('/', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def stream_case_events():
    return Response(__case_event_stream(), mimetype='text/event-stream')
