"""Pruebas de reloj.py en Python puro, sin ninguna importacion.

reloj.py se carga con open() + exec() en un diccionario propio. Como ese
diccionario tiene __name__ = "reloj", el menu del reloj no arranca.

Uso: python pruebas.py
"""


# ======================================================================
# Carga de reloj.py sin importarlo
# ======================================================================
def ruta_de_reloj():
    """Ruta de reloj.py en la misma carpeta que este archivo."""
    ruta = __file__
    corte = max(ruta.rfind("/"), ruta.rfind("\\"))
    if corte == -1:
        return "reloj.py"
    return ruta[:corte + 1] + "reloj.py"


espacio = {"__name__": "reloj"}
with open(ruta_de_reloj(), encoding="utf-8") as archivo:
    exec(archivo.read(), espacio)

CircularDoublyLinkedList = espacio["CircularDoublyLinkedList"]
RingCursor = espacio["RingCursor"]
LinkedQueue = espacio["LinkedQueue"]
sin = espacio["sin"]
cos = espacio["cos"]
PI = espacio["PI"]
Clock = espacio["Clock"]
render_dial = espacio["render_dial"]
DIAL_RADIUS = espacio["DIAL_RADIUS"]
AlarmManager = espacio["AlarmManager"]
Stopwatch = espacio["Stopwatch"]
CountdownTimer = espacio["CountdownTimer"]
WorldClock = espacio["WorldClock"]
parse_time = espacio["parse_time"]
parse_duration = espacio["parse_duration"]
App = espacio["App"]
SECONDS_PER_DAY = espacio["SECONDS_PER_DAY"]


# ======================================================================
# Ayudas
# ======================================================================
def lanza(error, funcion, *argumentos):
    """True si llamar a funcion(*argumentos) lanza la excepcion ``error``."""
    try:
        funcion(*argumentos)
    except error:
        return True
    return False


def cerca(a, b, tolerancia=1e-9):
    return abs(a - b) <= tolerancia


def vaciar(cola):
    salida = []
    while not cola.is_empty():
        salida.append(cola.dequeue())
    return salida


def app_silenciosa():
    """App cuyas notificaciones se quedan en la cola en vez de imprimirse."""
    app = App()
    app.show_notifications = lambda: None
    return app


# Las funciones de reloj.py buscan print primero en su propio espacio de
# nombres, asi que esto calla la salida de App.advance durante las pruebas.
espacio["print"] = lambda *args, **kwargs: None


# ======================================================================
# CircularDoublyLinkedList
# ======================================================================
def prueba_lista_append_conserva_orden():
    lista = CircularDoublyLinkedList()
    for valor in (1, 2, 3):
        lista.append(valor)
    assert list(lista) == [1, 2, 3], list(lista)
    assert len(lista) == 3


def prueba_lista_prepend_pone_al_frente():
    lista = CircularDoublyLinkedList([2, 3])
    lista.prepend(1)
    assert list(lista) == [1, 2, 3], list(lista)
    assert lista.head.value == 1
    assert len(lista) == 3


def prueba_lista_prepend_en_vacia():
    lista = CircularDoublyLinkedList()
    lista.prepend(7)
    assert list(lista) == [7]
    assert lista.head.next is lista.head and lista.head.prev is lista.head


def prueba_lista_insert_sorted_ordena():
    lista = CircularDoublyLinkedList()
    for valor in (5, 1, 4, 2, 3, 0, 6):
        lista.insert_sorted(valor, lambda v: v)
    assert list(lista) == [0, 1, 2, 3, 4, 5, 6], list(lista)


def prueba_lista_insert_sorted_es_estable():
    lista = CircularDoublyLinkedList()
    for par in ((2, "a"), (1, "b"), (2, "c"), (1, "d")):
        lista.insert_sorted(par, lambda p: p[0])
    assert [p[1] for p in lista] == ["b", "d", "a", "c"], list(lista)


