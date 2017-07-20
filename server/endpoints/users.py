from flask import request, current_app
from flask_security import roles_accepted
from flask_security.utils import encrypt_password
from server import forms
from server.return_codes import *


def read_all_users():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        result = [user.display() for user in running_context.User.query.all()]

        return result, SUCCESS
    return __func()


def create_user():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        data = request.get_json()
        un = data['username']
        if not running_context.User.query.filter_by(email=un).first():
            pw = encrypt_password(data['password'])

            # Creates User
            u = running_context.user_datastore.create_user(email=un, password=pw, active=data['active'])

            if 'roles' in data:
                u.set_roles(data['roles'])

            has_admin = False
            for role in u.roles:
                if role.name == 'admin':
                    has_admin = True
            if not has_admin:
                u.set_roles(['admin'])

            running_context.db.session.commit()
            current_app.logger.info('User added: {0}'.format(
                {"name": u.email, "roles": [str(_role) for _role in u.roles]}))
            return u.display(), OBJECT_CREATED
        else:
            current_app.logger.warning('Could not create user {0}. User already exists.'.format(un))
            return {"error": "User {0} already exists.".format(un)}, OBJECT_EXISTS_ERROR
    return __func()


def read_user(user_id):
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        user = running_context.user_datastore.get_user(user_id)
        if user:
            return user.display(), SUCCESS
        else:
            current_app.logger.error('Could not display user {0}. User does not exist.'.format(user_id))
            return {"error": 'User with id {0} does not exist.'.format(user_id)}, OBJECT_DNE_ERROR
    return __func()


def update_user():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        data = request.get_json()
        new_username = data['username']

        user = running_context.user_datastore.get_user(new_username)
        if user:
            current_username = user.email

            if 'active' in data:
                user.active = data['active']
            if 'password' in data:
                user.password = encrypt_password(form.password.data)
            if 'roles' in data:
                user.set_roles(data['roles'])

            running_context.db.session.commit()
            current_app.logger.info('Updated user {0}. Roles: {1}'.format(current_username, data['roles']))
            return user.display(), SUCCESS
        else:
            current_app.logger.error('Could not edit user {0}. User does not exist.'.format(new_username))
            return {"error": 'User {0} does not exist.'.format(new_username)}, OBJECT_DNE_ERROR
    return __func()


def delete_user(user_id):
    from server.flaskserver import running_context, current_user

    @roles_accepted(*running_context.user_roles['/users'])
    def __func():
        user = running_context.user_datastore.get_user(user_id)
        if user:
            if user != current_user:
                running_context.user_datastore.delete_user(user)
                running_context.db.session.commit()
                current_app.logger.info('User {0} deleted'.format(user.email))
                return {}, SUCCESS
            else:
                current_app.logger.error('Could not delete user {0}. User is current user.'.format(user.email))
                return {"error": 'User {0} is current user.'.format(user.email)}, UNAUTHORIZED_ERROR
        else:
            current_app.logger.error('Could not delete user {0}. User does not exist.'.format(user_id))
            return {"error": 'User with id {0} does not exist.'.format(user_id)}, OBJECT_DNE_ERROR
    return __func()
