import sys  # sys нужен для передачи argv в QApplication
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QSettings, QUrl, QThread
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget, QTableWidgetItem, QAction, QApplication, QMainWindow

import csv
import requests
import json

import json_coverage
from geojson import Feature, FeatureCollection, Point
import os

class Geocoder_ya():
    def __init__ (self,mainwindow,parent=None):
        super().__init__()
        self.mainwindow = mainwindow
        self.SERVICE_URL='https://geocode-maps.yandex.ru/1.x/?lang=ru_RU&apikey='
        self.limit = ''
        self.bbox = ''


    def run(self):
        yan = self.SERVICE_URL + self.mainwindow.lineEdit.text()
        if self.mainwindow.checkBox_city_on.isChecked() or self.mainwindow.filter_geoj == True:
            self.limit = '&results=100'
        yan = yan + self.limit + '&format=json&geocode='
        if self.mainwindow.checkBox_city_query.isChecked():
            yan = yan + self.mainwindow.lineEdit_2.text()
        if self.mainwindow.checkBox_bbox.isChecked():
            self.bbox = '&bbox=' + (self.mainwindow.lineEdit_x1.text() + ',' +
                                    self.mainwindow.lineEdit_y1.text() + '~' +
                                    self.mainwindow.lineEdit_x2.text() + ',' +
                                    self.mainwindow.lineEdit_y2.text() + '&rspn=1'
            )
        self.features = [] # массив для хранения атрибутов json
        number_line = len(open(self.mainwindow.inp[0],  mode = 'r', encoding = 'utf-8-sig').readlines())
        with open(self.mainwindow.inp[0], mode = 'r', encoding = 'utf-8-sig') as r_csvfile:
            try:        
                with open(self.mainwindow.out[0],'w',newline = '', encoding = 'utf-8-sig') as w_csvfile:
            
                    newFileReader = csv.DictReader(r_csvfile, delimiter = self.mainwindow.comboBox_delimiter.currentText())
                    fieldnames = newFileReader.fieldnames + ['x_yandex'] + ['y_yandex'] + ['точность'] + ['Статус запроса']
                    if (self.mainwindow.filter_geoj==True):
                        fieldnames = newFileReader.fieldnames + ['x_yandex'] + ['y_yandex'] + ['точность'] + ['Статус запроса'] + ['Принадлежность к выбранной геометрии (GeoJSON)']
                    writer_csv = csv.DictWriter(w_csvfile,fieldnames,delimiter = self.mainwindow.comboBox_delimiter.currentText())
                    writer_csv.writeheader()
                    i = 0
                    number_line = number_line - 1
                    for row in newFileReader:
                        i = i + 1
                        self.q = (i/number_line) * 100
                        self.mainwindow.progressBar.setValue(round(self.q))
                        address = ''
                        for e, key in enumerate(row.keys()):
                            c = self.field_selection(key)
                            if not c: #выбор указанных столбцов
                                continue
                            loc=str(row.get(key))
                            nk = ''
                            nk = nk+' '+loc
                            address = address+nk
                        st = yan + address + self.bbox
                        results = requests.get(st)
                        self.result = results.json()
                        if results.status_code == 403: #проверка на apiKey invalid
                            pass
                        elif results.status_code != 200 or self.result['response']['GeoObjectCollection']['featureMember'] == []:
                            row['Статус запроса'] = 'Не найдено'
                            writer_csv.writerow(row)
                            continue
                        row['Статус запроса'] = 'Успешно'
                        if self.mainwindow.checkBox_city_on.isChecked() == False and self.mainwindow.filter_geoj == False:
                            yx = self.result['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'].split()
                            yx[0], yx[-1] = yx[-1], yx[0]
                            row['x_yandex'] = yx[0]
                            row['y_yandex'] = yx[-1]
                            row['точность'] = self.result['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['precision']
                        if self.mainwindow.checkBox_city_on.isChecked():
                            filter_key = self.filter()
                            if self.mainwindow.filter_geoj == False:
                                yx = self.result['response']['GeoObjectCollection']['featureMember'][filter_key]['GeoObject']['Point']['pos'].split()
                                yx[0], yx[-1] = yx[-1], yx[0]
                                row['x_yandex'] = yx[0]
                                row['y_yandex'] = yx[-1]
                                row['точность'] = self.result['response']['GeoObjectCollection']['featureMember'][filter_key]['GeoObject']['metaDataProperty']['GeocoderMetaData']['precision']
                        if self.mainwindow.filter_geoj == True:
                            if self.mainwindow.checkBox_city_on.isChecked():
                                yx = self.result['response']['GeoObjectCollection']['featureMember'][filter_key]['GeoObject']['Point']['pos'].split()
                                yx[0], yx[-1] = yx[-1], yx[0]
                                row['x_yandex'] = yx[0]
                                row['y_yandex'] = yx[-1]
                                xy = ' '.join(yx)
                                js_coverage = json_coverage.coverage(self.mainwindow.geoj[0])
                                row['Принадлежность к выбранной геометрии (GeoJSON)'] = js_coverage.geojson_utensils(xy)
                                row['точность'] = self.result['response']['GeoObjectCollection']['featureMember'][filter_key]['GeoObject']['metaDataProperty']['GeocoderMetaData']['precision']
                            else:
                                filter_key = self.filter()
                                yx = self.result['response']['GeoObjectCollection']['featureMember'][filter_key]['GeoObject']['Point']['pos'].split()
                                yx[0], yx[-1] = yx[-1], yx[0]
                                xy = ' '.join(yx)
                                js_coverage = json_coverage.coverage(self.mainwindow.geoj[0])
                                row['Принадлежность к выбранной геометрии (GeoJSON)'] = js_coverage.geojson_utensils(xy)
                                row['x_yandex'] = yx[0]
                                row['y_yandex'] = yx[-1]
                                row['точность'] = self.result['response']['GeoObjectCollection']['featureMember'][filter_key]['GeoObject']['metaDataProperty']['GeocoderMetaData']['precision']
                        if self.mainwindow.checkBox.isChecked() or self.mainwindow.checkBox_create_json.isChecked():
                            latitude, longitude = map(float, (row['x_yandex'], row['y_yandex']))
                            self.features.append(Feature(geometry=Point((longitude, latitude)),properties={'name': address}))
                        writer_csv.writerow(row)
                    if self.mainwindow.checkBox.isChecked() or self.mainwindow.checkBox_create_json.isChecked():
                        self.csv_json()
                    self.mainwindow.success()
            except PermissionError:  #проверка на ошибку открытого файла
                self.mainwindow.error()
            except KeyError:
                self.mainwindow.error_key()

    def field_selection(self, key):  # Функция проверки имения поля
        field_check = 0
        for index in range(self.mainwindow.listWidget.count()):  # по количеству записей проверяем состояник чекбокса
            if (key == self.mainwindow.listWidget.item(index).text()) and (
                    self.mainwindow.listWidget.item(index).checkState() == 2):
                field_check = 1
        return field_check

    def csv_json(self):
        collection = FeatureCollection(self.features)
        if self.mainwindow.checkBox.isChecked():
            with open("map/web/GeoObs.json", "w", encoding='utf-8-sig') as f:
                json.dump(collection, f, ensure_ascii=False)
            f = open('map/web/GeoObs.json', 'r+', encoding='utf-8-sig')
            lines = f.readlines()
            f.seek(0)  # go back to the beginning of the file
            f.write('var adm =')
            for line in lines:  # write old content after new
                f.write(line)
            f.close()
        if self.mainwindow.checkBox_create_json.isChecked():
            path_geojs = os.path.splitext(self.mainwindow.out[0])[0] + '.geojson'
            with open(path_geojs, "w", encoding='utf-8-sig') as f_j:
                json.dump(collection, f_j, ensure_ascii=False)

    def filter(self):
        store = self.result['response']['GeoObjectCollection']['featureMember']
        filter_result = {}  # словарь, где хранится количество совпадений
        one_result_city = True
        one_result_geojson = True
        for i in range(len(store)):
            coincidence = 0
            if i == 0:
                filter_result.update({i: 0})
            geomess = store[i]['GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']['Components']
            if self.mainwindow.checkBox_city_on.isChecked():
                for j in range(len(geomess)):
                    if geomess[j].get('kind') == 'locality':
                        if geomess[j].get('name').lower() == self.mainwindow.lineEdit_2.text().lower():
                            coincidence = coincidence + 1
                            if one_result_city == True:
                                coincidence += 1
                                one_result_city = False
            if self.mainwindow.filter_geoj == True:
                yx = store[i]['GeoObject']['Point']['pos'].split()
                yx[0], yx[-1] = yx[-1], yx[0]
                xy = ' '.join(yx)
                js_coverage = json_coverage.coverage(self.mainwindow.geoj[0])
                geo_filter = js_coverage.geojson_utensils(xy)
                if geo_filter == True:
                    coincidence += 2
                    if one_result_geojson == True:
                        coincidence += 1
                        one_result_geojson = False
                if coincidence > 0:
                    filter_result.update({i: coincidence})
        filter_key = max(filter_result, key=filter_result.get)
        filter_result.clear()
        return filter_key