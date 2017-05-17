import json
import os
from flask import render_template, current_app, send_file
from flask_security import login_required, current_user, roles_accepted
import core.config.config
import core.config.paths
import core.filters
import core.flags
from core import helpers
from core.helpers import combine_dicts


def read_all_possible_subscriptions():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        return core.config.config.possible_events

    return __func()


def get_apps():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        return {"apps": helpers.list_apps()}

    return __func()


def get_app_actions():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        core.config.config.load_function_info()
        return core.config.config.function_info['apps']

    return __func()


def read_all_filters():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/playbooks'])
    def __func():
        return {"status": "success", "filters": core.config.config.function_info['filters']}

    return __func()


def read_all_flags():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/playbooks'])
    def __func():
        core.config.config.load_function_info()
        return {"status": "success", "flags": core.config.config.function_info['flags']}

    return __func()


def sys_pages(interface_name):
    from server.context import running_context
    from server import interface

    @roles_accepted(*running_context.user_roles['/interface'])
    def __func():
        if current_user.is_authenticated and interface_name:
            args = getattr(interface, interface_name)()
            combine_dicts(args, {"authKey": current_user.get_auth_token()})
            return render_template("pages/" + interface_name + "/index.html", **args)
        else:
            current_app.logger.debug('Unsuccessful login attempt')
            return {"status": "Could Not Log In."}

    return __func()


def login_info():
    @login_required
    def __func():
        if current_user.is_authenticated:
            return json.dumps({"auth_token": current_user.get_auth_token()})
        else:
            current_app.logger.debug('Unsuccessful login attempt')
            return {"status": "Could Not Log In."}

    return __func()


def read_all_widgets():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/apps'])
    def __func():
        return {_app: helpers.list_widgets(_app) for _app in helpers.list_apps()}

    return __func()


def validate_path(directory, filename):
    """ Checks that the filename is inside of the given directory
    Args:
        directory (str): The directory in which to search
        filename (str): The given filename

    Returns:
        (str): The sanitized path of the filename if valid, else None
    """
    base_abs_path = os.path.abspath(directory)
    normalized = os.path.normpath(os.path.join(base_abs_path, filename))
    return normalized if normalized.startswith(base_abs_path) else None


def read_client_file(filename):
    file = validate_path(core.config.paths.client_path, filename)
    if file is not None:
        return send_file(file), 200
    else:
        return {"error": "invalid path"}, 463
