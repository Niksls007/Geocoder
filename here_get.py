import sys  # sys нужен для передачи argv в QApplication
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QSettings, QUrl, QThread
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget, QTableWidgetItem, QAction, QApplication, QMainWindow

import csv
import requests
import json
import main
import json_coverage
from geojson import Feature, FeatureCollection, Point
import os


class Geocoder_here():
    def __init__ (self,mainwindow,parent=None):
        super().__init__()
        self.mainwindow = mainwindow
        self.SERVICE_URL = 'https://geocoder.ls.hereapi.com/6.2/geocode.json?apiKey='
        self.seacrhtext = '&searchtext='
        self.limit = '&maxresults=1'

    def run(self):
        self.features = []
        if self.mainwindow.checkBox_city_query.isChecked():
            self.seacrhtext = self.seacrhtext + self.mainwindow.lineEdit_2.text()
        if self.mainwindow.checkBox_city_on.isChecked() or self.mainwindow.filter_geoj == True:
            self.limit = self.limit + '00'
        if self.mainwindow.checkBox_bbox.isChecked():
            self.limit = self.limit + '&mapview=' + (self.mainwindow.lineEdit_x1.text() + ',' +
                                                  self.mainwindow.lineEdit_y2.text() + ';' +
                                                  self.mainwindow.lineEdit_x2.text() + ',' +
                                                  self.mainwindow.lineEdit_y1.text()
            )
        number_line = len(open(self.mainwindow.inp[0], mode = 'r', encoding = 'utf-8-sig').readlines())
        with open(self.mainwindow.inp[0], mode = 'r', encoding = 'utf-8-sig') as r_csvfile:
            try:
                with open(self.mainwindow.out[0], 'w', newline = '', encoding = 'utf-8-sig') as w_csvfile:
                    newFileReader = csv.DictReader(r_csvfile, delimiter = self.mainwindow.comboBox_delimiter.currentText())
                    fieldnames = newFileReader.fieldnames + ['x_here'] + ['y_here'] + ['Статус запроса']
                    if (self.mainwindow.filter_geoj == True):
                        fieldnames = newFileReader.fieldnames + ['x_here'] + ['y_here'] + ['Статус запроса'] + ['Принадлежность к выбранной геометрии (GeoJSON)']
                    writer_csv = csv.DictWriter(w_csvfile, fieldnames, delimiter = self.mainwindow.comboBox_delimiter.currentText())
                    writer_csv.writeheader()
                    i = 0
                    number_line = number_line - 1
                    for row in newFileReader:
                        i = i + 1
                        self.q = (i / number_line) * 100
                        self.mainwindow.progressBar.setValue(round(self.q))
                        b2 = ''
                        for e,key in enumerate(row.keys()):
                            c=self.field_selection(key)
                            if not c: #выбор указанных столбцов
                                continue
                            loc = str(row.get(key))
                            b2 = b2+' '+loc
                        st = self.SERVICE_URL + self.mainwindow.lineEdit.text() + self.seacrhtext + b2 + self.limit
                        results = requests.get(st)
                        result_get = results.json()
                        if results.status_code == 401: #не дать пройти apiKey invalid
                            pass
                        elif results.status_code != 200 or result_get['Response']['View'] == []:
                            row['Статус запроса']='Не найдено'
                            writer_csv.writerow(row)
                            continue
                        row['Статус запроса']='Успешно'
                        if self.mainwindow.checkBox_city_on.isChecked() == False and self.mainwindow.filter_geoj == False:
                            row['x_here'] = result_get['Response']['View'][0]['Result'][0]['Location']['DisplayPosition'].get('Latitude')
                            row['y_here'] = result_get['Response']['View'][0]['Result'][0]['Location']['DisplayPosition'].get('Longitude')
                        if self.mainwindow.checkBox_city_on.isChecked():
                            filter_key = self.filter(result_get)
                            row['x_here'] = result_get['Response']['View'][0]['Result'][filter_key]['Location']['DisplayPosition'].get('Latitude')
                            row['y_here'] = result_get['Response']['View'][0]['Result'][filter_key]['Location']['DisplayPosition'].get('Longitude')
                        if (self.mainwindow.filter_geoj == True):
                            if self.mainwindow.checkBox_city_on.isChecked():
                                xy = str(result_get['Response']['View'][0]['Result'][filter_key]['Location']['DisplayPosition'].get('Latitude')) + ' ' + str(result_get['Response']['View'][0]['Result'][filter_key]['Location']['DisplayPosition'].get('Longitude'))
                                js_coverage = json_coverage.coverage(self.mainwindow.geoj[0])
                                row['Принадлежность к выбранной геометрии (GeoJSON)'] = js_coverage.geojson_utensils(xy)
                            else:
                                filter_key = self.filter(result_get)
                                xy = str(result_get['Response']['View'][0]['Result'][filter_key]['Location']['DisplayPosition'].get('Latitude')) + ' ' + str(result_get['Response']['View'][0]['Result'][filter_key]['Location']['DisplayPosition'].get('Longitude'))
                                js_coverage = json_coverage.coverage(self.mainwindow.geoj[0])
                                row['x_here'] = result_get['Response']['View'][0]['Result'][0]['Location']['DisplayPosition'].get('Latitude')
                                row['y_here'] = result_get['Response']['View'][0]['Result'][0]['Location']['DisplayPosition'].get('Longitude')
                                row['Принадлежность к выбранной геометрии (GeoJSON)'] = js_coverage.geojson_utensils(xy)
                        writer_csv.writerow(row)
                        if self.mainwindow.checkBox.isChecked() or self.mainwindow.checkBox_create_json.isChecked():
                            latitude, longitude = map(float, (row['x_here'], row['y_here']))
                            self.features.append(
                                Feature(geometry=Point((longitude, latitude)), properties={'name': b2}))
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
            if (key == self.mainwindow.listWidget.item(index).text()) and (self.mainwindow.listWidget.item(index).checkState() == 2):
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

    def filter(self, results):
        geojson_filter = self.mainwindow.filter_geoj
        city = results
        filter_result = {}
        one_result_city = True
        one_result_geojson = True
        for i in range(len(city)):
            coincidence = 0
            if i == 0:
                filter_result.update({i: 0})
            if self.mainwindow.checkBox_city_on.isChecked() and city['Response']['View'][0]['Result'][i]['Location']['Address']['City'].lower() == self.mainwindow.lineEdit_2.text().lower():
                coincidence = coincidence + 1
                if one_result_city == True:
                    coincidence = coincidence + 1
                    one_result_city = False
            if geojson_filter == True:
                xy = str(city['Response']['View'][0]['Result'][i]['Location']['DisplayPosition'].get('Latitude')) + ' ' + str(city['Response']['View'][0]['Result'][i]['Location']['DisplayPosition'].get('Longitude'))
                js_coverage = json_coverage.coverage(self.mainwindow.geoj[0])
                geo_filter = js_coverage.geojson_utensils(xy)
                if geo_filter == True:
                    coincidence = coincidence + 2
                    if one_result_geojson == True:
                        coincidence = coincidence + 1
                        one_result_geojson = False
            if coincidence > 0:
                filter_result.update({i: coincidence})
        filter_key = max(filter_result, key=filter_result.get)
        filter_result.clear()
        return filter_key