def prueba_lista_remove_node_medio_cabeza_y_ultimo():
    lista = CircularDoublyLinkedList([1, 2, 3, 4])
    assert lista.remove_node(lista.node_at(1)) == 2
    assert list(lista) == [1, 3, 4]
    assert lista.remove_node(lista.head) == 1
    assert list(lista) == [3, 4] and lista.head.value == 3
    assert lista.remove_node(lista.node_at(-1)) == 4
    assert list(lista) == [3]
    assert lista.remove_node(lista.head) == 3
    assert lista.is_empty() and lista.head is None and len(lista) == 0


def prueba_lista_remove_node_mantiene_circularidad():
    lista = CircularDoublyLinkedList([1, 2, 3])
    lista.remove_node(lista.node_at(2))
    assert lista.head.prev.value == 2
    assert lista.head.prev.next is lista.head


def prueba_lista_node_at_positivo():
    lista = CircularDoublyLinkedList(range(10))
    for i in range(10):
        assert lista.node_at(i).value == i, i


def prueba_lista_node_at_negativo():
    lista = CircularDoublyLinkedList(range(10))
    assert lista.node_at(-1).value == 9
    assert lista.node_at(-3).value == 7
    assert lista.node_at(-10).value == 0
    assert lista.node_at(-11).value == 9


def prueba_lista_node_at_da_la_vuelta():
    lista = CircularDoublyLinkedList(range(5))
    assert lista.node_at(5).value == 0
    assert lista.node_at(7).value == 2
    assert lista.node_at(23).value == 3


def prueba_lista_circularidad_next_prev():
    lista = CircularDoublyLinkedList([1, 2, 3])
    cabeza = lista.head
    assert cabeza.prev.value == 3
    assert cabeza.prev.next is cabeza
    assert cabeza.next.next.next is cabeza
    assert cabeza.prev.prev.prev is cabeza
    for nodo in lista.nodes():
        assert nodo.next.prev is nodo and nodo.prev.next is nodo


def prueba_lista_vacia_lanza_index_error():
    lista = CircularDoublyLinkedList()
    assert lanza(IndexError, lista.node_at, 0)
    assert lanza(IndexError, lista.pop_front)
    assert lanza(IndexError, lista.remove_node, None)


# ======================================================================
# RingCursor
# ======================================================================
def prueba_cursor_forward_da_la_vuelta():
    cursor = RingCursor(CircularDoublyLinkedList(range(5)))
    assert cursor.value == 0
    assert cursor.forward() == 1
    assert cursor.forward(3) == 4
    assert cursor.forward() == 0
    assert cursor.forward(12) == 2


def prueba_cursor_backward_da_la_vuelta():
    cursor = RingCursor(CircularDoublyLinkedList(range(5)))
    assert cursor.backward() == 4
    assert cursor.backward(4) == 0
    assert cursor.backward(7) == 3


def prueba_cursor_seek_adelante():
    cursor = RingCursor(CircularDoublyLinkedList(range(60)))
    assert cursor.seek(lambda v: v == 10)
    assert cursor.value == 10


def prueba_cursor_seek_atras():
    cursor = RingCursor(CircularDoublyLinkedList(range(60)))
    assert cursor.seek(lambda v: v == 55)
    assert cursor.value == 55
    assert cursor.seek(lambda v: v == 50)
    assert cursor.value == 50


