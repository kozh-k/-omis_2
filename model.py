from datetime import datetime, timedelta

class User:
    def __init__(self, id, login):
        self.id = id
        self.login = login
        self.devices = []

class Device:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.status = "off"

    def turn_on(self):
        self.status = "on"

    def turn_off(self):
        self.status = "off"

class Script:
    def __init__(self, id, name, device_id, duration):
        self.id = id
        self.name = name
        self.device_id = device_id
        self.duration = duration

class History:
    def __init__(self, id, device_name, action, time):
        self.id = id
        self.device_name = device_name
        self.action = action
        self.time = time



class UserRepository:
    def __init__(self):
        self.users = []

    def add(self, user):
        self.users.append(user)


class DeviceRepository:
    def __init__(self):
        self.devices = []

    def add(self, device):
        self.devices.append(device)

class ScriptRepository:
    def __init__(self):
        self.scripts = []

    def add(self, script):
        self.scripts.append(script)


class HistoryRepository:
    def __init__(self):
        self.history = []

    def add(self, history_entry):
        self.history.append(history_entry)