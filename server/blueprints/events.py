import json
from flask import Blueprint, Response
from flask_security import auth_token_required, roles_accepted

events_page = Blueprint('events_page', __name__)


def __case_event_generator():
    while True:
        data = yield
        yield 'data: %s\n\n' % data

__case_event_stream = __case_event_generator()
__case_event_stream.send(None)


def __push_to_case_stream(sender, **kwargs):
    out = {'name': sender.name,
           'ancestry': sender.ancestry}
    if 'data' in kwargs:
        out['data'] = kwargs['data']
    __case_event_stream.send(json.dumps(out))


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
def stream_case_events():
    from server.flaskserver import running_context

    @roles_accepted(*running_context.user_roles['/cases'])
    def inner():
        return Response(__case_event_stream, mimetype='text/event-stream')
    return inner()
