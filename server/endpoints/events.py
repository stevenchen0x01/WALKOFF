from flask_security import auth_token_required, roles_accepted
import core.case.database as case_database
from server.return_codes import *
from flask import request


def update_event_note():
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        data = request.get_json()
        valid_event_id = case_database.case_db.session.query(case_database.Event) \
            .filter(case_database.Event.id == data['id']).all()
        if valid_event_id:
            case_database.case_db.edit_event_note(data['id'], data['note'])
            return case_database.case_db.event_as_json(data['id']), SUCCESS
        else:
            return {"error": "Event does not exist."}, OBJECT_DNE_ERROR
    return __func()


def read_event(event_id):
    from server.context import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        valid_event_id = case_database.case_db.session.query(case_database.Event) \
            .filter(case_database.Event.id == event_id).all()
        if valid_event_id:
            return case_database.case_db.event_as_json(event_id), SUCCESS
        else:
            return {"error": "Event does not exist."}, OBJECT_DNE_ERROR
    return __func()
