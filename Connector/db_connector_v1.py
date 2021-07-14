from pymetawear.client import MetaWearClient
import datetime, signal
from mysql import connector
import time


def handler(signum, frame):
    c.disconnect()


def run_sensor(sensor, table, settings, db, id):
    """
    Запись потока данных с датчика в соответствующую таблицу.
    :param sensor: MetaWearClient - характеризует датчик с которого тянутся данные.
    :param table: String - имя таблицы
    :param settings: dict - Настройки потока
    :param db: dict - Настройки подключения
    :param id: int - id записи в БД (sid)
    """
    con = connector.connect(**db)

    def callback(data):
        print(data)
        v = data['value']
        cursor = con.cursor(v)
        sql = f"INSERT INTO {table} (sid,tick,x,y,z) \
                VALUES ({id},{data['epoch'] - now},{v.x},{v.y},{v.z})"
        cursor.execute(sql)
        con.commit()

    print("Write acc settings...")
    sensor.set_settings(**settings)
    print("Subscribing to acc signal notifications...")
    sensor.high_frequency_stream = False
    sensor.notifications(callback)


if __name__ == "__main__":

    # Параметры устройства и записи в БД
    mac = "FC:70:05:86:16:03"
    db = {'host': '127.0.0.1', 'user': 'root', 'password': 'pass', 'database': 'NAVKA2'}
    id = 0

    c = MetaWearClient(mac, 'hci0', debug=True)
    print("New client created: {0}".format(c))
    signal.signal(signal.SIGTSTP, handler)

    print("Connecting to DB...")
    now = int(datetime.utcnow().timestamp() * 1e3)

    # Запуск записи данных с сенсора
    run_sensor(c.accelerometer, 'vAcc', {'data_rate': 200, 'data_range': 16.0}, db, id)
    run_sensor(c.gyroscope, 'vGyro', {'data_rate': 200, 'data_range': 2000.0}, db, id)

    try:
        time.sleep(20)
    except KeyboardInterrupt:
        print('KeyboardInterrupt occured')
        c.disconnect()
