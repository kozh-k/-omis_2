import tkinter as tk
from tkinter import simpledialog
from model import User, Device, Script, History, UserRepository, DeviceRepository, ScriptRepository, HistoryRepository
from controller import UserController, DeviceController, ScriptController, CommandController, HistoryController
from view import MainView
import mysql.connector
from tkinter import messagebox
from datetime import datetime, timedelta

DB_CONFIG = {
    'user': 'root',
    'password': '11111111',
    'host': '127.0.0.1',
    'database': 'omis'
}


class Application:
    def __init__(self):

        self.user_repository = UserRepository()
        self.device_repository = DeviceRepository()
        self.script_repository = ScriptRepository()
        self.history_repository = HistoryRepository()

        self.user_controller = UserController(self.user_repository)
        self.device_controller = DeviceController(self.device_repository)
        self.script_controller = ScriptController(self.script_repository, self.device_repository)
        self.history_controller = HistoryController(self.history_repository)
        self.command_controller = CommandController(None, self.device_controller, self.device_repository, self.history_controller)


        self.user_controller.create_user('test_user')
        self.device_controller.add_device('Лампа')
        self.device_controller.add_device('Телевизор')
        self.user_controller.create_user('test_user')
        
        self.load_devices_from_db()
        self.load_scripts_from_db()
        

        try: # Add initial devices on startup from database
            mydb = mysql.connector.connect(**DB_CONFIG)
            cursor = mydb.cursor()

            cursor.execute("SELECT * from devices") # add all devices to app memory on startup
            devices = cursor.fetchall()
            for device in devices:
                self.device_controller.add_device(device[1])


        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
        finally:
            if mydb.is_connected():
                cursor.close()
                mydb.close()

        self.main_view = MainView(self)

    def load_devices_from_db(self):
        try:
            mydb = mysql.connector.connect(**DB_CONFIG)
            cursor = mydb.cursor()
            cursor.execute("SELECT id, name FROM Devices")  # Select all devices
            devices = cursor.fetchall()
            
            

            self.device_repository.devices.clear()  # Clear the existing device list in the repository
            for device_id, device_name in devices:
                device = Device(device_id, device_name)
                self.device_repository.add(device)
                
            return self.device_repository.devices  # Return device list

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки устройств из БД: {e}")
            return []

        finally:
            if mydb.is_connected():
                cursor.close()
                mydb.close()
                
    def load_scripts_from_db(self):
        try:
            mydb = mysql.connector.connect(**DB_CONFIG)
            cursor = mydb.cursor()
            cursor.execute("SELECT id, name, device_id, duration FROM Scripts")
            scripts_data = cursor.fetchall()

            self.script_repository.scripts.clear()  # Clear existing scripts before loading new ones
            for script_data in scripts_data:
                script_id, name, device_id, duration = script_data

                device = next((d for d in self.device_repository.devices if d.id == device_id), None)

                if device: # if device exists in repository
                    script = Script(script_id, name, device_id, timedelta(seconds=duration))
                    self.script_repository.add(script) # then add script to repository
                else: # do not load scripts for non-existent devices
                    print(f"Warning: Device with ID {device_id} not found in the device_repository. Skipping script '{name}'.")
                    

        except Exception as e:
            print(f"Ошибка при загрузке сценариев из БД: {e}")
        finally:
            if mydb.is_connected():
                cursor.close()
                mydb.close()

    def run(self):
        self.main_view.mainloop()


if __name__ == "__main__":
    app = Application()
    app.run()