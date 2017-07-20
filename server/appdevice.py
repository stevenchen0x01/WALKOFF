import json
from abc import abstractmethod
from flask import current_app
from sqlalchemy import Integer, String
# from core.api import WalkoffAppDefinition
from . import database
import core.config.paths
import pyaes
import logging

db = database.db

logger = logging.getLogger(__name__)


class App(database.Base, object):
    __tablename__ = 'app'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    devices = db.relationship("Device", back_populates="app")

    def as_json(self, with_devices=False):
        """Gets the JSON representation of an App object.
        
        Returns:
            The JSON representation of an App object.
        """
        output = {'id': str(self.id), 'name': self.name}
        if with_devices:
            output['devices'] = [device.as_json() for device in self.devices]
        return output

    def __init__(self, app=None, devices=None):
        """Initializes an App object.
        
        Args:
            app (str, optional): The name of the app. Defaults to None.
            devices (list[str], optional): The list of device names to be associated with the App object. There is a
                one to many mapping from Apps to Devices.
        """
        self.name = app
        self.devices = [Device(name=device_name) for device_name in devices]

    def initialize(self):
        # self.api = WalkoffAppDefinition(self.name, self)
        pass

    @staticmethod
    def get_all_devices_for_app(app_name):
        """ Gets all the devices associated with an app

        Args:
            app_name (str): The name of the app
        Returns:
            (list[Device]): A list of devices associated with this app. Returns empty list if app is not in database
        """
        app = App.query.filter_by(name=app_name).first()
        if app is not None:
            return app.devices
        else:
            logger.warning('Cannot get devices for app {0}. App does not exist'.format(app_name))
            return []

    @staticmethod
    def get_device(app_name, device_name):
        """ Gets the device associated with an app

        Args:
            app_name (str): The name of the app
            device_name (str): The name of the device
        Returns:
            (Device): The desired device. Returns None if app or device not found.
        """
        app = App.query.filter_by(name=app_name).first()
        if app is not None:
            # efficient generator to get first instance of device with matching name. returns None if not found
            device = next((device for device in app.devices if device.name == device_name), None)
            if device is not None:
                return device
            else:
                logger.warning('Cannot get device {0} for app {1}. '
                               'Device does not exist for app'.format(device_name, app_name))
                return None
        else:
            logger.warning('Cannot get device {0} for app {1}. App does not exist'.format(device_name, app_name))
            return None

    @abstractmethod
    def shutdown(self):
        pass


class Device(database.Base):
    __tablename__ = 'device'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    username = db.Column(db.String(80))
    password = db.Column(db.LargeBinary())
    ip = db.Column(db.String(15))
    port = db.Column(db.Integer())
    extra_fields = db.Column(db.String)
    app_id = db.Column(db.String, db.ForeignKey('app.name'))
    app = db.relationship(App, back_populates="devices")

    def __init__(self, name="", username="", password=None, ip="0.0.0.0", port=0, extra_fields="", app_id=""):
        """Initializes a new Device object, which will be associated with an App object.
        
        Args:
            name (str, optional): The name of the Device object. Defaults to an empty string.
            username (str, optional): The username for the Device object. Defaults to an empty string.
            password (str, optional): The password for the Device object. Defaults to an empty string.
            ip (str, optional): The IP address for for the Device object. Defaults to "0.0.0.0".
            port (int, optional): The port for the Device object. Defaults to 0.
            extra_fields (str, optional): The string representation of a dictionary that holds various custom
                extra fields for the Device object. Defaults to an empty string.
            app_id (str, optional): The ID of the App object to which this Device is associated. Defaults to an 
                empty string.
        """
        self.name = name
        self.username = username
        self.password = password
        self.ip = ip
        self.port = port
        self.app_id = app_id
        if self.extra_fields != "":
            self.extra_fields = extra_fields.replace("\'", "\"")
        else:
            self.extra_fields = extra_fields

    @staticmethod
    def add_device(name, username, password, ip, port, extra_fields, app_server):
        """Adds a new Device object.
        
        Args:
            name (str, optional): The name of the Device object. Defaults to an empty string.
            username (str, optional): The username for the Device object. Defaults to an empty string.
            password (str, optional): The password for the Device object. Defaults to an empty string.
            ip (str, optional): The IP address for for the Device object. Defaults to "0.0.0.0".
            port (int, optional): The port for the Device object. Defaults to 0.
            extra_fields (str, optional): The string representation of a dictionary that holds various custom
            extra fields for the Device object. Defaults to an empty string.
            app_server (str, optional): The ID of the App object to which this Device is associated. Defaults to an 
            empty string.
        """
        device = Device(name=name, username=username, password=password, ip=ip, port=port, extra_fields=extra_fields,
                        app_id=app_server)
        db.session.add(device)
        db.session.commit()
        current_app.logger.info('Adding device to app {0}: {1}'.format(app_server, device.as_json(with_apps=False)))

    def get_password(self):
        try:
            with open(core.config.paths.AES_key_path, 'rb') as key_file:
                key = key_file.read()
        except (OSError, IOError):
            current_app.logger.error('No AES key found')
            return None
        else:
            aes = pyaes.AESModeOfOperationCTR(key)
            return aes.decrypt(self.password)

    def edit_device(self, form):
        """Edits various fields of the Device object. 
        
        Args:
            form (WTForm): The WTForm object containing the fields that the user wishes to change.
        """
        if form.name.data:
            self.name = form.name.data

        if form.username.data:
            self.username = form.username.data

        if form.pw.data:
            try:
                with open(core.config.paths.AES_key_path, 'rb') as key_file:
                    key = key_file.read()
            except (OSError, IOError) as e:
                current_app.logger.error('Error loading AES key from from {0}: '
                                         '{1}'.format(core.config.paths.AES_key_path, e))
            else:
                aes = pyaes.AESModeOfOperationCTR(key)
                pw = form.pw.data
                self.password = aes.encrypt(pw)

        if form.ipaddr.data:
            self.ip = form.ipaddr.data

        if form.port.data:
            self.port = form.port.data

        if form.extraFields.data:
            fields_dict = json.loads(form.extraFields.data.replace("\'", "\""))
            if self.extra_fields == "":
                self.extra_fields = form.extraFields.data
            else:
                extra_fields = json.loads(self.extra_fields)
                for field in fields_dict:
                    extra_fields[field] = fields_dict[field]
                self.extra_fields = json.dumps(extra_fields)

    def as_json(self, with_apps=True):
        """Gets the JSON representation of a Device object.
        
        Args:
            with_apps (bool, optional): A boolean to determine whether or not to include the App to which the Device
                is associated in the JSON output. Defaults to True.
                
        Returns:
            The JSON representation of a Device object.
        """
        output = {'id': str(self.id), 'name': self.name, 'username': self.username, 'ip': self.ip,
                  'port': str(self.port)}
        if with_apps:
            output['app'] = self.app.as_json()
        else:
            output['app'] = self.app.name
        if self.extra_fields:
            extra_fields = json.loads(self.extra_fields)
            for field in extra_fields:
                output[field] = extra_fields[field]
        return output

    def __repr__(self):
        return str({"name": self.name, "username": self.username, "password": self.password,
                    "ip": self.ip, "port": str(self.port), "app": self.app.as_json()})
