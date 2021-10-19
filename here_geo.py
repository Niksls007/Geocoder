import requests
import json
import random
import zipfile
import io
import os
from bs4 import BeautifulSoup
import csv
from geojson import Feature, FeatureCollection, Point


class Batch:
    def __init__ (self,mainwindow,parent=None):
        super().__init__()
        self.mainwindow = mainwindow
        self.SERVICE_URL = "https://batch.geocoder.ls.hereapi.com/6.2/jobs"
        self.jobId = None
        self.apikey = self.mainwindow.lineEdit.text()
        self.count = len(open(self.mainwindow.inp[0], mode='r', encoding='utf-8-sig').readlines()) - 1

    def name_c(self, key):  # Функция проверки имения поля
        ci = 0
        for index in range(self.mainwindow.listWidget.count()):  # по количеству записей проверяем состояник чекбокса
            if (key == self.mainwindow.listWidget.item(index).text()) and (
                    self.mainwindow.listWidget.item(index).checkState() == 2):
                ci = 1
        return ci

    def file_conversion(self):
        self.count = len(open(self.mainwindow.inp[0],  mode='r', encoding='utf-8-sig').readlines())-1
        self.path_conversion = os.path.dirname(self.mainwindow.out[0]) + '/'+'file_conversion'+''.join([random.choice(list('123456789')) for x in range(3)])+'.csv'
        with open(self.mainwindow.inp[0], mode='r', encoding='utf-8-sig') as r_csvfile:
            with open(self.path_conversion, 'w', newline='',encoding='utf-8-sig') as w_csvfile:
                newFileReader = csv.DictReader(r_csvfile, delimiter = self.mainwindow.comboBox_delimiter.currentText())
                head_name = ['recId', 'searchText']
                writer_csv = csv.DictWriter(w_csvfile, head_name, delimiter = self.mainwindow.comboBox_delimiter.currentText())
                writer_csv.writeheader()
                addresses = {}
                id = 1
                for i, row in enumerate(newFileReader):
                    addresses['recId'] = id
                    id += 1
                    addresses_get = ''
                    for e, key in enumerate(row.keys()):
                        c = self.name_c(key)
                        if (c == False):  # выбор указанных столбцов
                            continue
                        if addresses_get == '':
                            addresses_get = row.get(key)
                        else:
                            addresses_get = addresses_get + ',' + row.get(key)
                    if self.mainwindow.checkBox_city_query.isChecked():
                        addresses_get = self.mainwindow.lineEdit_2.text() + ',' + addresses_get
                    addresses['searchText'] = addresses_get
                    writer_csv.writerow(addresses)
        self.start()

    def start(self):
        indelim = self.mainwindow.comboBox_delimiter.currentText()
        outdelim = self.mainwindow.comboBox_delimiter.currentText()

        file = open(self.path_conversion, 'rb')
        params = {
            "action": "run",
            "apiKey": self.apikey,
            "politicalview":"RUS",
            "gen": 9,
            "maxresults": "1",
            "header": "true",
            "indelim": indelim,
            "outdelim": outdelim,
            "outcols": "displayLatitude,displayLongitude,locationLabel,houseNumber,street,district,city,postalCode,county,state,country",
            "outputcombined": "true",
        }
        if self.mainwindow.checkBox_bbox.isChecked():
            params.update({'mapview': self.mainwindow.lineEdit_x1.text() + ',' +
                                                  self.mainwindow.lineEdit_y2.text() + ';' +
                                                  self.mainwindow.lineEdit_x2.text() + ',' +
                                                  self.mainwindow.lineEdit_y1.text()})
        response = requests.post(self.SERVICE_URL, params=params, data=file)
        if response.status_code == 400:
            text = 'Один или несколько параметров недействительны по ключу или значению.'
            self.mainwindow.error_here_batch(text)
        elif response.status_code == 401:
            self.mainwindow.error_key()
        elif response.status_code == 403:
            text = 'Учетные данные для доступа не позволяют использовать эту конечную точку или ресурс.'
            self.mainwindow.error_here_batch(text)
        elif response.status_code == 404:
            text = 'Запрошенная конечная точка не существует. Это постоянная ошибка.'
            self.mainwindow.error_here_batch(text)
        elif response.status_code == 408:
            text = 'Клиент не завершил отправку полного запроса в установленный срок.'
            self.mainwindow.error_here_batch(text)
        elif response.status_code == 499:
            text = 'Клиент закрыл соединение до того, как служба смогла отправить ответ.'
            self.mainwindow.error_here_batch(text)
        elif response.status_code == 500:
            text = 'Службе не удалось обработать этот запрос из-за непредвиденного состояния программного обеспечения.'
            self.mainwindow.error_here_batch(text)
        elif response.status_code == 502:
            text = 'Плохой шлюз. Сервис временно недоступен.'
            self.mainwindow.error_here_batch(text)
        elif response.status_code == 503:
            text = 'Сервис временно недоступен.'
            self.mainwindow.error_here_batch(text)
        elif response.status_code == 504:
            text = 'Тайм-аут шлюза. Сервис временно недоступен.'
            self.mainwindow.error_here_batch(text)
        else:
            self.__stats(response)
            file.close()
            os.remove(self.path_conversion)


    
    def status (self, jobId):
        self.jobId = jobId
        statusUrl = self.SERVICE_URL + "/" + self.jobId
        params = {
            "action": "status",
            "apiKey": self.apikey,
        }
        response = requests.get(statusUrl, params=params)
        self.__stats(response)


        
    def result (self, jobId = None):
        if jobId is not None:
            self.jobId = jobId
        print("Requesting result data ...")
        resultUrl = self.SERVICE_URL + "/" + self.jobId + "/result"
        params = {
            "apiKey": self.apikey
        }
        response = requests.get(resultUrl, params=params, stream=True)
        if (response.ok):    
            zipResult = zipfile.ZipFile(io.BytesIO(response.content))
            path_zp = os.path.dirname(self.mainwindow.out[0])+'/'
            zipResult.extractall(path_zp)
            path_zp_out = path_zp+zipResult.namelist()[0]
            try:
                os.rename(path_zp_out, self.mainwindow.out[0])
                if self.mainwindow.checkBox.isChecked() or self.mainwindow.checkBox_create_json.isChecked():
                    self.csv_json(self.mainwindow.out[0])
            except WindowsError:
                new_name = ''.join([random.choice(list('123456789')) for x in range(3)])
                path_zp_csv = path_zp+new_name+os.path.basename(self.mainwindow.out[0])
                os.rename(path_zp_out, path_zp_csv)
                if self.mainwindow.checkBox.isChecked() or self.mainwindow.checkBox_create_json.isChecked():
                    self.csv_json(path_zp_csv)
            print("File saved successfully")
            self.mainwindow.success()

        elif response.status_code == 400:
            text = 'Один или несколько параметров недействительны по ключу или значению.'
            self.mainwindow.error_here_batch(text)
        else:
            print("Error")
            self.mainwindow.error_here_batch(response.text)
    def __stats (self, response):
        if (response.ok):
            parsedXMLResponse = BeautifulSoup(response.text, "lxml")
            self.jobId = parsedXMLResponse.find('requestid').get_text()
            if self.mainwindow.batch_start == True:
                self.mainwindow.start_batch(self.jobId)
            else:
                for stat in parsedXMLResponse.find('response').findChildren():
                    if (len(stat.findChildren()) == 0):
                        if (stat.name=='totalcount'):
                            self.q=(int(stat.get_text())/self.count)*100
                            self.mainwindow.progressBar.setValue(round(self.q))
                            if (stat.get_text()==str(self.count)):
                                self.result()
                                break
                            else:
                                if self.mainwindow.batch_check == True:
                                    self.mainwindow.check_status_batch(stat.get_text())
                                    break
                                else:
                                    self.status(self.jobId)
                            continue
                        if stat.name=='status':
                            if stat.get_text() == 'completed':
                                self.result()
                                break
                            elif stat.get_text() == 'failed':
                                self.mainwindow.check_status_batch(stat.get_text())
                                break
        else:
            self.mainwindow.error_here_batch(response.text)

    def name_c(self, key):  # Функция проверки имения поля
        ci = 0
        for index in range(self.mainwindow.listWidget.count()):  # по количеству записей проверяем состояник чекбокса
            if (key == self.mainwindow.listWidget.item(index).text()) and (
                    self.mainwindow.listWidget.item(index).checkState() == 2):
                ci = 1
        return ci

    def csv_json(self,path):
        features = []
        with open(path, newline='',encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter = self.mainwindow.comboBox_delimiter.currentText())
            for row in reader:
                if row['SeqNumber'] == '0' or row['locationLabel'] == '':
                    continue
                b2 = ''
                for e, key in enumerate(row.keys()):
                    c = self.name_c(key)
                    if (c == False):  # выбор указанных столбцов
                        continue
                    loc = str(row.get(key))
                    nk = ''
                    nk = nk + ' ' + loc
                    b2 = b2 + nk
                latitude, longitude = map(float, (row['displayLatitude'], row['displayLongitude']))
                features.append(
                    Feature(
                        geometry = Point((longitude, latitude)),
                        properties = {
                            'name': row['locationLabel']
                        }
                    )
                )


        collection = FeatureCollection(features)
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
