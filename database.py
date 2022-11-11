import sqlite3


class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self._con = sqlite3.connect(db_name)
        self.cur = self._con.cursor()
        self.openned_table = None

    def current_table(self, name):
        self.openned_table = name

    def create_table(self, name):
        self.name = name

        self.cur.execute(f"""CREATE TABLE {self.name} (
    ID    INTEGER PRIMARY KEY AUTOINCREMENT
                  UNIQUE
                  NOT NULL,
    event         NOT NULL,
    [key],
    delay);""")

        self.cur.execute(f"""insert into macro_db(name) values(?)""", (self.name,))
        self._con.commit()

    def add_events(self, lst):
        for event in lst:
            if 'pressed' in event or 'released' in event:
                self.cur.execute(f"""insert into {self.name}(event, key) values(?, ?)""", event.split())

            else:
                self.cur.execute(f"""insert into {self.name}(event, delay) values(?, ?)""", ('delay', event.split()[0]))

        self._con.commit()

    def get_macro_info(self):
        return self.cur.execute(f"""select name from macro_db""").fetchall()

    def get_events(self):
        print('ogdskgspdsokg')
        return self.cur.execute(f"""select event, key, delay from {self.openned_table}""").fetchall()

    def set_bind_key(self, key):
        self.cur.execute(f"""UPDATE macro_db
                                SET bind = '{key}'
                                WHERE name = '{self.openned_table}'""")
        self._con.commit()

    def get_bind_key(self):
        return self.cur.execute(f"""select bind from macro_db where name = '{self.openned_table}'""").fetchone()[0]

    def delete_item(self, item):
        self.cur.execute(f"DELETE FROM macro_db WHERE name = '{item}'")
        self.cur.execute(f"DROP TABLE IF EXISTS {item}; ")
        self._con.commit()


    def close(self):
        self._con.close()
