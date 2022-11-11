import sys
import time

from time import sleep
from database import Database
from keyboard import hook, unhook, press, release, on_press, unhook_all
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, QListWidget, QCheckBox, QInputDialog, QTableWidget, \
    QTableWidgetItem, QPushButton, QLineEdit, QMessageBox


class Example(QMainWindow, QApplication):
    macro: QListWidget
    keyboard_events: QCheckBox
    tableWidget: QTableWidget
    open_btn: QPushButton
    play_btn: QPushButton
    bind: QPushButton
    bind_key: QLineEdit
    delete_btn: QPushButton

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        uic.loadUi('macro.ui', self)

        self.recording = False
        self.start_stop_btn.toggled.connect(self.setGrabbing)
        self.play_btn.clicked.connect(self.play)
        self.open_btn.clicked.connect(self.open_macro)
        self.bind.clicked.connect(self.get_bind)
        self.delete_btn.clicked.connect(self.delete_item_from_database)
        self.start_stop_btn.setFocusPolicy(Qt.NoFocus)
        self.delays.setFocusPolicy(Qt.NoFocus)
        self.open_btn.setFocusPolicy(Qt.NoFocus)
        self.delete_btn.setFocusPolicy(Qt.NoFocus)
        self.keyboard_events.setFocusPolicy(Qt.NoFocus)
        # Прописываем почти всему setFocusPolicy(Qt.NoFocus) чтобы ничего не реагировало на нажатие пробела
        self.load_table()
        # Загрузка сохраненных макросов из базы данных

        self.is_playing = False
        self.bind_btn_pressed = False
        self.current_bind = None
        self.openned_macro = None

    def keyboardEventReceived(self, event):
        if self.delays.isChecked():
            self.time = time.perf_counter()
            self.macro.addItem(f'{str(round(self.time - self.last_time, 3))} s')
            self.last_time = self.time
        if self.keyboard_events.isChecked():
            key, key_event = self.get_event_info(event)
            if key_event == "down":
                self.macro.addItem(f'{key.lower()} pressed')
            else:
                self.macro.addItem(f'{key.lower()} released')
    # Обработка нажатий на клавиатуру и приведение данных к нужному формату

    def setGrabbing(self, enable):
        if enable:
            self.macro.clear()
            self.last_time = time.perf_counter()
            self.start_stop_btn.setText('stop')
            self.key = hook(self.keyboardEventReceived)
        else:
            self.start_stop_btn.setText('start')
            unhook(self.key)
            self.db = Database('ffing.sqlite')
            self.save_macro()
            self.db.add_events(self.getListFromListWidget())
            self.db.close()
            self.load_table()

    def save_macro(self):
        while True:
            name, ok_pressed = QInputDialog.getText(self, "", "Введите название макроса")
            if ok_pressed:
                if ' ' not in name and name:
                    self.db.create_table(name)
                    break
            else:
                self.macro.clear()
                break
        # При нажатии на кнопку Stop вылезает QInputDialog, где можно сохранить макрос (или не сохранять)

    def getListFromListWidget(self) -> list:
        items = []
        for i in range(self.macro.count()):
            item = self.macro.item(i)
            items.append(item.text())

        return items

    # Возвращает список событий из ListWidget

    def play(self):
        self.is_playing = True
        events = self.getListFromListWidget()
        for event in events:
            if "pressed" in event:
                press(event.split()[0])
            elif "released" in event:
                release(event.split()[0])
            else:
                sleep(float(event.split()[0]))
        self.is_playing = False

        # воспроизводит открытый макрос

    def load_table(self):
        self.db = Database('ffing.sqlite')

        info = self.db.get_macro_info()
        self.tableWidget.setRowCount(len(info))
        for i in range(len(info)):
            self.tableWidget.setItem(0, i, QTableWidgetItem(info[i][0]))
        self.db.close()

    def open_macro(self):
        self.macro.clear()
        self.db = Database('ffing.sqlite')
        name = self.tableWidget.currentItem().text()
        self.db.current_table(name)
        self.bind_key.setText(self.db.get_bind_key())
        self.current_bind = self.bind_key.text()
        events = self.db.get_events()

        for event in events:
            if event[0] == 'delay':
                self.macro.addItem(event[2] + ' s')
            else:
                self.macro.addItem(event[0] + ' ' + event[1])

        self.openned_macro = name
        self.db.close()
        

    def set_bind(self, event):
        if self.bind_btn_pressed:
            key = self.get_event_info(event)[0].lower()
            self.bind_key.setText(key)
            self.db = Database('ffing.sqlite')
            self.db.current_table(self.openned_macro)
            self.db.set_bind_key(key)
            self.current_bind = key
            self.bind_btn_pressed = False
            self.db.close()
        unhook_all()

    def get_bind(self):
        self.bind_btn_pressed = True
        on_press(self.set_bind)

    def delete_item_from_database(self):
        self.db = Database('ffing.sqlite')
        self.db.current_table(self.openned_macro)
        name = self.tableWidget.currentItem().text()
        self.db.current_table(self.openned_macro)
        valid = QMessageBox.question(
            self, '', f"Действительно удалить элемент с именем '{name}'",
            QMessageBox.Yes, QMessageBox.No)
        if valid == QMessageBox.Yes:
            self.db.delete_item(name)
        self.load_table()
        self.db.close()

    def keyPressEvent(self, event):
        if not self.bind_btn_pressed:
            key = on_press(self.bind_key_check)

    def bind_key_check(self, event):
        if not self.bind_btn_pressed:
            key = self.get_event_info(event)[0].lower()
            if key == self.current_bind and not self.is_playing:
                self.play()

    def get_event_info(self, line):
        try:
            key, key_event = str(line)[14:-1].split()
        except:
            key1, key2, key_event = str(line)[14:-1].split()
            key = f'{key1}_{key2}'
        return key, key_event

    def key_pressed(self):
        on_press(self.bind_key_check)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
