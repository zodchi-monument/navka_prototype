import sqlalchemy as db
from sqlalchemy import Table, Column, Integer, Float


class Navka_db:
    url = 'mysql+pymysql://root:qwerty@localhost/NAVKA2'
    engine = db.create_engine(url)

    @staticmethod
    def init_value_table(name, meta):
        ret = Table(name, meta, Column('vid', Integer), Column('sid', Integer),Column('tick', Integer),
                    Column('x', Float), Column('y', Float), Column('z', Float))
        return ret

    def __init__(self):
        """
            Описаны основные сущности в БД NAVKA2
        """ 
        meta = db.MetaData(db)
        # Сессия - Характеристики тренировочной сессии
        self.Sessions = Table('Sessions', meta, Column('sid', Integer), Column('date', Integer))
        # Данные акселерометра - сырые данные с датчика акселерометра с привязкой к сессиям
        self.vAcc = self.init_value_table('vAcc', meta)
        # Данные гироскопа - сырые данные с датчика гироскопа с привязкой к сессиям
        self.vGyro = self.init_value_table('vGyro', meta)
        # Каскады в рамках сессии - отрезки в данных во время которых происходит несколько прыжков, и сопутствующих
        # колебаний показаний датчика
        self.Cscds = Table('Cscds', meta, Column('cid', Integer), Column('sid', Integer),Column('t0', Integer),
                           Column('tn', Integer))
        # Идентификаторы начала и конца прыжков в рамках каскада
        self.Jmps = Table('Jmps', meta, Column('jid', Integer), Column('cid', Integer), Column('strt', Integer),
                           Column('stop', Integer))
        # Тренды от начала до конца прыжков, для просто вычислений для отображения на фронте (акселерометр и гироскоп).
        self.vJmps = Table('vJmps', meta, Column('id', Integer), Column('jid', Integer), Column('tick', Integer),
                          Column('a', Float), Column('g', Float))
        self.connection = self.engine.connect()

    def get_jumps_in_session(self, ssi):
        sql = self.Jmps.join(self.Cscds, self.Cscds.c.cid == self.Jmps.c.cid).select().where(self.Cscds.c.sid == ssi)
        result = self.connection.execute(sql).fetchall()
        return result

    def get_trend_by_jmps_id(self, jid):
        sql = self.vJmps.join(self.Jmps, self.Jmps.c.jid == self.vJmps.c.jid).select().where(self.Jmps.c.jid == jid)
        result = self.connection.execute(sql).fetchall()
        return result

    def get_jmp_strt_stop(self, jid):
        sql = self.Jmps.select().where(self.Jmps.c.jid == jid)
        result = self.connection.execute(sql).fetchall()
        return result

    def get_trend_by_session_id(self, sid):
        sql = self.vAcc.select().where(self.vAcc.c.sid == sid)
        result = self.connection.execute(sql).fetchall()
        return result

    def get_cscds_by_session_id(self, sid):
        sql = self.Cscds.select().where(self.Cscds.c.sid == sid)
        result = self.connection.execute(sql).fetchall()
        return result

    def get_jmp_ids_by_cscd(self, cid):
        sql = self.Jmps.select().where(self.Jmps.c.cid == cid)
        result = self.connection.execute(sql).fetchall()
        return result

    def get_jmp_by_id(self, j):
        sql = self.vJmps.select().where(self.vJmps.c.jid == int(j))
        result = self.connection.execute(sql).fetchall()
        return result


if __name__ == "__main__":
    db = Navka_db()
