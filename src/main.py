# Author : Mathias Amato
# Name : Fyle
# Date : 01.03.2024
# Description : Small app allowing the user to encrypt any file, open it only from the application, and decrypt it at any time

import PyQt6
from PyQt6 import QtWidgets, QtGui, QtCore
from cryptography.fernet import Fernet
import json
import random
import os
import shutil
import hashlib
from functions import Functions

class MainApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FYLE - File Securing App")
        self.setWindowIcon(QtGui.QIcon("/home/mathias/ECOLE/file-securing-app/src/logo.png"))
        self.setGeometry(100, 100, 400, 700)
        self.functions_object = Functions()
        self.setup_ui()

    #Add or update the list of encrypted files on the front-end
    def set_list_of_files(self):
        self.list_widget.clear() #Clear all the elements of the list for update
        data = self.functions_object.get_list_of_encrypted_files()
        for file in data:
            item_file = QtWidgets.QListWidgetItem(f"{file['original_file_path']}")
            item_file.setToolTip(file["original_file_path"]) #Help recover the file path to find the object in the json file
            self.list_widget.addItem(item_file)

    #Setup the interface of the application
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        app_name_label = QtWidgets.QLabel("FYLE")
        app_name_label.setFont(QtGui.QFont("Arial", 20))      
        layout.addWidget(app_name_label)

        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setFont(QtGui.QFont("Arial", 11))
        self.set_list_of_files()
        layout.addWidget(self.list_widget)
        

        encryption_button = QtWidgets.QPushButton("Encrypt a file", self)
        encryption_button.clicked.connect(self.perform_encryption)
        
        decryption_button = QtWidgets.QPushButton("Decrypt", self)
        decryption_button.clicked.connect(self.perform_decryption)
        
        open_file_button = QtWidgets.QPushButton("Open file", self)
        open_file_button.clicked.connect(self.perform_open_file)

        encryption_button.setFont(QtGui.QFont("Arial", 14))
        decryption_button.setFont(QtGui.QFont("Arial", 14))
        open_file_button.setFont(QtGui.QFont("Arial", 14))
        
        button_layout_ende = QtWidgets.QHBoxLayout()
        button_layout_ende.addWidget(encryption_button)
        button_layout_ende.addWidget(decryption_button)
        
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.addLayout(button_layout_ende)
        button_layout.addWidget(open_file_button)

        layout.addLayout(button_layout)

        self.footer_label = QtWidgets.QLabel("© 2024 Mathias Amato - CFPT", self)
        self.footer_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setStyleSheet("color: #FFFFFF;")

        layout.addWidget(self.footer_label)

        self.setStyleSheet(
            "QWidget { background-color: #1E1E1E; color: #FFFFFF; }"
            "QListWidget { border: none; background-color: #252525; color: #FFFFFF; }"
            "QListWidget::item { height: 40px; }"
            "QPushButton { background-color: transparent; color: #FFFFFF; padding: 10px; border: 1px solid #3498db; border-radius: 5px; }"
        )

        #Disable the decrypt and open file buttons while no file is selected
        decryption_button.setEnabled(False)
        decryption_button.setStyleSheet("border: 1px solid gray; color: gray;")
        
        open_file_button.setEnabled(False)
        open_file_button.setStyleSheet("border: 1px solid gray; color: gray;")
        
        buttons = [decryption_button, open_file_button]

        self.list_widget.itemSelectionChanged.connect(lambda: self.update_button_state(buttons))

    #Enable or disable the decrypt and open file buttons, depending on if a file is selected or not
    def update_button_state(self, buttons):
        state = bool(self.list_widget.selectedItems())
        for button in buttons:
            button.setEnabled(state)
            if state:
                button.setStyleSheet("background-color: transparent; color: #FFFFFF; padding: 10px; border: 1px solid #3498db; border-radius: 5px;")
            else:
                button.setStyleSheet("border: 1px solid gray; color: gray;")

    #Call the encryption method in functions.py and update the list on the front-end
    def perform_encryption(self):
        self.functions_object.encrypt_selected_file()
        self.set_list_of_files()

    #Call the decryption method in functions.py and update the list on the front-end
    def perform_decryption(self):
        self.functions_object.decrypt_selected_file(self.list_widget.currentItem())
        self.set_list_of_files()
    
    #Call the method that opens a file in functions.py
    def perform_open_file(self):
        self.functions_object.open_file_using_default_app(self.list_widget.currentItem().toolTip())

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    mobile_app = MainApp()
    mobile_app.show()
    app.exec()
