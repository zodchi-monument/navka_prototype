from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear import libmetawear as lmw
from mbientlab.metawear.cbindings import *
from mysql import connector
from datetime import datetime


class State:
    def __init__(self, device):
        self.device = device
        self.samples = 0
        self.g_callback = FnVoid_VoidP_DataP(self.g_handler)
        self.a_callback = FnVoid_VoidP_DataP(self.a_handler)

    def g_handler(self, ctx, data):
        v = parse_value(data)
        e = data.contents.epoch - now
        sql = f"INSERT INTO vGyro (sid,tick,x,y,z) VALUES ({ID},{e},{v.x},{v.y},{v.z})"
        print(sql)
        cursor = con_a.cursor()
        cursor.execute(sql)
        con_a.commit()

    def a_handler(self, ctx, data):
        v = parse_value(data)
        e = data.contents.epoch - now
        sql = f"INSERT INTO vAcc (sid,tick,x,y,z) VALUES ({ID},{e},{v.x},{v.y},{v.z})"
        print(sql)
        cursor = con_g.cursor()
        cursor.execute(sql)
        con_g.commit()


if __name__ == "__main__":

    params = {'host': '127.0.0.1', 'user': 'root', 'password': 'T0_Gather', 'database': 'NAVKA2'}
    con_a = connector.connect(**params)
    con_g = connector.connect(**params)
    now = int(datetime.utcnow().timestamp() * 1e3)
    ID = 2

    d = MetaWear("FC:70:05:86:16:03")
    d.connect()
    print("Connected to " + d.address)
    s = State(d)

    print("Configuring device")
    lmw.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)

    lmw.mbl_mw_acc_set_odr(s.device.board, 200.0)
    lmw.mbl_mw_acc_set_range(s.device.board, 16)
    lmw.mbl_mw_acc_write_acceleration_config(s.device.board)

    signal = lmw.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    lmw.mbl_mw_datasignal_subscribe(signal, None, s.a_callback)
    lmw.mbl_mw_acc_enable_acceleration_sampling(s.device.board)
    lmw.mbl_mw_acc_start(s.device.board)

    lmw.mbl_mw_gyro_bmi160_set_odr(s.device.board, AccBmi160Odr._200Hz)
    lmw.mbl_mw_gyro_bmi160_set_range(s.device.board, 2000)
    lmw.mbl_mw_gyro_bmi160_write_config(s.device.board)
    signal = lmw.mbl_mw_gyro_bmi160_get_rotation_data_signal(s.device.board)
    lmw.mbl_mw_datasignal_subscribe(signal, None, s.g_callback)
    lmw.mbl_mw_gyro_bmi160_enable_rotation_sampling(s.device.board)
    lmw.mbl_mw_gyro_bmi160_start(s.device.board)

    print('start')
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print('KeyboardInterrupt occured')

        lmw.mbl_mw_acc_stop(s.device.board)
        lmw.mbl_mw_acc_disable_acceleration_sampling(s.device.board)
        a_signal = lmw.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
        lmw.mbl_mw_datasignal_unsubscribe(a_signal)

        lmw.mbl_mw_gyro_bmi160_stop(s.device.board)
        lmw.mbl_mw_gyro_bmi160_disable_rotation_sampling(s.device.board)
        g_signal = lmw.mbl_mw_gyro_bmi160_get_rotation_data_signal(s.device.board)
        lmw.mbl_mw_datasignal_unsubscribe(g_signal)

        libmetawear.mbl_mw_debug_disconnect(s.device.board)
        con_a.close()
        con_g.close()
