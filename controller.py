from datetime import datetime
from model import Device, Script, History, User
from datetime import timedelta
import time
import mysql.connector

DB_CONFIG = {
    'user': 'root',
    'password': '11111111',
    'host': '127.0.0.1',
    'database': 'omis'
}


class UserController:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def create_user(self, login):
        user = User(len(self.user_repository.users) + 1, login)  # Простое добавление ID
        self.user_repository.add(user)
        return user

class DeviceController:
    def __init__(self, device_repository):
        self.device_repository = device_repository

    def add_device(self, name):
        try:
            mydb = mysql.connector.connect(**DB_CONFIG)
            cursor = mydb.cursor()

            # Check if a device with the same name already exists
            cursor.execute("SELECT * FROM Devices WHERE name = %s", (name,))
            existing_device = cursor.fetchone()
            if existing_device:
                return "Устройство с таким именем уже существует."

            sql = "INSERT INTO Devices (name) VALUES (%s)"
            val = (name,)
            cursor.execute(sql, val)
            mydb.commit()

            device_id = cursor.lastrowid  # Get the ID of the inserted device
            device = Device(device_id, name)
            self.device_repository.add(device)
            return "Устройство успешно добавлено"

        except Exception as e:
            return str(e)

        finally:
            if mydb.is_connected():
                cursor.close()
                mydb.close()


class ScriptController:

    def __init__(self, script_repository, device_repository):
        self.script_repository = script_repository 
        self.device_repository = device_repository

    def create_script(self, name, device_id, duration_str):
        try:
            mydb = mysql.connector.connect(**DB_CONFIG)
            cursor = mydb.cursor()

            duration = int(duration_str)

            sql = "INSERT INTO Scripts (name, device_id, duration) VALUES (%s, %s, %s)"
            val = (name, device_id, duration)
            cursor.execute(sql, val)
            mydb.commit()

            script_id = cursor.lastrowid

            device = next((dev for dev in self.device_repository.devices if dev.id == device_id), None)

            if not device:  # Check if the device exists in the repository
                raise ValueError(f"Device with ID {device_id} not found.")
            


            script = Script(script_id, name, device_id, timedelta(seconds=duration))

            self.script_repository.add(script)
            return script

        except Exception as e:
            return str(e)

        finally:
            if mydb.is_connected():
                cursor.close()
                mydb.close()


class CommandController:
    def __init__(self, command_manager, device_manager, device_repository, history_controller):
        self.command_manager = command_manager
        self.device_manager = device_manager
        self.device_repository = device_repository
        self.history_controller = history_controller

    def process_voice_command(self, user_id, command_str):
        try:
            mydb = mysql.connector.connect(**DB_CONFIG)
            cursor = mydb.cursor()
            cursor.execute("SELECT name FROM Devices")
            db_devices = [d[0] for d in cursor.fetchall()]

            parts = command_str.split()

            if len(parts) < 2:
                return "Неизвестная команда"

            device_found = False
            for device_name in db_devices:
                if device_name.lower() in command_str.lower():
                    print("Начало работы...")
                    device = next((d for d in self.device_repository.devices if d.name.lower() == device_name.lower()), None)

                    if device:
                        time.sleep(5)
                        print("Завершение работы")
                        self.history_controller.add_history_entry(device, "запуск")
                        device_found = True
                        return f"Устройство {device_name} запущено"
                        
                    else:
                        raise ValueError(f"Device '{device_name}' not found in the repository")

                    break



            if not device_found:
                device_name = " ".join(parts[:-1])
                action = parts[-1]

                device = next((d for d in self.device_repository.devices if d.name.lower() == device_name.lower()), None)

                if not device:
                       return "Устройство не найдено"


                if action.lower() in ("включить", "выключить"):
                    print(f"{action.capitalize()} устройство {device_name}")
                    self.history_controller.add_history_entry(device, action) # Pass device object
                    return f"Устройство {device_name} {action}но"


                else:
                    return "Неизвестная команда"



        except Exception as e:
            return f"Ошибка при обработке команды: {e}"

        finally:
            if mydb.is_connected():
                cursor.close()
                mydb.close()
               
               
    def run_device(self, device_id, duration): # Fixed: use device_id instead of device_name and action_type
        try:
            mydb = mysql.connector.connect(**DB_CONFIG)
            cursor = mydb.cursor()

            cursor.execute("SELECT name FROM Devices WHERE id = %s", (device_id,))
            result = cursor.fetchone()


            if not result:
                return f"Устройство с ID '{device_id}' не найдено."

            device_name = result[0]

            print(f"Начало работы {device_name}...")  # Replace with actual device control logic
            time.sleep(duration)  # Simulate device operation
            print(f"Завершение работы {device_name}")


            return True

        except Exception as e:
            return str(e) # return error message
        finally:
            if mydb.is_connected():
                cursor.close()
                mydb.close()
    

class HistoryController:
    def __init__(self, history_repository):
        self.history_repository = history_repository

    def add_history_entry(self, device, action):
        try:
            mydb = mysql.connector.connect(**DB_CONFIG)
            cursor = mydb.cursor()

            sql = "INSERT INTO History (device_name, time) VALUES (%s, %s)"
            val = (device.name, datetime.now()) # Use datetime.now() here

            cursor.execute(sql, val)
            mydb.commit()
            name = str(device.name)
            print(f"Добавлено в историю: {name} - {datetime.now()}") # Use datetime.now() or entry.time for printing


        except Exception as e:
            print(f"Ошибка добавления в историю: {e}")
        finally:
            if mydb.is_connected():
                cursor.close()
                mydb.close()