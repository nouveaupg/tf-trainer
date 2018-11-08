import MySQLdb
import json
import sys


class NotConnectedToDatabase(Exception):
    """ Raised when the connection to the database failed """
    pass


def reset_admin_password_console():
    print("Setting new admin password:")
    while 1:
        first = getpass.getpass(prompt="new admin password: ")
        repeat = getpass.getpass(prompt="repeat to confim: ")
        if first == repeat:
            print("New admin password.")
            return first
        else:
            print("Passwords must match. CTRL-C to exit.")


class Database:
    def __init__(self, logger=None):
        self.db_connected = False
        self.logger = logger
        try:
            config_stream = open("config.json", "r")
            config_data = json.load(config_stream)
            config_stream.close()
            db_host = config_data['mysql_host']
            db_username = config_data['mysql_user']
            db_password = config_data['mysql_password']
            db_name = config_data['mysql_database']
            db = MySQLdb.connect(db_host, db_username, db_password, db_name)
            if db:
                self.db = db
                self.db_connected = True
        except FileNotFoundError:
            if self.logger:
                self.logger = self.logger.error("config.json not found.")
        except MySQLdb.Error as e:
            try:
                if self.logger:
                    self.logger.error("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
                else:
                    print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
            except IndexError:
                if self.logger:
                    self.logger.error("MySQL Error: %s" % (str(e),))
                else:
                    print("MySQL Error: %s" % (str(e),))

    def get_admin_id(self):
        if self.db_connected is False:
            raise NotConnectedToDatabase
        try:
            c = self.db.cursor()
            c.execute("SELECT user_id FROM users WHERE email_address='admin';")
            row = c.fetchone()
            c.close()
            if row:
                return row[0]
            return 0
        except MySQLdb.Error as e:
            # don't even check for the logger since this only runs from the console.
            try:
                print("MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
            except IndexError:
                print("MySQL Error: %s" % (str(e),))
        return -1


if __name__ == "__main__":
    import sys

    try:
        db = Database()
        print("Connected to database successfully, checking for admin user.")
        admin_id = db.get_admin_id()
    except NotConnectedToDatabase:
        print("Could not connect to database, check the config.json file.")
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


