import MySQLdb
import json
import datetime


class PostedImage:
    def __init__(self, make=None, model=None, year=None, url=None, uploader_id=None):
        self.make = make
        self.model = model
        self.year = year
        self.url = url
        self.uploader_id = uploader_id
        self.image_id = 0
        self.uploaded = datetime.datetime.now()
        self.metadata = {}
        self.processed = None

    def store(self):
        if self.image_id != 0:
            # image already in database
            return self.image_id

        db = MySQLdb.connect(host="localhost", user="root", database='tensor_flow')
        c = db.cursor()
        try:
            c.execute("INSERT INTO posted_images (year,make,model,url,uploader_id) VALUES (%s,%s,%s,%s,%s)",
                  (self.year, self.make, self.model, self.url, self.uploader_id))
            self.image_id = c.lastrowid
            if len(self.metadata) > 0:
                c.execute("UPDATE posted_images SET json_data=%s WHERE image_id=%s",(json.dumps(self.metadata),self.image_id))
            db.commit()
            c.close()
            db.close()
            return self.image_id
        except MySQLdb.Error as e:
            c.close()
            db.close()
            return 0

    def fetch_metadata(self):
        # image_id = 0 means no database record
        if self.image_id == 0:
            return None
        db = MySQLdb.connect(host="localhost", user="root", database='tensor_flow')
        c = db.cursor()
        try:
            c.execute("SELECT json_data FROM posted_images WHERE image_id=%s",(self.image_id,))
            row = c.fetchone()
            c.close()
            db.close()
            if row:
                self.metadata = json.loads(row[0])
                return self.metadata
        except MySQLdb.Error as e:
            c.close()
            db.close()
        return None

    def flush_metadata(self):
        if self.image_id == 0:
            return False
        db = MySQLdb.connect(host="localhost", user="root", database='tensor_flow')
        c = db.cursor()
        try:
            result = c.execute("UPDATE posted_images SET json_data=%s WHERE image_id=%s",(json.dumps(self.metadata),self.image_id))
            db.commit()
            c.close()
            db.close()
            if result == 1:
                return True
            return False
        except MySQLdb.Error as e:
            c.close()
            db.close()
            return False


    @staticmethod
    def date_of_last_image_posted_by(uploader_id):
        db = MySQLdb.connect(host="localhost", user="root", database="tensor_flow")
        c = db.cursor()
        try:
            c.execute("SELECT uploaded FROM posted_images WHERE uploader_id=%s ORDER BY uploaded DESC LIMIT 1",
                      (uploader_id,))
            row = c.fetchone()
            if row:
                c.close()
                db.close()
                return row[0]
        except MySQLdb.Error as e:
            # TODO: maybe some logging in the future for all these MySQL exception handlers
            pass
        c.close()
        db.close()
        return None


    @staticmethod
    def count_posted_images(uploader_id=None,processed=False):
        db = MySQLdb.connect(host="localhost", user="root", database="tensor_flow")
        c = db.cursor()
        sql = "SELECT COUNT(*) FROM posted_images"
        if processed is False:
            sql += " WHERE processed IS NULL"
        try:
            if uploader_id:
                if processed is False:
                    sql += " AND uploader_id=%s"
                else:
                    sql += " WHERE uploader_id=%s"
                c.execute(sql, (uploader_id,))
            else:
                c.execute(sql)
            row = c.fetchone()
            c.close()
            db.close()
            return row[0]
        except MySQLdb.Error as e:
            c.close()
            db.close()
            return 0

    @staticmethod
    def get_images(uploader_id=None,processed=False):
        # TODO: probably want some paging (offset/limit) here at some point)
        images = []
        db = MySQLdb.connect(host="localhost", user="root", database="tensor_flow")
        c = db.cursor()
        sql = "SELECT image_id, year, make, model, url, uploader_id,processed,uploaded FROM posted_images"
        if processed is False:
            sql += " WHERE processed IS NULL"
        try:
            if uploader_id:
                if processed is False:
                    sql += " AND uploader_id=%s"
                else:
                    sql += " WHERE uploader_id=%s"
                c.execute(sql,(uploader_id,))
            else:
                c.execute(sql)
            for row in c:
                new_image = PostedImage(row[2],row[3],row[1],row[4],row[5])
                new_image.uploaded = row[7]
                new_image.image_id = row[0]
                new_image.processed = row[6]
                images.append(new_image)
            c.close()
            db.close()
            return images
        except MySQLdb.Error as e:
            c.close()
            db.close()
            return None
