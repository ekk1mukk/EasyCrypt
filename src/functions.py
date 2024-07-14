# Author : Mathias Amato
# Name : Fyle
# Date : 01.03.2024
# Description : Small app allowing the user to encrypt any file, open it only from the application, and decrypt it at any time

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from cryptography.fernet import Fernet
import json
import random
import os
import shutil
import hashlib
import threading
import time
import psutil
import re
import mimetypes

class Functions():
    def __init__(self):
        self.files_opened = []
        self.MAX_FILE_SIZE = 500*1024*1024 #500 MB
        pass

    #Send a popup showing an error and the reason for it
    def show_error_popup(self, reason):
        error_dialog = QErrorMessage()
        error_dialog.setWindowTitle("Error")
        error_dialog.showMessage(reason)
        error_dialog.exec()

    #Allows to add encrypted files to the front-end list, returns the object fetched from the json
    def get_list_of_encrypted_files(self):
        try:
            with open("./files_list.json", "r") as json_file:
                all_files = json.load(json_file) #Fetch from the json file

                return all_files
        except Exception:
            self.show_error_popup("Error while fetching the list of encrypted files.")

    #Take a decrypted file and encrypt it
    def write_encrypted_file(self, filepath, key):
        fernet = Fernet(key) #Use Fernet algorithm

        with open(filepath, 'rb') as file:
            file_to_encrypt = file.read() #Read the content of the file

        encrypted = fernet.encrypt(file_to_encrypt)

        with open(filepath, 'wb') as encrypted_file:
            encrypted_file.write(encrypted) #Write the encrypted content to the file

    #Take the encrypted file and decrypt it, returns the file object from the json and the key
    def write_decrypted_file(self, filepath):
        with open("./files_list.json", "r") as json_file:
            all_files = json.load(json_file)

        #Find in the object fetched from the json file, the relevant file object
        file_object = next((obj for obj in all_files if obj.get("original_file_path") == filepath), None)

        if not file_object:
            self.show_error_popup("File not found.")
            return 0, 0, 0

        if file_object['file_id'] in self.files_opened:
            self.show_error_popup("File is currently opened. Close it first.")
            return 0, 0, 0

        with open(file_object["file_key"], 'rb') as file: #Get the key
            key = file.read()

        fernet = Fernet(key)

        with open(file_object['encrypted_file_path'], 'rb') as enc_file:
            encrypted_file = enc_file.read() #Read the content of the encrypted file

        decrypted = fernet.decrypt(encrypted_file)

        with open(file_object['encrypted_file_path'], 'wb') as decrypted_file:
            decrypted_file.write(decrypted) #Write the decrypted content in the file

        return file_object, key, all_files

    #Open the file dialog, encrypt the selected file (write_encrypted_file) and move it to a special folder
    def encrypt_selected_file(self):

        try:
            self.file_path, _ = QFileDialog.getOpenFileName(None, 'Encrypt file', '.') #Open file dialog to select a file to encrypt
            if not self.file_path:
                return

            file_size = os.path.getsize(self.file_path)

            if file_size > self.MAX_FILE_SIZE: #If the file is bigger thant the authorized size, show an error
                self.show_error_popup("This file is too big. Maximum allowed is : " + str(self.MAX_FILE_SIZE/1024/1024) + "MB.")
                return

            file_path_hash = hashlib.sha256(self.file_path.encode('utf-8')).hexdigest() #Hash the file path in sha256

            file_name = self.file_path.split('/')[-1] #Take the string after the last / (the file name)

            file_obj = { #Init a new object
                "file_id": file_path_hash, #The hashed name of the file
                "extension": "",
                "encrypted_file_path": "", #The path of the encrpted file
                "original_file_path": self.file_path, #The original path of the file before encryption
                "original_file_name": file_name, #The original file name before encryption
                "file_key": "" #The path of the file containing the key
            }

            key = Fernet.generate_key()


            self.write_encrypted_file(self.file_path, key)

            with open("./files_list.json", "r") as json_file:
                all_files = json.load(json_file)

            #Write the file containing the key
            with open(f'./encrypted_files_and_keys/{file_obj["file_id"]}.key', 'wb') as filekey:
                filekey.write(key)
                self.file_key = filekey.name

            file_obj["extension"] = os.path.splitext(self.file_path)[1]
            file_obj["file_key"] = self.file_key
            file_obj['encrypted_file_path'] = f"./encrypted_files_and_keys/{file_obj['file_id']}{file_obj['extension']}"

            all_files.append(file_obj) #Add the new object to the set of objects

            with open("./files_list.json", "w") as json_file:
                json.dump(all_files, json_file, indent=4) #Update the json file with the new object

            shutil.move(self.file_path, file_obj['encrypted_file_path']) #Move the file from the original path to the new path
        except Exception:
            self.show_error_popup("Error while encrypting. Maybe Fyle is missing some permissions.")

    #Decrypt the selected file in the front-end list and move it to its original path
    def decrypt_selected_file(self, current_item):

        try:
            #Trick to easily get the original file path in the case that the name of the element of the list is not the complete path
            self.file_path = current_item.toolTip()

            file_object, _, all_files = self.write_decrypted_file(self.file_path) #Getting the key is useless here

            if file_object == 0 and all_files == 0:
                return

            shutil.move(file_object['encrypted_file_path'], f"{file_object['original_file_path']}") #Move the file to its original path
            os.remove(file_object['file_key']) #Remove the file containing the key

            index_to_remove = next(index for index, file_obj in enumerate(all_files) if file_obj['file_id'] == file_object['file_id'])
            all_files.pop(index_to_remove)

            with open("./files_list.json", "w") as json_file:
                json.dump(all_files, json_file, indent=4) #Update the json file without theobject of the decrypted file
        except Exception:
            self.show_error_popup("Error while decrypting. Maybe Fyle is missing some permissions.")

    #Temporarely decrypt and open the selected file in the front-end list and using the operating system's default app
    def open_file_using_default_app(self, filepath):

        try:

            file_object, key, _ = self.write_decrypted_file(filepath)

            if file_object == 0 and key == 0:
                return

            full_path = os.path.abspath("encrypted_files_and_keys/" + file_object['file_id'] + file_object['extension'])

            print(full_path)
            #Open the file using the OS's default app
            QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))

            time.sleep(1) #Let the file open

            #Start a new thread for the app
            monitor_thread = threading.Thread(target=self.monitor_file_use_and_encrypt_back_if_closed, args=(file_object['encrypted_file_path'], key, file_object))
            monitor_thread.start()

            self.files_opened.append(file_object['file_id'])

        except Exception as e:
            print(e)
            self.show_error_popup(f"Error while opening the file: {e}")

    #Running in a separate thread, check if the default app is still in use, and encrypt it back if not
    def monitor_file_use_and_encrypt_back_if_closed(self, encrypted_file_path, key, file_object):
        try:
            while True:
                process_found = False
                cmdline = ''
                for process in psutil.process_iter(attrs=["cmdline"]): #Loop through each process...
                    if process.info["cmdline"] is not None:
                        cmdline = ''.join(process.info["cmdline"]) #...and make it one string

                    if re.search(file_object['file_id'], cmdline): #Search inside the string for the right process using the hashed name of the file in the command
                        process_found = True
                        break

                if not process_found: #If the process is not found thus the app has been closed
                    self.write_encrypted_file(encrypted_file_path, key)
                    index_to_remove = next(index for index, file_id in enumerate(self.files_opened) if file_id == file_object['file_id'])
                    self.files_opened.pop(index_to_remove)
                    break

                time.sleep(1) #Slow down the loop to preserve CPU use
        except Exception:
            self.show_error_popup("Error while monitoring file usage.")
