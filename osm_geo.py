import sys  # sys нужен для передачи argv в QApplication
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QSettings, QUrl, QThread
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget, QTableWidgetItem, QAction, QApplication, QMainWindow

import csv
import requests
import json
import re
import os

import json_coverage
from geojson import Feature, FeatureCollection, Point


class Geocoder_osm():
    def __init__(self, mainwindow, parent=None):
        super().__init__()
        self.mainwindow = mainwindow
        self.SERVICE_URL = 'https://nominatim.openstreetmap.org/search?q='
        self.limit = '&format=json&limit='

    def run(self):
        if self.mainwindow.checkBox_city_query.isChecked():
            self.SERVICE_URL = self.SERVICE_URL + self.mainwindow.lineEdit_2.text()
        if self.mainwindow.checkBox_city_on.isChecked() or self.mainwindow.filter_geoj == True:
            self.limit = self.limit + '50'
        else:
            self.limit = self.limit + '1'
        if self.mainwindow.checkBox_bbox.isChecked():
            self.limit = self.limit + '&viewbox=' + (self.mainwindow.lineEdit_x1.text() + ',' +
                                                     self.mainwindow.lineEdit_y1.text() + ',' +
                                                     self.mainwindow.lineEdit_x2.text() + ',' +
                                                     self.mainwindow.lineEdit_y2.text())
        number_line = len(open(self.mainwindow.inp[0], mode='r', encoding='utf-8-sig').readlines())
        self.features = []
        with open(self.mainwindow.inp[0], mode='r', encoding='utf-8-sig') as r_csvfile:
            try:
                with open(self.mainwindow.out[0], 'w', newline='', encoding='utf-8-sig') as w_csvfile:

                    newFileReader = csv.DictReader(r_csvfile, delimiter = self.mainwindow.comboBox_delimiter.currentText())
                    fieldnames = newFileReader.fieldnames + ['x_osm'] + ['y_osm'] + ['Статус запроса']
                    if (self.mainwindow.filter_geoj == True):
                        fieldnames = newFileReader.fieldnames + ['x_osm'] + ['y_osm'] + ['Статус запроса'] + [
                            'Принадлежность к выбранной геометрии (GeoJSON)']
                    writer_csv = csv.DictWriter(w_csvfile, fieldnames, delimiter = self.mainwindow.comboBox_delimiter.currentText())
                    writer_csv.writeheader()
                    i = 0
                    number_line = number_line - 1
                    for row in newFileReader:
                        i = i + 1
                        self.q = (i / number_line) * 100
                        self.mainwindow.progressBar.setValue(round(self.q))
                        address = ''
                        for e, key in enumerate(row.keys()):
                            c = self.field_selection(key)
                            if not c:  # выбор указанных столбцов
                                continue
                            loc = str(row.get(key))
                            part_address = ''
                            part_address = part_address + ' ' + loc
                            address = address + part_address
                        st = self.SERVICE_URL + address + self.limit
                        results = requests.get(st)
                        if results.status_code != 200 or results.text == '[]':
                            row['Статус запроса'] = 'Не найдено'
                            writer_csv.writerow(row)
                            continue
                        row['Статус запроса'] = 'Успешно'
                        b = json.loads(results.text)
                        if self.mainwindow.checkBox_city_on.isChecked() == False and self.mainwindow.filter_geoj == False:
                            row['x_osm'] = b[0].get('lat')
                            row['y_osm'] = b[0].get('lon')
                        if self.mainwindow.checkBox_city_on.isChecked():
                            filter_key = self.filter_name(b)
                            row['x_osm'] = b[filter_key].get('lat')
                            row['y_osm'] = b[filter_key].get('lon')
                        if (self.mainwindow.filter_geoj == True):
                            if self.mainwindow.checkBox_city_on.isChecked():
                                xy = b[filter_key].get('lat') + ' ' + b[filter_key].get('lon')
                                js_coverage = json_coverage.coverage(self.mainwindow.geoj[0])
                                row['Принадлежность к выбранной геометрии (GeoJSON)'] = js_coverage.geojson_utensils(xy)
                            else:
                                filter_key = self.filter_name(b)
                                xy = b[filter_key].get('lat') + ' ' + b[filter_key].get('lon')
                                js_coverage = json_coverage.coverage(self.mainwindow.geoj[0])
                                row['x_osm'] = b[filter_key].get('lat')
                                row['y_osm'] = b[filter_key].get('lon')
                                row['Принадлежность к выбранной геометрии (GeoJSON)'] = js_coverage.geojson_utensils(xy)
                        writer_csv.writerow(row)
                        if self.mainwindow.checkBox.isChecked() or self.mainwindow.checkBox_create_json.isChecked():
                            latitude, longitude = map(float, (row['x_osm'], row['y_osm']))
                            self.features.append(
                                Feature(geometry=Point((longitude, latitude)), properties={'name': address}))
                    if self.mainwindow.checkBox.isChecked() or self.mainwindow.checkBox_create_json.isChecked():
                        self.csv_json()
                    self.features = []
                    self.mainwindow.success()
            except PermissionError:  # проверка на ошибку открытого файла
                self.mainwindow.error()
            except KeyError:
                self.mainwindow.error_key()
            except requests.exceptions.ConnectionError:
                self.mainwindow.errorConnection()

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


    def filter_name(self, results):
        b = results
        filter_result = {}  # словарь, где хранится количество совпадений
        one_result = True
        for i in range(len(b)):
            result = [x.strip() for x in b[i].get('display_name').split(',')]
            coincidence = 0  # количество совпадений
            if (i == 0):
                filter_result.update({i: 0})
            if self.mainwindow.checkBox_city_on.isChecked():
                for j in range(len(result)):
                    filter_st = re.search(self.mainwindow.lineEdit_2.text().lower(), result[j].lower())
                    if (i == 0) and (j == 0):
                        filter_result.update({i: j})
                    if filter_st != None:
                        coincidence = coincidence + 1
            if self.mainwindow.filter_geoj == True:
                xy = b[i].get('lat') + ' ' + b[i].get('lon')
                js_coverage = json_coverage.coverage(self.mainwindow.geoj[0])
                geo_filter = js_coverage.geojson_utensils(xy)
                if geo_filter == True:
                    coincidence = coincidence + 2
                    if one_result == True:
                        coincidence = coincidence + 1
                        one_result = False
            if coincidence > 0:
                filter_result.update({i: coincidence})
        filter_key = max(filter_result, key=filter_result.get)
        filter_result.clear()
        return filter_key
