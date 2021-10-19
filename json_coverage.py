import sys
from shapely.geometry import Point, Polygon #для геометрии
import json #для геометрии
class coverage():
    def __init__(self, path):
        self.path = path

    def geojson_utensils(self,xy):
        xy = xy.split() #координаты
        F = Point(float(xy[0]), float(xy[-1]))
        poi = False
        with open(self.path, encoding='utf-8-sig') as js:
            data = json.load(js)      
        for feature in data['features']:
            s = feature['geometry']['coordinates']
            if (feature['geometry']['type'] == "Point") or (feature['geometry']['type'] == "LineString") or (feature['geometry']['type'] == "MultiPoint") or (feature['geometry']['type'] == "MultiLineString"):
                continue
            if (feature['geometry']['type'] == 'MultiPolygon'):
                s = s[0]
            s = s[0]
            for u in s:
                u.reverse()
            g = Polygon(s)
            if (F.within(g) == True):
                poi = True
                break
        js.close()
        return poi