import MySQLdb
import hashlib
import re
import random
import datetime

USER_REGEX = re.compile("[A-Za-z0-9]{4,55}")
SQL_PROTECTION_REGEX = re.compile("[a-fA-F0-9]{4,36}")


class User:
    SORT_LAST_LOGIN = 1
    
    def __init__(self, username=None, password=None):
        self.username = username
        if self.username:
            together = username + password
            self.password = hashlib.sha256(together.encode('utf-8')).hexdigest()
        else:
            self.password = None
        self.last_logged_in = datetime.datetime.now()
        self.user_id = -1
        self.status = None
        self.session_id = None

    def validate_session(self, session_token):
        if not SQL_PROTECTION_REGEX.match(session_token):
            # guard against sql injection
            return False
        db = MySQLdb.connect(host="localhost", user="root", database='tensor_flow')
        c = db.cursor()
        try:
            c.execute("SELECT user_id,username,password,last_login,status FROM users WHERE session_token=%s",
                      (session_token,))
            row = c.fetchone()
            if row:
                self.user_id = row[0]
                self.username = row[1]
                self.password = row[2]
                self.last_logged_in = row[3]
                self.status = row[4]
                self.session_id = session_token
                c.close()
                db.close()
                return True
        except MySQLdb.Error as e:
            c.close()
            db.close()
        return False

    def create_user(self):
        if not USER_REGEX.match(self.username):
            # protect against sql injection
            return None
        db = MySQLdb.connect(host="localhost", user="root", database='tensor_flow')
        c = db.cursor()
        self.session_id = new_session_token()
        try:
            c.execute("INSERT INTO users (username,password,session_token) VALUES (%s,%s,%s);",
                      (self.username, self.password, self.session_id))
            last_row = c.lastrowid
            c.close()
            db.commit()
            db.close()
            return last_row, self.session_id
        except MySQLdb.Error as e:
            c.close()
            db.close()
            return None

    @staticmethod
    def count_users():
        db = MySQLdb.connect(host="localhost", user="root", database="tensor_flow")
        c = db.cursor()
        try:
            c.execute("SELECT COUNT(*) FROM users;")
            row = c.fetchone()
            c.close()
            db.close()
            return row[0]
        except MySQLdb.Error as e:
            c.close()
            db.close()
            return 0

    def logout(self, session_token):
        if not SQL_PROTECTION_REGEX.match(session_token):
            return False
        db = MySQLdb.connect(host="localhost", user="root", database="tensor_flow")
        c = db.cursor()
        c.execute("SELECT user_id FROM users WHERE session_token=%s", (session_token,))
        row = c.fetchone()
        result = 0
        if row:
            result = c.execute("UPDATE users SET session_token=NULL WHERE user_id=%s", (row[0],))
        c.close()
        if result == 1:
            self.session_id = None
            self.user_id = -1
            self.username = None
            self.password = None
            self.last_logged_in = None
            db.commit()
            db.close()
            return True
        db.close()
        return False

    def login(self):
        if not USER_REGEX.match(self.username):
            return None
        db = MySQLdb.connect(host="localhost", user="root", database='tensor_flow')
        c = db.cursor()
        c.execute("SELECT user_id,password,last_login FROM users WHERE username=%s", (self.username,))
        row = c.fetchone()
        if row is None:
            return row
        if row[1] != self.password:
            return None
        self.last_logged_in = row[2]
        self.user_id = row[0]
        self.session_id = new_session_token()
        c.execute("UPDATE users SET session_token=%s WHERE user_id=%s", (self.session_id, self.user_id))
        db.commit()
        c.close()
        db.close()
        return self.user_id, self.session_id

    @staticmethod
    def get_all_users(sort=None):
        sql = "SELECT user_id, username, password, session_token, last_login, status FROM users"
        if sort == User.SORT_LAST_LOGIN:
            sql += " ORDER BY last_login DESC"
        db = MySQLdb.connect(host="localhost", user="root", database='tensor_flow')
        c = db.cursor()
        all_users = []
        try:
            c.execute(sql)
            for row in c:
                new_user = User()
                new_user.user_id = row[0]
                new_user.username = row[1]
                new_user.password = row[2]
                new_user.session_id = row[3]
                new_user.last_logged_in = row[4]
                new_user.status = row[5]
                all_users.append(new_user)
            c.close()
            db.close()
            return all_users
        except MySQLdb.Error as e:
            c.close()
            db.close()
            return None


def new_session_token():
    token = "%08x%08x" % (random.randint(0, 0xffffffff), random.randint(0, 0xffffffff))
    return token.upper()


if __name__ == "__main__":
    print("Attempting to create admin user...")
    admin_password = input("Administrator password: ")
    u = User("admin", admin_password)
    admin_account = u.create_user()
    if admin_account:
        print("Admin account created")
    else:
        print("Could not create admin account.")

