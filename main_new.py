from flask import Flask, render_template, json
import numpy as np
from batabase import Navka_db

app = Flask(__name__, static_url_path='')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


@app.route('/ssn/<ssi>/jmp/<jnum>')
def main_page(ssi, jnum):
    """
    Запускает рендер основной страницы
    :param ssi: id сессии
    :param jnum: id выбранного прыжка
    :return:
    """
    db = Navka_db()
    jmps = db.get_jumps_in_session(ssi)
    jmps = [(i[2] - i[3]) / 1000.0 for i in jmps]
    return render_template('index.html', ssi=ssi, id=jnum, jmps=jmps)


@app.route('/jump/<ssi>.<jnum>', methods=['GET'])
def jump(ssi, jnum):
    """
    :param sid: id сессии
    :param jid: номер прыжка в сессии
    :return:
    Вызов возвращает все данные по конкретному прыжку номер n_jmp в сессии id_ss
        return: {
        "t":  [ массив int отсечек по времени ],
        "a":  [ массив float значений ускорения в единицах 9.78 м2/с ],
        "g":  [ массив float оборот/сек. ],
        "rc": float значение количества оборотов за прыжок
        "br": tuple(начало прыжка, окончание прыжка) - время, если в a есть экстра периоды до и после.}
    """
    db = Navka_db()
    # Определяем id n-ного прыжка (n_jmp) в сессии id_ss.
    jmps = db.get_jumps_in_session(ssi)
    id_jmp = jmps[int(jnum)][0]

    # Достаем тренды по прыжку n_jmp
    trend = db.get_trend_by_jmps_id(id_jmp)
    trend = np.array([[d.tick, d.a, d.g] for d in trend]).T

    # Подготовка данных для отправки на фронт
    result = {"t": [], "a": [], "g": []}
    if trend.any():
        for i, k in enumerate(result.keys()):
            result[k] = list(trend[i])

        # Расчет суммарного числа оборотов Σg[i](t[i] - t[i-1]) * 0.001 где i (1..n)
        result['rc'] = round(trend[2][1:].dot((trend[0][1:]-trend[0][:-1])) * 0.001, 3)

        # В случае если в vJmps записаны дополнительные участки - достаем границы начала и конца прыжка.
        b = db.get_jmp_strt_stop(id_jmp)[0]
        result['br'] = [b[2], b[3]]
    else:
        result.update({'br': -1, 'rc': 0})

    return json.dumps(result)


@app.route('/trend/<sid>', methods=['GET', 'POST'])
def main_trend(sid):
    """
    :param sid: id сессии
    :return :
    Вызов возвращает все данные для заданной сессии прыжков
        return: {
            "raw":  [ xy - весь тренд данных ],
            "labels":  [ лэйблы данных ],
            "cascades":  [ массив xy каскадов для выделения на графике ],
            "jmp_points": [ точки отображающие прыжки ] }
    """
    db = Navka_db()
    responce = {'raw': {'x': [], 'y': []}, 'labels': []}

    d = db.get_trend_by_session_id(sid)
    d = np.array(d).T

    tick = [int(i) for i in d[2]]
    a = (d[3]**2+d[4]**2+d[5]**2)**0.5

    try:
        responce['raw'] = {'x': tick, 'y': list(a)}
        responce['labels'] = list(range(tick[0], tick[-1] + 1))
    except IndexError:
        pass

    # Jumps cascades only
    cid, cx, cy = [], [0], [0]
    casc = db.get_cscds_by_session_id(sid)
    if len(responce['raw']['x']) != 0:
        # TODO: Подумать над более элегантным методом отрисовки тренда каскадов
        for i, _, t0, tn in casc:
            cid.append(i)
            # Формирование тренда
            cx.append(responce['raw']['x'][t0])
            cy.append(0)

            cx.extend(responce['raw']['x'][t0:tn + 1])
            cy.extend(responce['raw']['y'][t0:tn + 1])

            cx.append(responce['raw']['x'][tn])
            cy.append(0)

        cx.append(responce['raw']['x'][-1])
        cy.append(0)

    # Следующую строка выключает отрисовку тренда, для более быстрой отладки
    # responce['raw'] = {'x': [], 'y': []}

    responce['cascades'] = {'x': cx, 'y': cy}

    # Jumps
    jx, jy = [], []
    responce['jmp_points'] = {'x': [], 'y': []}
    """
    Доработать в следующей итерации (отображение точек на графике)
    На фронте функционал заложен.
    for i in cid:
        for j in db.get_jmp_ids_by_cscd(i):
            jmp = db.get_jmp_by_id(j[0])
            responce['jmp_points']['x'].append(jmp[0][2])
            responce['jmp_points']['x'].append(jmp[0][3])
    """
    return json.dumps(responce)


if __name__ == '__main__':
    app.run(debug=True)



