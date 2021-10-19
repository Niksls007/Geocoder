import json
from geojson import Feature, FeatureCollection, Polygon


class Bbox():
    def __init__ (self,mainwindow,parent=None):
        super().__init__()
        self.mainwindow = mainwindow


    def create_bbox(self):
        bbox = [ [0]*2 for i in range(4)]
        features = []
        bbox[0][0], bbox[0][1] = float(self.mainwindow.lineEdit_x1.text()),  float(self.mainwindow.lineEdit_y1.text())
        bbox[1][0], bbox[1][1] = float(self.mainwindow.lineEdit_x2.text()), float(self.mainwindow.lineEdit_y1.text())
        bbox[2][0], bbox[2][1] = float(self.mainwindow.lineEdit_x2.text()), float(self.mainwindow.lineEdit_y2.text())
        bbox[3][0], bbox[3][1] = float(self.mainwindow.lineEdit_x1.text()), float(self.mainwindow.lineEdit_y2.text())
        features.append(
            Feature(
                geometry = Polygon([bbox]),
                properties = {
                    'name': 'Охват'
                }
            )
        )

        collection = FeatureCollection(features)
        with open("map/web/bbox.json", "w",encoding='utf-8-sig') as f:
            json.dump(collection,f,ensure_ascii=False)
        f = open('map/web/bbox.json','r+',encoding='utf-8-sig')
        lines = f.readlines()
        f.seek(0) # go back to the beginning of the file
        f.write('var bbox_map =')
        for line in lines: # write old content after new
            f.write(line)
        f.close()