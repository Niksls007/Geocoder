import sys  # sys нужен для передачи argv в QApplication
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QUrl


from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget, QTableWidgetItem, QAction, QApplication, QMainWindow


import menu_design
import bbox_on_map
import style_message
import re
import os
import time
import yandex_geo
import osm_geo
import here_geo
import here_get

import csv


from PyQt5.QtGui import QIcon

from PyQt5.QtWebEngineWidgets import *





class ExampleApp(QtWidgets.QMainWindow, menu_design.Ui_MainWindow):


    
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.filter_geoj=False
        self.setWindowIcon(QIcon("./img/icon.png"))
        self.select_csv.clicked.connect(self.Select)
        self.fil_json.clicked.connect(self.Select_geojson)
        self.inp=[]
        self.out=[]
        self.Button_start.clicked.connect(self.start)
        self.Button_select.clicked.connect(self.select_all)
        self.Button_delete.clicked.connect(self.delete_all)
        self.Button_bbox_on.clicked.connect(self.bbox)
        self.Button_check_id.clicked.connect(self.check_batch)
        self.Button_check_id_auto.clicked.connect(self.start_auto_batch)
        self.geoj = None
        self.batch_check = False   # для проверки статуса пакетного запроса
        self.batch_start = False   # для проверки запуска пакетного запроса
        self.batch_auto = False    # для запуска автоматической проверки пакетного запроса
        self.type_num_col = style_message.type_num_col
        self.url="file:/map/web/map.html"
        self.webView.load(QUrl(self.url))
        self.delimiter_check = ''
        self.loading.setVisible(False)



    def check_bbox(self):
        try:
            if (re.match(r"[,0-9 -.]*$", self.lineEdit_x1.text())
            and re.match(r"[,0-9 -.]*$", self.lineEdit_y1.text())
            and re.match(r"[,0-9 -.]*$", self.lineEdit_x2.text())
            and re.match(r"[,0-9 -.]*$", self.lineEdit_y2.text())):
                if (-180 <= float(self.lineEdit_x1.text()) <= 180
                and -180 <= float(self.lineEdit_x2.text()) <= 180
                and -90 <= float(self.lineEdit_y1.text()) <= 90
                and -90 <= float(self.lineEdit_y2.text()) <= 90
                ):
                    return True
                else:
                    return False
            else:
                return False
        except ValueError:
            return False

    def bbox(self):
        if self.check_bbox() == True and self.comboBox.currentIndex() == 1:
            self.box = bbox_on_map.Bbox(mainwindow=self)
            self.box.create_bbox()
            self.url = "file:/map/web/yandex-bbox.html"
            self.webView.setUrl(QUrl(self.url))
            self.success_bbox()
        elif self.check_bbox() == True and self.comboBox.currentIndex() != 1:
            self.box = bbox_on_map.Bbox(mainwindow=self)
            self.box.create_bbox()
            self.url = "file:/map/web/map-bbox.html"
            self.webView.setUrl(QUrl(self.url))
            self.success_bbox()
        else:
            self.error_data_bbox()



    def select_all(self):
        for index in range(self.listWidget.count()):
            self.listWidget.item(index).setCheckState(QtCore.Qt.Checked)


    def delete_all(self):
        for index in range(self.listWidget.count()):
            self.listWidget.item(index).setCheckState(QtCore.Qt.Unchecked)

    def Select_geojson(self):
        self.geoj = QFileDialog.getOpenFileName(self, 'Select file',"", '*.geojson')
        if self.geoj[0] != '':
            self.checkBox_filter_geojson.setChecked(True)

    def updata_tab(self):
        self.tableWidget.setVisible(True)

    def Select(self):
        name_col = []
        self.inp = QFileDialog.getOpenFileName(self, 'Select file',"", '*.csv')
        self.delimiter_check = self.comboBox_delimiter.currentText()
        try:
            stolb=len(open(self.inp[0],  mode='r', encoding='utf-8-sig').readlines()) # считываем данные для предпросмотра таблицы
            with open(self.inp[0],  mode='r', encoding='utf-8-sig') as fileInput:
                newFileReader = csv.DictReader(fileInput, delimiter = self.comboBox_delimiter.currentText())
                stolb = stolb - 1
                self.tableWidget.setRowCount(stolb)
                data = []
                for u,row_data in enumerate(newFileReader):
                    self.tableWidget.setColumnCount(1)
                    if len(row_data) > 1:
                            self.tableWidget.setColumnCount(len(row_data))
                    dat_1 = []
                    name_col = []
                    for column, stuff in enumerate(row_data.keys()):
                        dat_1.append(row_data.get(stuff))
                        name_col.append(stuff)
                    data.append(dat_1)
                    self.tableWidget.setHorizontalHeaderLabels(name_col)
            row = 0
            for dat in data:
                for col, z in enumerate(dat):
                    item = QTableWidgetItem(z)
                    self.tableWidget.setItem(row, col, item)
                row = 1 + row

            self.listWidget.clear()# обновление столбца
            self.das = name_col
            
            for i in name_col:  #добавление названий столбцов для выбора нужных
                item = QtWidgets.QListWidgetItem()
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Checked)
                self.listWidget.addItem(item)
                item.setText(i)

            self.tableWidget.setVisible(True)
            self.label_2.setVisible(True)
            self.select_output_file()
            
        except FileNotFoundError:
            msg = QMessageBox()
            msg.setWindowTitle("Внимание!")
            msg.setWindowIcon(QIcon("./img/icon.png"))
            msg.setText("Выберите файл")
            msg.setStyleSheet(self.type_num_col)
            result = msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            if retval == QMessageBox.Ok:
                self.show()


    def select_output_file(self):
        
        self.out = QFileDialog.getSaveFileName(self, "Select output file ","", '*.csv')
        if (self.inp==self.out):
            msg = QMessageBox()
            msg.setWindowTitle("Внимание!")
            msg.setText("Нельзя перезаписать тот же файл")
            msg.setText("Выберете другое имя файлу")
            msg.setStyleSheet(self.type_num_col)
            result = msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            if retval == QMessageBox.Ok:
                self.select_output_file()

    def start(self):
        msg = QMessageBox()
        self.loading.setVisible(True)
        msg.setWindowTitle("Внимание!")
        msg.setWindowIcon(QIcon("./img/icon.png"))
        msg.setText("Вы уверены, что хотите начать\nпроцесс геокодирования?")
        msg.setStyleSheet(self.type_num_col)
        result = msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        retval = msg.exec_()
        if retval == QMessageBox.Ok:
            self.check_data()
            self.show()
        else:
            self.loading.setVisible(False)

    def start_auto_batch(self):
        msg = QMessageBox()
        self.loading.setVisible(True)
        msg.setWindowTitle("Внимание!")
        msg.setWindowIcon(QIcon("./img/icon.png"))
        msg.setText("Вы уверены, что хотите начать\nавтоматическую проверку статуса запроса?")
        msg.setStyleSheet(self.type_num_col)
        result = msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        retval = msg.exec_()
        if retval == QMessageBox.Ok:
            self.auto_batch()
            self.show()
        else:
            self.loading.setVisible(False)

    def check_data(self):
        try:
            if (self.inp[0] == ''):
                msg = QMessageBox()
                msg.setWindowTitle("Внимание!")
                msg.setWindowIcon(QIcon("./img/icon.png"))
                msg.setText("Выберите файл")
                msg.setStyleSheet(self.type_num_col)
                result = msg.setStandardButtons(QMessageBox.Ok)
                retval = msg.exec_()
                if retval == QMessageBox.Ok:
                    self.loading.setVisible(False)
                    self.show()
            elif (self.out[0] == ''):
                msg = QMessageBox()
                msg.setWindowTitle("Внимание!")
                msg.setWindowIcon(QIcon("./img/icon.png"))
                msg.setText("Укажите путь для сохранения")
                msg.setStyleSheet(self.type_num_col)
                result = msg.setStandardButtons(QMessageBox.Ok)
                retval = msg.exec_()
                if retval == QMessageBox.Ok:
                    self.loading.setVisible(False)
                    self.show()
            elif (self.lineEdit.text() == '' and self.comboBox.currentIndex()!=0): #проверка надобности ключ
                msg = QMessageBox()
                msg.setWindowTitle("Внимание!")
                msg.setWindowIcon(QIcon("./img/icon.png"))
                msg.setText("Укажите ключ API")
                msg.setStyleSheet(self.type_num_col)
                result = msg.setStandardButtons(QMessageBox.Ok)
                retval = msg.exec_()
                if retval == QMessageBox.Ok:
                    self.loading.setVisible(False)
                    self.show()
            elif self.geoj == None and self.checkBox_filter_geojson.isChecked():
                msg = QMessageBox()
                msg.setWindowTitle("Внимание!")
                msg.setWindowIcon(QIcon("./img/icon.png"))
                msg.setText("Выберите GeoJSON")
                msg.setStyleSheet(self.type_num_col)
                result = msg.setStandardButtons(QMessageBox.Ok)
                retval = msg.exec_()
                if retval == QMessageBox.Ok:
                    self.loading.setVisible(False)
                    self.show()
            elif self.check_bbox() != True and self.checkBox_bbox.isChecked():
                self.error_data_bbox()
            elif self.lineEdit_2.text() == '' and self.checkBox_city_query.isChecked():
                self.error_city_query()
            elif self.delimiter_check != self.comboBox_delimiter.currentText():
                self.error_delimiter()
            else:
                self.run()   
        except  IndexError:
            msg = QMessageBox()
            msg.setWindowTitle("Внимание!")
            msg.setWindowIcon(QIcon("./img/icon.png"))
            msg.setText("Выберите файл")
            msg.setStyleSheet(self.type_num_col)
            result = msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()
            if retval == QMessageBox.Ok:
                self.loading.setVisible(False)
                self.show()
    def run(self):
        self.start_time = time.time()
        if self.checkBox_filter_geojson.isChecked():
            self.filter_geoj = True
        if self.comboBox.currentIndex() == 0:
            self.osm = osm_geo.Geocoder_osm(mainwindow = self)
            self.osm.run()
        elif self.comboBox.currentIndex() == 1:
            self.cl=yandex_geo.Geocoder_ya(mainwindow = self)
            self.cl.run()
        elif self.comboBox.currentIndex() == 2:
            self.here = here_get.Geocoder_here(mainwindow = self)
            self.here.run()
        elif self.comboBox.currentIndex() == 3:
            self.batch_start = True
            service = here_geo.Batch(mainwindow = self)
            service.file_conversion()

    def start_batch(self, id):
        id = id
        msg = QMessageBox()
        msg.setWindowTitle("Проверка статуса")
        msg.setText('Запрос отправлен на сервер. Вам предоставлен идентификатор пакетного запроса. '
                    'С помощью него Вы сможете проверить статус работы.')
        msg.setStyleSheet(self.type_num_col)
        msg.setWindowIcon(QIcon("./img/icon.png"))
        result = msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        self.lineEdit_id.setText(id)
        self.progressBar.setValue(0)
        self.batch_start = False
        self.loading.setVisible(False)
        self.show()


    def check_batch(self):
        self.batch_check = True
        if self.inp == []:
            self.error_here_batch('Выберете файл, который ранее был отправлен через пакетный запрос.')
        elif self.out == []:
            self.error_here_batch('Укажите путь для сохранения выходного файла.')
        elif self.delimiter_check != self.comboBox_delimiter.currentText():
            self.error_delimiter()
        else:
            service = here_geo.Batch(mainwindow=self)
            service.status(self.lineEdit_id.text())

    def auto_batch(self):
        self.batch_auto = True
        if self.inp == []:
            self.error_here_batch('Выберете файл, который ранее был отправлен через пакетный запрос.')
        elif self.out == []:
            self.error_here_batch('Укажите путь для сохранения выходного файла.')
        elif self.delimiter_check != self.comboBox_delimiter.currentText():
            self.error_delimiter()
        else:
            service = here_geo.Batch(mainwindow=self)
            service.status(self.lineEdit_id.text())



    def check_status_batch(self, done):
        done = done
        if done == 'failed':
            massage = 'Неверный идентификатор пакетного запроса.'
        else:
            massage = 'Обработано ' + done + ' адресов'
        msg = QMessageBox()
        msg.setWindowTitle("Проверка статуса")
        msg.setText(massage)
        msg.setStyleSheet(self.type_num_col)
        msg.setWindowIcon(QIcon("./img/icon.png"))
        result = msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        self.batch_check = False
        self.progressBar.setValue(0)
        self.loading.setVisible(False)
        self.show()

    def success(self):
        msg = QMessageBox()
        msg.setWindowIcon(QIcon("./img/icon.png"))
        msg.setWindowTitle("Успешно!")
        str(time.time() - self.start_time)
        time_end = '%.3f'%(time.time() - self.start_time)
        msg.setText("Процесс успешно завершен.\nВремя выполнения — " + time_end + ' секунды')
        msg.setStyleSheet(self.type_num_col)
        result = msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        self.loading.setVisible(False)
        if self.checkBox.isChecked() and self.comboBox.currentIndex() != 1:
            if self.checkBox_bbox.isChecked():
                self.box = bbox_on_map.Bbox(mainwindow=self)
                self.box.create_bbox()
                self.url = "file:/map/web/map-json_bbox.html"
                self.webView.setUrl(QUrl(self.url))
            else:
                self.url = "file:/map/web/map-json.html"
                self.webView.setUrl(QUrl(self.url))
        elif self.checkBox.isChecked() and self.comboBox.currentIndex() == 1:
            if self.checkBox_bbox.isChecked():
                self.box = bbox_on_map.Bbox(mainwindow=self)
                self.box.create_bbox()
                self.url = "file:/map/web/map_yandex_bbox.html"
                self.webView.setUrl(QUrl(self.url))
            else:
                self.url = "file:/map/web/map_yandex_json.html"
                self.webView.setUrl(QUrl(self.url))

        self.filter_geoj = False
        self.progressBar.setValue(0)

    def error_delimiter(self):
        msg = QMessageBox()
        msg.setWindowTitle("Внимание!")
        msg.setWindowIcon(QIcon("./img/icon.png"))
        msg.setText("Вы поменяли символ разделителя")
        msg.setStyleSheet(self.type_num_col)
        result = msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        if retval == QMessageBox.Ok:
            self.loading.setVisible(False)
            self.show()

    def error_key(self):
        msg = QMessageBox()
        msg.setWindowTitle("Ошибка!")
        msg.setText("Указан неверный ключ API")
        msg.setStyleSheet(self.type_num_col)
        msg.setWindowIcon(QIcon("./img/icon.png"))
        result = msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        self.progressBar.setValue(0)
        self.loading.setVisible(False)
        self.show()

    def error(self):
        msg = QMessageBox()
        msg.setWindowTitle("Ошибка!")
        msg.setText("Закройте CSV-файл")
        msg.setWindowIcon(QIcon("./img/icon.png"))
        msg.setStyleSheet(self.type_num_col)
        result = msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        self.progressBar.setValue(0)
        self.loading.setVisible(False)
    def errorConnection(self):
        msg = QMessageBox()
        msg.setWindowTitle("Ошибка!")
        msg.setText("Отсутствует доступ к сети")
        msg.setWindowIcon(QIcon("./img/icon.png"))
        msg.setStyleSheet(self.type_num_col)
        result = msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        self.progressBar.setValue(0)
        self.loading.setVisible(False)
        self.show()

    def error_data_bbox(self):
        msg = QMessageBox()
        msg.setWindowTitle("Ошибка!")
        msg.setWindowIcon(QIcon("./img/icon.png"))
        msg.setText("Введены некорректные данные")
        msg.setStyleSheet(self.type_num_col)
        result = msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        self.loading.setVisible(False)
        if retval == QMessageBox.Ok:
            self.show()

    def success_bbox(self):
        msg = QMessageBox()
        msg.setWindowTitle("Успешно!")
        msg.setWindowIcon(QIcon("./img/icon.png"))
        msg.setText("Охват выбран")
        msg.setStyleSheet(self.type_num_col)
        result = msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        if retval == QMessageBox.Ok:
            self.show()

    def error_here_batch(self, text):
        message = text
        if message == '':
            message = 'Укажите идентификатор пакетного запроса'
        msg = QMessageBox()
        msg.setWindowTitle("Ошибка!")
        msg.setWindowIcon(QIcon("./img/icon.png"))
        msg.setText(message)
        msg.setStyleSheet(self.type_num_col)
        result = msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        self.loading.setVisible(False)
        if retval == QMessageBox.Ok:
            self.show()

    def error_city_query(self):
        msg = QMessageBox()
        msg.setWindowTitle("Ошибка!")
        msg.setWindowIcon(QIcon("./img/icon.png"))
        msg.setText('Введите название города для добавление его в запрос.')
        msg.setStyleSheet(self.type_num_col)
        result = msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()
        self.loading.setVisible(False)
        if retval == QMessageBox.Ok:
            self.show()



def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = ExampleApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()