import json
import os
import sys
import logging

from flask import render_template, redirect, url_for, send_from_directory
from flask_security import login_required, auth_token_required, current_user, roles_accepted
from flask_security.utils import encrypt_password
from gevent import monkey
import xml.dom.minidom as minidom
from xml.etree import ElementTree
import core.config.config
import core.config.paths
import core.filters
import core.flags
from core import helpers

from core.helpers import combine_dicts
from server.context import running_context
from . import database, interface
from server import app

logger = logging.getLogger(__name__)

monkey.patch_all()

urls = ['/', '/key', '/playbooks', '/configuration', '/interface', '/execution/listener',
        '/execution/listener/triggers', '/metrics',
        '/roles', '/users', '/configuration', '/cases', '/apps', '/execution/scheduler']

default_urls = urls
database.initialize_user_roles(urls)


# Creates Test Data
@app.before_first_request
def create_user():
    running_context.db.create_all()

    if not database.User.query.first():
        admin_role = running_context.user_datastore.create_role(name='admin',
                                                                description='administrator',
                                                                pages=default_urls)

        u = running_context.user_datastore.create_user(email='admin', password=encrypt_password('admin'))
        running_context.user_datastore.add_role_to_user(u, admin_role)
        running_context.db.session.commit()

    apps = set(helpers.list_apps()) - set([_app.name
                                           for _app in running_context.db.session.query(running_context.App).all()])
    app.logger.debug('Found apps: {0}'.format(apps))
    for app_name in apps:
        running_context.db.session.add(running_context.App(app=app_name, devices=[]))
    running_context.db.session.commit()

    running_context.CaseSubscription.sync_to_subscriptions()

    app.logger.handlers = logging.getLogger('server').handlers

# This is required by zone.js as it need to access the
# "main.js" file in the "ClientApp\app" folder which it
# does by accessing "<your-site-path>/app/main.js"
# @app.route('/app/<path:filename>')
# def client_app_app_folder(filename):
#     return send_from_directory(os.path.join(core.config.paths.client_path, "app"), filename)

# Custom static data
@app.route('/client/<path:filename>')
def client_app_folder(filename):
    return send_from_directory(os.path.abspath(core.config.paths.client_path), filename)

# @app.route('/')
# @login_required
# def default():
#     if current_user.is_authenticated:
#         default_page_name = 'dashboard'
#         args = {"apps": running_context.get_apps(),
#                 "authKey": current_user.get_auth_token(),
#                 "currentUser": current_user.email,
#                 "default_page": default_page_name}
#         return render_template("container.html", **args)
#     else:
#         return {"status": "Could Not Log In."}

@app.route('/')
@app.route('/controller')
@app.route('/playbook')
@app.route('/devices')
@app.route('/triggers')
@app.route('/cases')
@app.route('/settings')
def default():
    if current_user.is_authenticated:
        args = {"apps": running_context.get_apps(),
                "authKey": current_user.get_auth_token(),
                "currentUser": current_user.email,
                "default_page": 'controller'}
        return render_template("index.html", **args)
    else:
        return redirect(url_for('login'))

# @app.route('/login', methods=['GET'])
# def login():
#     return render_template("login_user.html")

@app.route('/availablesubscriptions', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/cases'])
def display_possible_subscriptions():
    return json.dumps(core.config.config.possible_events)


# Returns System-Level Interface Pages
@app.route('/interface/<string:name>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/interface'])
def sys_pages(name):
    if current_user.is_authenticated and name:
        args = getattr(interface, name)()
        combine_dicts(args, {"authKey": current_user.get_auth_token()})
        return render_template("pages/" + name + "/index.html", **args)
    else:
        app.logger.debug('Unsuccessful login attempt')
        return {"status": "Could Not Log In."}


# TODO: DELETE
@app.route('/interface/<string:name>/display', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/interface'])
def system_pages(name):
    if current_user.is_authenticated and name:
        args = getattr(interface, name)()
        combine_dicts(args, {"authKey": current_user.get_auth_token()})
        return render_template("pages/" + name + "/index.html", **args)
    else:
        return {"status": "Could Not Log In."}


# Returns the API key for the user
@app.route('/key', methods=['GET', 'POST'])
@login_required
def login_info():
    if current_user.is_authenticated:
        return json.dumps({"auth_token": current_user.get_auth_token()})
    else:
        app.logger.debug('Unsuccessful login attempt')
        return {"status": "Could Not Log In."}


@app.route('/widgets', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/apps'])
def list_all_widgets():
    return json.dumps({_app: helpers.list_widgets(_app) for _app in helpers.list_apps()})


def write_playbook_to_file(playbook_name):
    playbook_filename = os.path.join(core.config.paths.workflows_path, '{0}.playbook'.format(playbook_name))
    backup = None
    try:
        with open(playbook_filename) as original_file:
            backup = original_file.read()
        os.remove(playbook_filename)
    except (IOError, OSError):
        pass

    app.logger.debug('Writing playbook {0} to file'.format(playbook_name))
    write_format = 'w' if sys.version_info[0] == 2 else 'wb'

    try:
        with open(playbook_filename, write_format) as workflow_out:
            xml = ElementTree.tostring(running_context.controller.playbook_to_xml(playbook_name))
            xml_dom = minidom.parseString(xml).toprettyxml(indent='\t')
            workflow_out.write(xml_dom.encode('utf-8'))
    except Exception as e:
        logger.error('Could not save playbook to file. Reverting file to original. '
                     'Error: {0}'.format(helpers.format_exception_message(e)))
        with open(playbook_filename, 'w') as f:
            f.write(backup)
