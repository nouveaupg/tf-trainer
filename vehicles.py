import MySQLdb
import re

YEAR_REGEX = re.compile("[1-2][0-9]{3}")


class Vehicle:
    def __init__(self, year, make, model, s3path, uploader):
        self.year = year
        self.make = make
        self.model = model
        self.s3path = s3path
        self.uploader = uploader
        self.vehicle_id = 0

    def store(self):
        if self.vehicle_id:
            return 0  # already in database

        db = MySQLdb.connect(host='localhost', user='root', database='tensor_flow')
        c = db.cursor()
        sql = "INSERT INTO posted_images (year,make,model,url,uploader_id) VALUES ({0},'{1}','{2}','{3}',{4});".format(self.year,
                                                                                                                       self.make,
                                                                                                                       self.model,
                                                                                                                       self.s3path,
                                                                                                                       self.uploader_id)
        try:
            c.execute(sql)
            last_row = c.lastrowid
            self.vehicle_id = last_row
            c.close()
            db.close()
            return last_row
        except:
            c.close()
            db.close()
            return 0

    def get_vehicles_by_criteria(self, year=None, make=None, model=None, uploader=None):
        predicate = ""
        if year:
            predicate = "year=" + year
        if make:
            if len(predicate) > 0:
                predicate += " AND make='{0}'".format(make)
            else:
                predicate = "make='{0}'".format(make)
        if model:
            if len(predicate) > 0:
                predicate += " AND model='{0}'".format(model)
            else:
                predicate = "model='{0}'".format(model)
        if uploader:
            if len(predicate) > 0:
                predicate += " AND uploader_id={0}".format(uploader)
            else:
                predicate = "uploader_id={0}".format(uploader)
        sql = "SELECT vehicle_id,year,make,model,s3path,uploader_id,processed FROM vehicles WHERE {0};".format(predicate)
        db = MySQLdb.connect(host="localhost", user="root", database="tensor_flow")
        c = db.cursor()
        c.execute(sql)
        results = []
        for each in c:
            newVehicle = Vehicle(each[1], each[2], each[3], each[4], each[5])
            newVehicle.vehicle_id = each[0]
            newVehicle.processed = each[6]
            results.append(newVehicle)
        return results

    def count_vehicles_by_criteria(self, year=None, make=None, model=None, uploader_id=None):
        predicate = ""
        if year:
            predicate = "year=" + year
        if make:
            if len(predicate) > 0:
                predicate += " AND make='{0}'".format(make)
            else:
                predicate = "make='{0}'".format(make)
        if model:
            if len(predicate) > 0:
                predicate += " AND model='{0}'".format(model)
            else:
                predicate = "model='{0}'".format(model)
        if uploader_id:
            if len(predicate) > 0:
                predicate += " AND uploader={0}".format(uploader_id)
            else:
                predicate = "uploader={0}".format(uploader_id)
        sql = "SELECT COUNT(*) FROM posted_images WHERE {0};".format(predicate)
        db = MySQLdb.connect(host="localhost", user="root", database="tensor_flow")
        c = db.cursor()
        c.execute(sql)
        row = c.fetchone()
        c.close()
        db.close()
        if row:
            return row[0]
        else:
            return 0
