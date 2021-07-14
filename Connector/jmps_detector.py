from scipy.signal import filtfilt, butter, argrelextrema
from mysql import connector
import pandas as pd
import numpy as np
import time


def minmax(a):
    """
    Вспомогательный метод вместо MinMaxScaler
    :param a: Массив данных без скейлинга
    :return: Массив данных со скейлингом
    """
    result = []
    mn, mx = min(a), max(a)
    if mn != mx:
        for i in a:
            result.append((i - mn) / (mx - mn))
    else:
        result = a
    return np.array(result)


# Вспомогательный метод вместо фильтрация + MinMaxScaler
fminmax = lambda d, f, s: minmax(abs(filtfilt(*butter(3, f, s), d, axis=0)))


def get_csc(d, max_gap=150, min_acc=4.5, min_csc_size=300):
    """
    Метод определяющий каскады прыжков из заранее фильтрованных данных (Верхнеуровневая обработка)
    :param data: Массив данных
    :param max_gap: максимальный промежуток между двумя каскадами, при котором они будут объеденены
    :param min_acc: минимальныое ускорение по акселерометру при котором будет детектироваться каскад.
    :param min_csc_size: Минимальный размер детекируемых каскадов
    :return: Массив каскадов (t_start, t_end)
    """

    # Обработка только значений выше нижнего порога.
    ind = d[d > min_acc].index.values

    # Объединение всплесков с каскадами.
    res = [[ind[0]]]
    for i in range(len(ind)-1):
        d = ind[i+1]-ind[i]
        # Объединение малых всплесков в каскады
        if d > max_gap:
            res[-1].append(ind[i])
            res.append([ind[i+1]])
    res[-1].append(ind[-1])

    # Удаление каскадов, длительность которых мала для прыжка
    result = []
    for c in res:
        a, b = c
        if b-a > min_csc_size:
            # Корректировка, чтобы захватить минимумы после каскада
            result.append((a, b))
    return result


def get_jmp(d, f=0.015):
    """
    Метод определяющий прыжки в каскадах из заранее фильтрованных данных (Нижнеуровневая обработка)
    :param d: Данные для анализа
    :param f: Частота фильтра
    :return: ret: Массив прыжков (t_start, t_end, Series) с интерполированными данными
    """
    ret = []
    if max(d['a'].values) > 10:

        # Интерполяция данных на единую сетку по 1 мск.
        t = d.index.values
        ti = list(range(t[0], t[-1], 1))
        d = pd.merge(pd.DataFrame(index=ti), d, left_index=True, right_index=True, how='outer')
        d = d.interpolate()

        # Поиск градиентов по данным.
        d_n = fminmax(d, 0.5, 'hp')
        g = np.gradient(d_n.T[0], edge_order=2)

        # Поиск экстремумов по графику градиента.
        dat = fminmax(g, f, 'lp')
        g = pd.Series(dat, index=d.index.values)
        ex = list(argrelextrema(dat, np.greater, order=10)[0])

        # Формирование данных по прыжкам из пары точек начало конец и интерполированных данных
        # HINT: На данном этапе заложен только один приыжок на каскад, для упрощения задачи
        if len(ex) >= 2:
            ex = list(g.iloc[ex].nlargest(2).index)
            t0, tn = min(ex), max(ex)
            if tn - t0 > 250:
                ret = [(t0, tn, d.loc[t0 - 50:tn + 50])]
    return ret


if __name__ == "__main__":

    sid = 5
    db = dict(host='127.0.0.1', user='root', password='T0_Gather', database='NAVKA2')

    while True:
        conn = connector.connect(**db)
        cursor = conn.cursor()

        cursor.execute(f"SELECT tick FROM vAcc WHERE sid={sid};")
        # Номер последней записи в сессии
        i_n = cursor.fetchall()
        i_n, t_n = len(i_n), max(i_n)[0]

        # Определение завершенности последнего каскада
        cursor.execute(f"SELECT MAX(tn) FROM Cscds WHERE sid={sid}")

        # Номер записи на которой закончился последний каскад
        i_c = cursor.fetchall()[0][0]

        if i_n == i_c:
            cursor.execute(f"SELECT MAX(t0) FROM Cscds WHERE sid={sid}")

            # Номер записи на которой начался последний каскад
            i_c = cursor.fetchall()[0][0]

        i_c = i_c if i_c else 0
        print(f"{i_c}:{i_n}")

        # Выбирается еще не обработанный набор данных
        cursor.execute(f"SELECT tick, SQRT(x*x+y*y+z*z) FROM vAcc WHERE sid={sid} ORDER BY tick DESC LIMIT {abs(i_n - i_c)};")
        dat = np.array([data for data in cursor][::-1]).T
        dat = pd.Series(dat[1], index=[int(i) for i in dat[0]], name='a')

        if dat.any():
            # Анализ "хвоста данных"
            csc = get_csc(dat)
            if csc:
                # Дополнительная защита отт разрывов
                if csc[-1][1] + 10 > t_n:
                    csc.remove(csc[-1])

            # Перезапись каскадов
            if csc:
                # Если каскад не заканчивается в самом конце тренда
                if csc[-1][1] == i_n:
                    csc = csc[:-1]
                if len(csc) > 0:
                    for c in csc:
                        # TODO: Надо менять в БД. подумать как лучше
                        i_0, i_n = list(dat.index.values).index(c[0]), list(dat.index.values).index(c[1])
                        cursor.execute(f"INSERT INTO Cscds (sid, t0, tn) Values ({sid},{i_0},{i_n})")
                        cursor.execute(f"SELECT LAST_INSERT_ID();")
                        cid = cursor.fetchall()[0][0]
                        print(f"cscd:{cid}")
                        conn.commit()

                        # Достаем для каскада данные по акселерометру
                        cursor.execute(
                            f"SELECT tick, SQRT(x*x+y*y+z*z) FROM vAcc WHERE sid={sid} AND tick>={c[0]} AND tick<={c[1]}")
                        data = pd.DataFrame(cursor.fetchall(), columns=['t', 'a'])
                        data.index = data['t']
                        data = data.drop(['t'], axis=1)

                        result = get_jmp(data)
                        for jump in result:
                            strt,stop,jump = jump
                            cursor.execute(f"INSERT INTO Jmps (cid, strt,stop) VALUE ({cid},{strt},{stop})")
                            cursor.execute(f"SELECT LAST_INSERT_ID();")
                            jid = cursor.fetchall()[0][0]
                            to_insert = []
                            for i in jump.index:
                                val = jump.loc[i].values
                                a = val[0]
                                g = val[1] if len(val) == 2 else 0
                                to_insert.append((jid, i, a,g))
                            print(to_insert)
                            to_insert = str(to_insert)[1:-1]
                            cursor.execute(f"INSERT INTO vJmps (jid, tick, a,g) VALUES {to_insert}")
                conn.commit()
        time.sleep(1)