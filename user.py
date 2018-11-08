import MySQLdb
import hashlib
import re
import datetime
import binascii

USER_REGEX = re.compile("[A-Za-z0-9]{4,55}")
SQL_PROTECTION_REGEX = re.compile("[a-fA-F0-9]{4,36}")


class RegexException(Exception):
    """ Raised when input fails a RegEx match """
    pass


class User:
    SORT_LAST_LOGIN = 1

    def __init__(self, db, username=None, password=None):
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
        self.db = db

    def validate_session(self, session_token):
        if not SQL_PROTECTION_REGEX.match(session_token):
            # guard against sql injection
            raise RegexException
        c = self.db.cursor()
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
            try:
                if e.args[0] == 1062:
                    return -1, "E-mail address already exists in database!"
                if self.logger:
                    self.logger.error("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
                else:
                    print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
            except IndexError:
                if self.logger:
                    self.logger.error("MySQL Error: %s" % (str(e),))
                else:
                    print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
        return False

    def create_user(self):
        if not USER_REGEX.match(self.username):
            # protect against sql injection
            raise RegexException
        c = self.db.cursor()
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
            try:
                if e.args[0] == 1062:
                    return -1, "E-mail address already exists in database!"
                if self.logger:
                    self.logger.error("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
                else:
                    print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
            except IndexError:
                if self.logger:
                    self.logger.error("MySQL Error: %s" % (str(e),))
                else:
                    print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
        return None

    def count_users(self):
        c = self.db.cursor()
        try:
            c.execute("SELECT COUNT(*) FROM users;")
            row = c.fetchone()
            c.close()
            db.close()
            return row[0]
        except MySQLdb.Error as e:
            try:
                if e.args[0] == 1062:
                    return -1, "E-mail address already exists in database!"
                if self.logger:
                    self.logger.error("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
                else:
                    print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
            except IndexError:
                if self.logger:
                    self.logger.error("MySQL Error: %s" % (str(e),))
                else:
                    print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
        return 0

    def logout(self, session_token):
        if not SQL_PROTECTION_REGEX.match(session_token):
            # protect against sql injection
            return RegexException
        c = self.db.cursor()
        c.execute("SELECT user_id FROM users WHERE session_token=%s", (session_token,))
        row = c.fetchone()
        sql_result = 0
        if row:
            sql_result = c.execute("UPDATE users SET session_token=NULL WHERE user_id=%s", (row[0],))
        c.close()
        if sql_result == 1:
            self.session_id = None
            self.user_id = -1
            self.username = None
            self.password = None
            self.last_logged_in = None
            self.db.commit()
            return True
        return False

    def login(self):
        if not USER_REGEX.match(self.username):
            return None
        c = self.db.cursor()
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
        self.db.commit()
        c.close()
        return self.user_id, self.session_id

    def get_all_users(sort=None):
        sql = "SELECT user_id, username, password, session_token, last_login, status FROM users"
        if sort == User.SORT_LAST_LOGIN:
            sql += " ORDER BY last_login DESC"
        c = self.db.cursor()
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
            try:
                if e.args[0] == 1062:
                    return -1, "E-mail address already exists in database!"
                if self.logger:
                    self.logger.error("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
                else:
                    print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
            except IndexError:
                if self.logger:
                    self.logger.error("MySQL Error: %s" % (str(e),))
                else:
                    print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))


def new_session_token():
    rng_out = os.urandom(8)
    new_token += binascii.hexlify(rng_out).decode()
    return new_token


if __name__ == "__main__":
    import sys

    db = Database()
    print("Connected to database successfully, checking for admin user.")
    admin_id = db.get_admin_id()
    if admin_id:
        print("Account 'admin' found, reset password? (Y/n)")
        raw_input = input("> ")
        if raw_input == "Y":
            new_passwd = reset_admin_password_console()
            db.reset_password(admin_id, new_passwd)
            print("Reset admin password.")
            sys.exit(0)
    else:
        print("No admin account found, creating a new one.")
        new_passwd = reset_admin_password_console()
        result = db.create_user("Administrator", "admin", new_passwd, "console")
        if result:
            print("Successfully created new admin user.")
            sys.exit(0)
        else:
            print("Failed to create new admin user.")
            sys.exit(1)
