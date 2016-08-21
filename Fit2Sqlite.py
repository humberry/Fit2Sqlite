# coding: utf-8
import sqlite3
import sys
from fitparse import FitFile, FitParseError

class Fit2Sqlite(object):
    def __init__(self, path, files):
        self.shape_type_def = {0: 'Null Shape',1: 'Point', 3: 'PolyLine', 5: 'Polygon', 8: 'MultiPoint', 11: 'PointZ', 13: 'PolyLineZ', 15: 'PolygonZ', 18: 'MultiPointZ', 21: 'PointM', 23: 'PolyLineM', 25: 'PolygonM', 28: 'MultiPointM', 31: 'MultiPatch'}
        
        self.path = path
        self.sqlcon = None
        self.sqlcur = None
        self.shapes = []
        self.shapes_count = 0
        self.polys = []
        self.polys_count = 0
        self.points = []
        self.points_count = 0
        
        self.check_tables()
        print(str(self.shapes_count) + ' shapes, ' + str(self.polys_count) + ' polys and ' + str(self.points_count) + ' points')
        print()
        self.shapes_count += 1
        self.polys_count += 1

        for i in range(len(files)):        
            self.read_files(files[i])
        self.sqlcon.close()
        print('db closed')
        print('exit')
       
    def check_tables(self):
        self.sqlcon = sqlite3.connect('earth.db')
        self.sqlcur = self.sqlcon.cursor()
        
        #ID_Shape = For each shape(file/table)
        #ID_Poly = For each poly(line/gon or for many points like cities)
        #ID_Point = For each point per poly
        cursor = self.sqlcur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='Shapes'")
        if cursor.fetchone()[0] == 0:
            self.sqlcur.execute("CREATE TABLE 'Shapes' ('ID_Shape' INTEGER, 'Name' TEXT)")
            #print 'Table Shapes is created'
        else:
            #print 'Table Shapes exists'
            cursor = self.sqlcur.execute("SELECT max(ID_Shape) FROM Shapes")
            self.shapes_count = cursor.fetchone()[0]
            if self.shapes_count == None:
                self.shapes_count = 0
                
        cursor = self.sqlcur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='Polys'")
        if cursor.fetchone()[0] == 0:
            self.sqlcur.execute("CREATE TABLE 'Polys' ('ID_Shape' INTEGER, 'ID_Poly' INTEGER, 'ShapeType' INTEGER, 'Xmin' REAL, 'Ymin' REAL, 'Xmax' REAL, 'Ymax' REAL, 'NumParts' INTEGER, 'NumPoints' INTEGER, 'Name' TEXT)")
            self.sqlcon.commit()
            #print 'Table Polys is created'
        else:
            #print 'Table Polys exists'
            cursor = self.sqlcur.execute("SELECT max(ID_Poly) FROM Polys")
            self.polys_count = cursor.fetchone()[0]
            if self.polys_count == None:
                self.polys_count = 0
                
        cursor = self.sqlcur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='Points'")
        if cursor.fetchone()[0] == 0:
            self.sqlcur.execute("CREATE TABLE 'Points' ('ID_Poly' INTEGER, 'ID_Point' INTEGER, 'Part' INTEGER, 'X' REAL, 'Y' REAL, 'Name' TEXT)")
            #print 'Table Points is created'
        else:
            #print 'Table Points exists'
            cursor = self.sqlcur.execute("SELECT COUNT(*) FROM Points")
            self.points_count = cursor.fetchone()[0]

    def get_points(self, shape, ShapeType):
        index = 1
        part = 0
        num_parts = len(shape.parts)
        num_points = len(shape.points)
        
        parts_end = []
        if num_parts == 1:
            parts_end.append(num_points)
        else:
            parts_end = shape.parts[1:]
            parts_end.append(num_points)

        for i in xrange(num_points):
            if i == parts_end[part]:
                part += 1
                index = 1
                self.points.append((self.polys_count, index, part, shape.points[i][0], shape.points[i][1], None))
                index += 1
            else:
                self.points.append((self.polys_count, index, part, shape.points[i][0], shape.points[i][1], None))
                index += 1
            
    def read_files(self, file):
        try:
            fitfile = FitFile(file + ".fit")
            fitfile.parse()
        except FitParseError as e:
            print("Error while parsing .fit file: %s" % e)
            sys.exit(1)

        self.shapes = []
        self.points = []
        self.polys = []
            
        records = list(fitfile.get_messages(name='record'))
        amount_records = len(records)
        
        Xmin = None
        Ymin = None
        Xmax = None
        Ymax = None
        
        i = 1
        x = None
        y = None
        name = None
        for record in records:
            for field in record:
                if field.name == 'position_lat' or field.name == 'position_long':
                    if field.name == 'position_lat':
                        y = field.value * (180.0 / 2147483648)
                    else:
                        x = field.value * (180.0 / 2147483648)
            if x != None and y != None:
                self.points.append((self.polys_count, i, 0, x, y, name))
                i += 1
                if Xmin == None:
                    Xmin = x
                else:
                    if x < Xmin:
                        Xmin = x
                if Ymin == None:
                    Ymin = y
                else:
                    if y < Ymin:
                        Ymin = y
                if Xmax == None:
                    Xmax = x
                else:
                    if x > Xmax:
                        Xmax = x
                if Ymax == None:
                    Ymax = y
                else:
                    if y > Ymax:
                        Ymax = y
            x = None
            y = None
        
        #print("Xmin = %.7f," % Xmin, "Ymin = %.7f" % Ymin)
        #print("Xmax = %.7f," % Xmax, "Ymax = %.7f" % Ymax)
        ShapeType = 3
        #print(self.shape_type_def[ShapeType])
        NumParts = 1
        NumPoints = len(self.points)
        name = None
        self.polys.append((self.shapes_count, self.polys_count, ShapeType, Xmin, Ymin, Xmax, Ymax, NumParts, NumPoints, name))

        self.shapes.append((self.shapes_count, file))

        if len(self.shapes) > 0:
            self.sqlcur.executemany("INSERT INTO Shapes VALUES (?, ?)", self.shapes)
            print('added ' + str(len(self.shapes)) + ' shape ' + file)
            self.sqlcon.commit()
        if len(self.polys) > 0:
            self.sqlcur.executemany("INSERT INTO Polys VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", self.polys)
            print('added ' + str(len(self.polys)) + ' polys')
            self.sqlcon.commit()
        if len(self.points) > 0:
            self.sqlcur.executemany("INSERT INTO Points VALUES (?, ?, ?, ?, ?, ?)", self.points)
            print('added ' + str(len(self.points)) + ' points')
            self.sqlcon.commit()
        print()
        self.shapes_count += 1
        self.polys_count += 1
        
if __name__ == '__main__':
    path = 'activities/'
    
    files_fit = ('2016-06-07-16-05-17',)
    
    Fit2Sqlite(path, files_fit)
