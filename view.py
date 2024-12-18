import speech_recognition as sr
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import mysql.connector
from model import Script

DB_CONFIG = {
    'user': 'root',
    'password': '11111111',
    'host': '127.0.0.1',
    'database': 'omis'
}

class MainView(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("Умный дом")
        self.create_widgets()


    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.create_voice_tab(notebook)
        self.create_script_tab(notebook)
        self.create_devices_tab(notebook)
        self.create_history_tab(notebook)

    def create_voice_tab(self, notebook):
        voice_frame = ttk.Frame(notebook)
        notebook.add(voice_frame, text="Голосовой ввод")

        voice_button = ttk.Button(voice_frame, text="Произнесите команду", command=self.voice_command_clicked)
        voice_button.pack(pady=20)

        self.command_label = ttk.Label(voice_frame, text="", wraplength=300)
        self.command_label.pack()


    def voice_command_clicked(self):
        r = sr.Recognizer() 

        with sr.Microphone() as source:
            print("Слушаю...")
            audio = r.listen(source)

        try:
            command = r.recognize_google(audio, language="ru-RU")
            messagebox.showinfo("Распознанная команда", f"Вы сказали: {command}")
            user_id = 1
            result = self.controller.command_controller.process_voice_command(user_id, command)
            # self.controller.history_controller.add_history_entry(command.split()[0] if len(command.split()) > 0 else "Неизвестное устройство", command.split()[1] if len(command.split()) > 1 else "Неизвестное действие")
            messagebox.showinfo("Результат", result)


        except sr.UnknownValueError:
            messagebox.showerror("Ошибка", "Не удалось распознать речь.")
        except sr.RequestError as e:
            messagebox.showerror("Ошибка", f"Ошибка запроса к сервису распознавания речи; {e}")



    def create_script_tab(self, notebook):  # Updated for database scripts
        script_frame = ttk.Frame(notebook)
        notebook.add(script_frame, text="Сценарий")

        self.script_combobox = ttk.Combobox(script_frame, values=[])
        self.script_combobox.pack(pady=10)
        self.update_script_combobox()  # Called here to populate on startup

        run_button = ttk.Button(script_frame, text="Запустить", command=self.run_script_clicked)
        run_button.pack(pady=10)

        create_button = ttk.Button(script_frame, text="Создать", command=self.create_script_clicked)
        create_button.pack(pady=10)

    def run_script_clicked(self):
        try:
            selected_script_name = self.script_combobox.get()

            print(self.controller.script_repository.scripts)
            script = next((s for s in self.controller.script_repository.scripts if s.name == selected_script_name), None)
            
            if script:
                self.run_script(script)
            else:
                messagebox.showwarning("Сценарий не найден", f"Сценарий '{selected_script_name}' не найден.")


        except Exception as e:
             messagebox.showerror("Ошибка", f"Ошибка при запуске сценария: {e}")
             
    def run_script(self, script):
        try:
            device_id = script.device_id
            duration = script.duration.seconds # in seconds

            messagebox.showinfo("Запуск сценария", f"Сценарий '{script.name}' запущен.")
            print(f"Запуск устройства ID {device_id} на {duration} секунд.")

            device = next((d for d in self.controller.device_repository.devices if d.id == device_id), None)

            if not device:
                raise ValueError(f"Устройство с ID {device_id} не найдено в репозитории.")

            result = self.controller.command_controller.run_device(device_id, duration)

            if isinstance(result, str):  # Check for error from CommandController
                raise ValueError(result)
            
            self.controller.history_controller.add_history_entry(device, f"выполнение сценария '{script.name}'")



        except ValueError as e:
            messagebox.showerror("Ошибка выполнения сценария", str(e))
        

    def update_script_combobox(self):
        try:
            mydb = mysql.connector.connect(**DB_CONFIG)
            cursor = mydb.cursor()
            cursor.execute("SELECT name FROM Scripts") # get all scripts
            scripts = cursor.fetchall()
            self.script_combobox['values'] = [s[0] for s in scripts]  # Update combobox values

            if self.script_combobox['values']:
                self.script_combobox.current(0) # set the first item as selected
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при чтении сценариев из базы данных: {e}")
        finally:
            if mydb.is_connected():
                cursor.close()
                mydb.close()

    def create_script_clicked(self):
        self.devices = self.controller.load_devices_from_db()  # Load devices from DB here
        self.device_options = [d.name for d in self.devices]
       
        self.create_script_window = tk.Toplevel(self)
        self.create_script_window.title("Создание сценария")

        # --- Device Selection ---
        device_label = tk.Label(self.create_script_window, text="Выберите девайс")
        device_label.grid(row=0, column=0, padx=5, pady=5)

        self.device_options = self.get_device_options_from_db()  # Fetch device options from the database
        self.device_var = tk.StringVar(self.create_script_window)
        if self.device_options:
            self.device_var.set(self.device_options[0])  # Set default value if available


        device_dropdown = ttk.Combobox(self.create_script_window, textvariable=self.device_var, values=self.device_options)
        device_dropdown.grid(row=0, column=1, padx=5, pady=5)


        # --- Duration ---
        duration_label = tk.Label(self.create_script_window, text="Продолжительность работы (сек)")
        duration_label.grid(row=1, column=0, padx=5, pady=5) # row = 1 now because there is no start time field
        self.duration_entry = tk.Entry(self.create_script_window)
        self.duration_entry.grid(row=1, column=1, padx=5, pady=5)

      #   --- Action Type ---
      #   action_type_label = tk.Label(self.create_script_window, text="Тип работы (on/off)")
      #   action_type_label.grid(row=2, column=0, padx=5, pady=5) # row=2
      #   self.action_type_entry = tk.Entry(self.create_script_window)
      #   self.action_type_entry.grid(row=2, column=1, padx=5, pady=5)


        # --- Name ---
        name_label = tk.Label(self.create_script_window, text="Название сценария")
        name_label.grid(row=3, column=0, padx=5, pady=5) # row=3
        self.name_entry = tk.Entry(self.create_script_window)
        self.name_entry.grid(row=3, column=1, padx=5, pady=5)


        # --- OK Button ---
        ok_button = ttk.Button(self.create_script_window, text="OK", command=self.create_script_ok_clicked)
        ok_button.grid(row=4, column=0, columnspan=2, pady=10)


    def create_script_ok_clicked(self):
        try:
            selected_device_name = self.device_var.get()
            duration_str = self.duration_entry.get()
            script_name = self.name_entry.get()

            if not all([selected_device_name, duration_str, script_name]):
                raise ValueError('Все поля должны быть заполнены')

            if not duration_str.isdigit():
                raise ValueError("Продолжительность должна быть целым числом.")

            try:
                mydb = mysql.connector.connect(**DB_CONFIG)
                cursor = mydb.cursor()

                cursor.execute("SELECT id FROM Devices WHERE name = %s", (selected_device_name,))
                result = cursor.fetchone()

                if result:
                    device_id = result[0]

                    try:
                        duration = int(duration_str) # parse duration before calling the controller
                        new_script = self.controller.script_controller.create_script(script_name, device_id, duration)


                        if isinstance(new_script, Script):
                            self.controller.load_scripts_from_db()  # Reload scripts from DB
                            self.create_script_window.destroy()
                            self.update_script_combobox()
                            messagebox.showinfo("Сценарий создан", f"Сценарий '{script_name}' успешно создан.")

                        else:  # Handle script creation error
                            messagebox.showerror("Ошибка", f"Ошибка при создании сценария: {new_script}")

                    except ValueError as e: # handle duration parsing errors
                         messagebox.showerror("Ошибка", f"Ошибка при создании сценария: {e}")



                else:
                    raise ValueError(f"Устройство '{selected_device_name}' не найдено в базе данных.")


            except mysql.connector.Error as e:
                messagebox.showerror("Ошибка базы данных", f"Ошибка при работе с базой данных: {e}")

            finally:
                if mydb.is_connected():
                    cursor.close()
                    mydb.close()


        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            
    def get_device_options_from_db(self): # get devices for dropdown
        try:
            mydb = mysql.connector.connect(**DB_CONFIG)
            cursor = mydb.cursor()
            cursor.execute("SELECT name FROM Devices")
            devices = cursor.fetchall()
            device_options = [device[0] for device in devices] # flatten list of tuples
            return device_options
        except mysql.connector.Error as e:
            messagebox.showerror("Ошибка базы данных", f"Ошибка при чтении устройств из базы данных: {e}")
            return [] # return empty list if error
        finally:
            if mydb.is_connected():
                cursor.close()
                mydb.close()

    def create_devices_tab(self, notebook):
        devices_frame = ttk.Frame(notebook)
        notebook.add(devices_frame, text="Девайсы")

        devices_label = ttk.Label(devices_frame, text="Список девайсов")
        devices_label.pack()

        self.devices_listbox = tk.Listbox(devices_frame)
        self.devices_listbox.pack(pady=10)

        self.update_devices_listbox()
        self.devices_listbox.bind("<<ListboxSelect>>", self.device_selected)

        # --- Добавление нового устройства ---
        self.new_device_name = tk.StringVar() # variable for entry text
        new_device_entry = ttk.Entry(devices_frame, textvariable=self.new_device_name)
        new_device_entry.pack(pady=5)

        add_device_button = ttk.Button(devices_frame, text="Добавить девайс", command=self.add_device)
        add_device_button.pack()
        
    def add_device(self):
        device_name = self.new_device_name.get() # get name from input field

        if device_name: # if device name isn't empty
            result = self.controller.device_controller.add_device(device_name) # call device controller method to add the device
            if result == "Устройство успешно добавлено":
                self.update_devices_listbox()
                messagebox.showinfo("Успех", result)
                self.new_device_name.set("") # clear the input field after success

            else:
                messagebox.showerror("Ошибка", result) # show error message from database

        else:
            messagebox.showwarning("Предупреждение", "Введите имя устройства.")


    def update_devices_listbox(self): # update devices listbox from database
        self.devices_listbox.delete(0, tk.END)
        try:
            mydb = mysql.connector.connect(**DB_CONFIG) # using global DB_CONFIG
            cursor = mydb.cursor()
            cursor.execute("SELECT name FROM Devices")
            devices = cursor.fetchall()
            for device in devices:
                self.devices_listbox.insert(tk.END, device[0])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при чтении из базы данных: {e}")
        finally:
            if mydb.is_connected():
                cursor.close()
                mydb.close()


    def device_selected(self, event):
        try:
            selection = self.devices_listbox.curselection()
            if selection:
                index = selection[0]
                selected_device_name = self.devices_listbox.get(index)  # Get the name of the selected device

                try:  # Wrap the database query in a try-except block
                    mydb = mysql.connector.connect(**DB_CONFIG)
                    cursor = mydb.cursor()
                    cursor.execute("SELECT id, name FROM Devices WHERE name = %s", (selected_device_name,))
                    device_data = cursor.fetchone()

                    if device_data:
                        device_id, device_name = device_data
                        device_info = f"ID: {device_id}\nИмя: {device_name}\n"

                        # You can fetch and add more device info here if needed

                        messagebox.showinfo("Информация о девайсе", device_info)
                    else:
                        messagebox.showinfo("Информация о девайсе", "Устройство не найдено в базе данных.")

                except mysql.connector.Error as e:  # Catch database errors
                    messagebox.showerror("Ошибка базы данных", f"Ошибка при чтении из базы данных: {e}")
                finally:  # Always close the database connection
                    if mydb.is_connected():
                        cursor.close()
                        mydb.close()

        except IndexError as e:  # Catch IndexError
            messagebox.showerror("Ошибка", f"Ошибка индекса: {e}") # show error in messagebox



    def create_history_tab(self, notebook):
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="История")

        self.history_text = tk.Text(history_frame, wrap=tk.WORD)
        self.history_text.pack(fill="both", expand=True)
        self.update_history()


    def update_history(self):
      self.history_text.delete("1.0", tk.END)
      try:
         mydb = mysql.connector.connect(**DB_CONFIG)
         cursor = mydb.cursor()
         cursor.execute("SELECT time, device_name FROM History")
         history_entries = cursor.fetchall()

         for entry in history_entries:
               self.history_text.insert(tk.END, f"{entry[0]}: {entry[1]}\n")  # Убрали - {entry[2]}

      except Exception as e:
         messagebox.showerror("Ошибка", f"Ошибка при чтении истории из базы данных: {e}")
      finally:
            if mydb.is_connected():
               cursor.close()
               mydb.close()