def prueba_cursor_seek_todos_los_valores():
    for tamano in (1, 2, 3, 4, 7, 24):
        for objetivo in range(tamano):
            cursor = RingCursor(CircularDoublyLinkedList(range(tamano)))
            cursor.forward(tamano // 2)
            assert cursor.seek(lambda v: v == objetivo), (tamano, objetivo)
            assert cursor.value == objetivo, (tamano, objetivo)


def prueba_cursor_seek_no_encontrado():
    cursor = RingCursor(CircularDoublyLinkedList(range(5)))
    cursor.forward(2)
    assert cursor.seek(lambda v: v == 99) is False
    assert cursor.value == 2


def prueba_cursor_en_lista_vacia():
    cursor = RingCursor(CircularDoublyLinkedList())
    assert cursor.seek(lambda v: True) is False
    assert lanza(IndexError, cursor.forward)
    assert lanza(IndexError, cursor.backward)
    assert lanza(IndexError, lambda: cursor.value)


# ======================================================================
# LinkedQueue
# ======================================================================
def prueba_cola_fifo():
    cola = LinkedQueue()
    assert cola.is_empty() and len(cola) == 0
    for valor in ("a", "b", "c"):
        cola.enqueue(valor)
    assert len(cola) == 3
    assert cola.dequeue() == "a"
    cola.enqueue("d")
    assert vaciar(cola) == ["b", "c", "d"]
    assert cola.is_empty()


def prueba_cola_vacia_lanza_index_error():
    cola = LinkedQueue()
    assert lanza(IndexError, cola.dequeue)
    cola.enqueue(1)
    cola.dequeue()
    assert lanza(IndexError, cola.dequeue)


# ======================================================================
# sin / cos
# ======================================================================
def prueba_sin_valores_conocidos():
    casos = (
        (0, 0.0), (PI / 6, 0.5), (PI / 4, 0.7071067811865476),
        (PI / 2, 1.0), (PI, 0.0), (3 * PI / 2, -1.0), (2 * PI, 0.0),
        (-PI / 2, -1.0), (-PI / 6, -0.5), (1.0, 0.8414709848078965),
        (100.0, -0.5063656411097588), (-7.0, -0.6569865987187891),
    )
    for x, esperado in casos:
        assert cerca(sin(x), esperado), (x, sin(x), esperado)


def prueba_cos_valores_conocidos():
    casos = (
        (0, 1.0), (PI / 3, 0.5), (PI / 2, 0.0), (PI, -1.0),
        (3 * PI / 2, 0.0), (2 * PI, 1.0), (-PI, -1.0),
        (1.0, 0.5403023058681398), (100.0, 0.8623188722876839),
    )
    for x, esperado in casos:
        assert cerca(cos(x), esperado), (x, cos(x), esperado)


def prueba_sin_cuadrado_mas_cos_cuadrado():
    x = -10.0
    while x <= 10.0:
        assert cerca(sin(x) ** 2 + cos(x) ** 2, 1.0), x
        x += 0.37


# ======================================================================
# Clock
# ======================================================================
def prueba_reloj_empieza_en_cero():
    reloj = Clock()
    assert reloj.text() == "00:00:00"
    assert reloj.days == 0


def prueba_reloj_set():
    reloj = Clock()
    reloj.set(13, 45, 30)
    assert (reloj.hour, reloj.minute, reloj.second) == (13, 45, 30)
    assert reloj.text() == "13:45:30"
    assert reloj.seconds_of_day() == 13 * 3600 + 45 * 60 + 30
    reloj.set(2, 5)
    assert reloj.text() == "02:05:00"
    reloj.set(23, 59, 59)
    assert reloj.text() == "23:59:59"


def prueba_reloj_tick_simple():
    reloj = Clock()
    reloj.set(10, 0, 0)
    assert reloj.tick() is False
    assert reloj.text() == "10:00:01"


def prueba_reloj_tick_59_a_0():
    reloj = Clock()
    reloj.set(10, 20, 59)
    assert reloj.tick() is True
    assert reloj.text() == "10:21:00"
    reloj.set(10, 59, 59)
    assert reloj.tick() is True
    assert reloj.text() == "11:00:00"
    assert reloj.days == 0


def prueba_reloj_medianoche_suma_dia():
    reloj = Clock()
    reloj.set(23, 59, 59)
    assert reloj.tick() is True
    assert reloj.text() == "00:00:00"
    assert reloj.days == 1


def prueba_reloj_varios_dias():
    reloj = Clock()
    reloj.set(12, 0, 0)
    for _ in range(2 * SECONDS_PER_DAY + 30):
        reloj.tick()
    assert reloj.text() == "12:00:30"
    assert reloj.days == 2


# ======================================================================
# render_dial
# ======================================================================
def prueba_esfera_dimensiones():
    filas = render_dial(3, 15, 45).split("\n")
    r = DIAL_RADIUS
    assert len(filas) == 2 * r + 1, len(filas)
    for fila in filas:
        assert len(fila) <= 4 * r + 1, fila
    assert max(len(fila) for fila in filas) == 4 * r + 1


def prueba_esfera_centro_es_o():
    r = DIAL_RADIUS
    for hora, minuto, segundo in ((0, 0, 0), (3, 15, 45), (12, 30, 0), (23, 59, 59)):
        filas = render_dial(hora, minuto, segundo).split("\n")
        assert filas[r][2 * r] == "O", (hora, minuto, segundo)


def prueba_esfera_marcas_y_numeros():
    r = DIAL_RADIUS
    # Hora elegida para que ninguna manecilla tape un numero.
    texto = render_dial(2, 10, 22)
    filas = texto.split("\n")
    assert filas[0][2 * r] == "+"
    assert filas[2 * r][2 * r] == "+"
    assert filas[r][0] == "+"
    assert filas[r][4 * r] == "+"
    for numero in range(1, 13):
        assert str(numero) in texto, numero


def prueba_esfera_segundero_apunta_bien():
    r = DIAL_RADIUS
    filas = render_dial(6, 30, 15).split("\n")
    assert ":" in filas[r][2 * r + 1:], filas[r]
    filas = render_dial(6, 15, 45).split("\n")
    assert ":" in filas[r][:2 * r], filas[r]


# ======================================================================
# AlarmManager
# ======================================================================
def prueba_alarmas_ordenadas_por_hora():
    gestor = AlarmManager()
    gestor.add(9, 0, "c")
    gestor.add(7, 30, "a")
    gestor.add(12, 0, "d")
    gestor.add(7, 45, "b")
    assert [a.label for a in gestor.alarms] == ["a", "b", "c", "d"]


def prueba_alarmas_ringing():
    gestor = AlarmManager()
    gestor.add(7, 0, "uno")
    gestor.add(7, 0, "dos")
    gestor.add(8, 0, "tres")
    assert [a.label for a in gestor.ringing(7, 0)] == ["uno", "dos"]
    assert list(gestor.ringing(7, 1)) == []


def prueba_alarmas_toggle():
    gestor = AlarmManager()
    gestor.add(7, 0, "uno")
    gestor.add(8, 0, "dos")
    alarma = gestor.toggle(0)
    assert alarma.label == "uno" and alarma.active is False
    assert list(gestor.ringing(7, 0)) == []
    gestor.toggle(0)
    assert [a.label for a in gestor.ringing(7, 0)] == ["uno"]
    assert gestor.toggle(-1).label == "dos"


def prueba_alarmas_remove():
    gestor = AlarmManager()
    gestor.add(7, 0, "uno")
    gestor.add(8, 0, "dos")
    gestor.add(9, 0, "tres")
    assert gestor.remove(1).label == "dos"
    assert [a.label for a in gestor.alarms] == ["uno", "tres"]


def prueba_alarmas_next_after():
    gestor = AlarmManager()
    assert gestor.next_after(0) == (None, None)
    gestor.add(7, 0, "manana")
    gestor.add(22, 0, "noche")
    alarma, espera = gestor.next_after(6 * 3600)
    assert alarma.label == "manana" and espera == 3600
    alarma, espera = gestor.next_after(23 * 3600)
    assert alarma.label == "manana" and espera == 8 * 3600
    alarma, espera = gestor.next_after(10 * 3600 + 30)
    assert alarma.label == "noche" and espera == 12 * 3600 - 30


def prueba_alarmas_next_after_ignora_inactivas():
    gestor = AlarmManager()
    gestor.add(7, 0, "manana")
    gestor.add(22, 0, "noche")
    gestor.toggle(0)
    alarma, espera = gestor.next_after(6 * 3600)
    assert alarma.label == "noche" and espera == 16 * 3600
    gestor.toggle(1)
    assert gestor.next_after(6 * 3600) == (None, None)


def prueba_alarmas_next_after_justo_en_la_hora():
    gestor = AlarmManager()
    gestor.add(7, 0, "manana")
    alarma, espera = gestor.next_after(7 * 3600)
    assert alarma.label == "manana" and espera == SECONDS_PER_DAY


# ======================================================================
# Stopwatch
# ======================================================================
def prueba_cronometro_vueltas():
    cronometro = Stopwatch()
    cronometro.tick()
    assert cronometro.elapsed == 0
    cronometro.running = True
    for _ in range(5):
        cronometro.tick()
    cronometro.lap()
    for _ in range(3):
        cronometro.tick()
    cronometro.lap()
    for _ in range(7):
        cronometro.tick()
    cronometro.lap()
    assert list(cronometro.laps) == [5, 3, 7]
    assert cronometro.elapsed == 15


def prueba_cronometro_pausa_y_reset():
    cronometro = Stopwatch()
    cronometro.running = True
    cronometro.tick()
    cronometro.tick()
    cronometro.running = False
    cronometro.tick()
    assert cronometro.elapsed == 2
    cronometro.lap()
    cronometro.reset()
    assert cronometro.elapsed == 0 and cronometro.running is False
    assert cronometro.laps.is_empty()
    cronometro.running = True
    cronometro.tick()
    cronometro.lap()
    assert list(cronometro.laps) == [1]


# ======================================================================
# CountdownTimer
# ======================================================================
def prueba_temporizador_termina_una_sola_vez():
    temporizador = CountdownTimer()
    temporizador.start(3)
    assert temporizador.running
    resultados = [temporizador.tick() for _ in range(10)]
    assert resultados == [False, False, True] + [False] * 7, resultados
    assert temporizador.remaining == 0
    assert temporizador.running is False


def prueba_temporizador_en_cero_no_arranca():
    temporizador = CountdownTimer()
    temporizador.start(0)
    assert temporizador.running is False
    assert temporizador.tick() is False
    assert temporizador.remaining == 0


def prueba_temporizador_pausado_no_avanza():
    temporizador = CountdownTimer()
    temporizador.start(5)
    temporizador.tick()
    temporizador.running = False
    temporizador.tick()
    assert temporizador.remaining == 4


# ======================================================================
# WorldClock
# ======================================================================
def prueba_mundial_misma_zona():
    mundo = WorldClock()
    assert mundo.time_in(-5 * 60, 10 * 3600) == (10 * 3600, 0)


def prueba_mundial_media_hora():
    mundo = WorldClock()
    # Bogota 08:00 -> Nueva Delhi 18:30 (diferencia de 10 h 30 min).
    assert mundo.time_in(5 * 60 + 30, 8 * 3600) == (18 * 3600 + 30 * 60, 0)


def prueba_mundial_dia_siguiente():
    mundo = WorldClock()
    # Bogota 20:00 -> Tokio 10:00 del dia siguiente.
    assert mundo.time_in(9 * 60, 20 * 3600) == (10 * 3600, 1)
    # Bogota 15:00 -> Nueva Delhi 01:30 del dia siguiente.
    assert mundo.time_in(5 * 60 + 30, 15 * 3600) == (1 * 3600 + 30 * 60, 1)


def prueba_mundial_dia_anterior():
    mundo = WorldClock()
    mundo.local_offset = 9 * 60
    # Tokio 05:00 -> Bogota 15:00 del dia anterior.
    assert mundo.time_in(-5 * 60, 5 * 3600) == (15 * 3600, -1)
    mundo.local_offset = 5 * 60 + 30
    # Nueva Delhi 03:00 -> Londres 21:30 del dia anterior.
    assert mundo.time_in(0, 3 * 3600) == (21 * 3600 + 30 * 60, -1)


def prueba_mundial_cursor_recorre_ciudades():
    mundo = WorldClock()
    assert mundo.cursor.value[0] == "Bogota"
    mundo.cursor.backward()
    assert mundo.cursor.value[0] == "Sidney"
    mundo.cursor.forward(2)
    assert mundo.cursor.value[0] == "Ciudad de Mexico"


# ======================================================================
# parse_time / parse_duration
# ======================================================================
def prueba_parse_time_validos():
    assert parse_time("7:30") == (7, 30, 0)
    assert parse_time("07:30:15") == (7, 30, 15)
    assert parse_time("0:0") == (0, 0, 0)
    assert parse_time("23:59:59") == (23, 59, 59)


def prueba_parse_time_invalidos():
    for texto in ("", "7", "24:00", "12:60", "12:00:60", "-1:00", "a:b",
                  "7:30:", "1:2:3:4", "12.30", "7:-5"):
        assert parse_time(texto) is None, texto


def prueba_parse_duration_validos():
    casos = (
        ("90", 90), ("90s", 90), ("5m", 300), ("2h", 7200), ("2H", 7200),
        ("1:30:00", 5400), ("1:30", 90), ("0", 0), (" 5 m ", 300),
        ("0:00:01", 1),
    )
    for texto, esperado in casos:
        assert parse_duration(texto) == esperado, (texto, parse_duration(texto))


def prueba_parse_duration_invalidos():
    for texto in ("", "abc", "-5", "-5m", "5x", "h", "1:2:3:4", "1::", ":",
                  "1:30:xx", "-1:30"):
        assert parse_duration(texto) is None, (texto, parse_duration(texto))


def prueba_parse_duration_rechaza_partes_negativas():
    # "2:-30" no es una duracion valida; no deberia interpretarse como 90 s.
    for texto in ("2:-30", "1:-1:00", "0:-5"):
        assert parse_duration(texto) is None, (texto, parse_duration(texto))


# ======================================================================
# App.advance
# ======================================================================
def prueba_app_advance_mueve_reloj_y_cronometro():
    app = app_silenciosa()
    app.clock.set(10, 0, 0)
    app.stopwatch.running = True
    app.advance(125)
    assert app.clock.text() == "10:02:05"
    assert app.stopwatch.elapsed == 125
    assert app.notifications.is_empty()


def prueba_app_advance_alarma_en_cola():
    app = app_silenciosa()
    app.clock.set(6, 59, 30)
    app.alarms.add(7, 0, "Despertar")
    app.alarms.add(7, 1, "Apagada")
    app.alarms.toggle(1)
    app.advance(120)
    assert vaciar(app.notifications) == ["ALARMA 07:00  Despertar"]


def prueba_app_advance_alarma_a_medianoche():
    app = app_silenciosa()
    app.clock.set(23, 59, 50)
    app.alarms.add(0, 0, "Medianoche")
    app.advance(10)
    assert vaciar(app.notifications) == ["ALARMA 00:00  Medianoche"]
    assert app.clock.days == 1


def prueba_app_advance_temporizador_en_cola():
    app = app_silenciosa()
    app.clock.set(8, 0, 0)
    app.timer.start(90)
    app.advance(200)
    assert vaciar(app.notifications) == [
        "TEMPORIZADOR: el tiempo termino a las 08:01:30"
    ]
    assert app.timer.running is False


def prueba_app_advance_orden_fifo():
    app = app_silenciosa()
    app.clock.set(8, 0, 0)
    app.timer.start(30)
    app.alarms.add(8, 1, "Reunion")
    app.alarms.add(8, 2, "Cafe")
    app.advance(180)
    assert vaciar(app.notifications) == [
        "TEMPORIZADOR: el tiempo termino a las 08:00:30",
        "ALARMA 08:01  Reunion",
        "ALARMA 08:02  Cafe",
    ]


def prueba_app_advance_sin_silenciar_vacia_la_cola():
    app = App()
    app.clock.set(6, 59, 59)
    app.alarms.add(7, 0, "x")
    app.advance(1)
    assert app.notifications.is_empty()


# ======================================================================
# Corredor
# ======================================================================
def correr():
    pruebas = [(nombre, funcion) for nombre, funcion in globals().items()
               if nombre.startswith("prueba_") and callable(funcion)]
    fallas = 0
    for nombre, funcion in pruebas:
        try:
            funcion()
        except AssertionError as error:
            fallas += 1
            detalle = str(error)
            print("FALLA " + nombre + (": " + detalle if detalle else ""))
        except Exception as error:
            fallas += 1
            print("FALLA " + nombre + ": " + type(error).__name__ + ": " + str(error))
        else:
            print("OK    " + nombre)
    print()
    print(str(len(pruebas)) + " pruebas, " + str(fallas) + " fallas")
    return fallas


if __name__ == "__main__":
    if correr():
        raise SystemExit(1)
