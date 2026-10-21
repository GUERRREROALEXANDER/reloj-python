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
DISPLAY = espacio["DISPLAY"]
PixelCanvas = espacio["PixelCanvas"]
render_face = espacio["render_face"]
render_big_time = espacio["render_big_time"]
render_big_time_ascii = espacio["render_big_time_ascii"]
draw_face = espacio["draw_face"]
strip_ansi = espacio["strip_ansi"]
visible_len = espacio["visible_len"]
pad = espacio["pad"]
to_ascii = espacio["to_ascii"]
paint = espacio["paint"]
show = espacio["show"]
parse_decimal = espacio["parse_decimal"]
wait_one_second = espacio["wait_one_second"]
LOOPS_PER_SECOND = espacio["LOOPS_PER_SECOND"]
FACE_SIZE = espacio["FACE_SIZE"]
C_HOUR_HAND = espacio["C_HOUR_HAND"]
C_MINUTE_HAND = espacio["C_MINUTE_HAND"]
C_BEZEL_ALERT = espacio["C_BEZEL_ALERT"]


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
# Ayudas para la parte visual
# ======================================================================
def guardar_display():
    return (DISPLAY.color, DISPLAY.ansi, DISPLAY.unicode, DISPLAY.loops_per_second)


def restaurar_display(estado):
    DISPLAY.color, DISPLAY.ansi, DISPLAY.unicode, DISPLAY.loops_per_second = estado


def celdas_de_color(linea):
    """Convierte una linea con codigos ANSI en celdas (letra, color, fondo)."""
    celdas = []
    letra_color = fondo = None
    i = 0
    while i < len(linea):
        if linea[i] == "\x1b":
            fin = linea.index("m", i)
            partes = linea[i + 2:fin].split(";")
            j = 0
            while j < len(partes):
                if partes[j] == "0":
                    letra_color = fondo = None
                elif partes[j] == "38":
                    letra_color = int(partes[j + 2])
                    j += 2
                elif partes[j] == "48":
                    fondo = int(partes[j + 2])
                    j += 2
                j += 1
            i = fin + 1
        else:
            celdas.append((linea[i], letra_color, fondo))
            i += 1
    return celdas


def mascara(texto, color):
    """Celdas (fila, columna) donde aparece ``color`` como letra o como fondo."""
    puntos = set()
    filas = texto.split("\n")
    for fila in range(len(filas)):
        celdas = celdas_de_color(filas[fila])
        for col in range(len(celdas)):
            if celdas[col][1] == color or celdas[col][2] == color:
                puntos.add((fila, col))
    return puntos


class Respuestas:
    """Reemplaza a ``ask`` de reloj.py con respuestas escritas de antemano."""

    def __init__(self, *respuestas):
        self.pendientes = list(respuestas)
        self.preguntas = []

    def __call__(self, pregunta):
        self.preguntas.append(pregunta)
        if not self.pendientes:
            raise AssertionError("se pidio una respuesta de mas: " + pregunta)
        return self.pendientes.pop(0)


def con_respuestas(respuestas, funcion):
    """Llama a ``funcion`` con ``ask`` reemplazado y luego lo deja como estaba."""
    original = espacio["ask"]
    espacio["ask"] = respuestas
    try:
        return funcion()
    finally:
        espacio["ask"] = original


# ======================================================================
# PixelCanvas
# ======================================================================
def prueba_lienzo_empieza_vacio():
    lienzo = PixelCanvas(4, 3)
    assert lienzo.width == 4 and lienzo.height == 3
    for y in range(3):
        for x in range(4):
            assert lienzo.get(x, y) is None, (x, y)


def prueba_lienzo_plot_y_get():
    lienzo = PixelCanvas(5, 5)
    lienzo.plot(0, 0, 1)
    lienzo.plot(4, 4, 2)
    lienzo.plot(2, 3, 3)
    assert lienzo.get(0, 0) == 1
    assert lienzo.get(4, 4) == 2
    assert lienzo.get(2, 3) == 3
    assert lienzo.get(3, 2) is None
    lienzo.plot(2, 3, 9)
    assert lienzo.get(2, 3) == 9


def prueba_lienzo_limites_se_ignoran():
    lienzo = PixelCanvas(3, 2)
    for x, y in ((-1, 0), (0, -1), (3, 0), (0, 2), (99, 99), (-5, -5)):
        lienzo.plot(x, y, 7)
        assert lienzo.get(x, y) is None, (x, y)
    # Un indice negativo no debe pintar el otro extremo de la fila.
    assert lienzo.pixels == [[None] * 3, [None] * 3], lienzo.pixels


def prueba_lienzo_linea_horizontal_vertical_diagonal():
    lienzo = PixelCanvas(10, 10)
    lienzo.line(1, 1, 6, 1, "h")
    assert [x for x in range(10) if lienzo.get(x, 1) == "h"] == [1, 2, 3, 4, 5, 6]
    lienzo.line(8, 7, 8, 2, "v")
    assert [y for y in range(10) if lienzo.get(8, y) == "v"] == [2, 3, 4, 5, 6, 7]
    lienzo.line(0, 9, 4, 5, "d")
    for i in range(5):
        assert lienzo.get(i, 9 - i) == "d", i


def prueba_lienzo_linea_pendiente_sin_huecos():
    lienzo = PixelCanvas(20, 20)
    lienzo.line(2, 3, 15, 9, 1)
    assert lienzo.get(2, 3) == 1 and lienzo.get(15, 9) == 1
    # Una linea mas ancha que alta pinta exactamente un pixel por columna.
    for x in range(2, 16):
        cuantos = sum(1 for y in range(20) if lienzo.get(x, y) == 1)
        assert cuantos == 1, (x, cuantos)


def prueba_lienzo_linea_fuera_del_lienzo_no_falla():
    lienzo = PixelCanvas(5, 5)
    lienzo.line(-3, 2, 8, 2, 1)
    assert [lienzo.get(x, 2) for x in range(5)] == [1] * 5


def prueba_lienzo_disco():
    lienzo = PixelCanvas(11, 11)
    lienzo.disc(5, 5, 3, 1)
    assert lienzo.get(5, 5) == 1
    assert lienzo.get(8, 5) == 1 and lienzo.get(2, 5) == 1
    assert lienzo.get(5, 8) == 1 and lienzo.get(5, 2) == 1
    assert lienzo.get(8, 8) is None
    assert lienzo.get(9, 5) is None


def prueba_lienzo_to_text_medios_bloques():
    lienzo = PixelCanvas(4, 2)
    lienzo.plot(0, 0, 1)         # solo arriba
    lienzo.plot(1, 1, 1)         # solo abajo
    lienzo.plot(2, 0, 1)
    lienzo.plot(2, 1, 1)         # las dos
    assert lienzo.to_text() == "▀▄█"


def prueba_lienzo_to_text_alto_impar():
    lienzo = PixelCanvas(2, 5)
    lienzo.plot(0, 4, 1)
    lineas = lienzo.to_text().split("\n")
    assert len(lineas) == 3, lineas
    assert lineas[2] == "▀", lineas


def prueba_lienzo_to_text_con_color():
    lienzo = PixelCanvas(3, 2)
    lienzo.plot(0, 0, 10)
    lienzo.plot(0, 1, 20)
    texto = lienzo.to_text(color=True)
    assert "\x1b[" in texto
    assert visible_len(texto) == 3, repr(texto)
    assert celdas_de_color(texto)[0] == ("▀", 10, 20), celdas_de_color(texto)


# ======================================================================
# render_face
# ======================================================================
def prueba_face_lineas_y_ancho_constantes():
    for hora, minuto, segundo in ((0, 0, 0), (3, 15, 45), (10, 8, 30), (23, 59, 59)):
        con_color = render_face(hora, minuto, segundo, color=True).split("\n")
        assert len(con_color) == (FACE_SIZE + 1) // 2, len(con_color)
        for linea in con_color:
            assert visible_len(linea) == FACE_SIZE, (hora, minuto, segundo, visible_len(linea))
        sin_color = render_face(hora, minuto, segundo).split("\n")
        assert len(sin_color) == (FACE_SIZE + 1) // 2, len(sin_color)
        assert max(len(linea) for linea in sin_color) == FACE_SIZE
        for linea in sin_color:
            assert len(linea) <= FACE_SIZE


def prueba_face_cambia_con_los_segundos():
    assert render_face(10, 8, 0) != render_face(10, 8, 30)
    assert render_face(10, 8, 0) != render_face(10, 8, 59)


def prueba_face_minutero_se_mueve_con_los_segundos():
    antes = mascara(render_face(10, 8, 0, color=True), C_MINUTE_HAND)
    despues = mascara(render_face(10, 8, 59, color=True), C_MINUTE_HAND)
    assert antes, "no se encontro el minutero"
    assert antes != despues


def prueba_face_horario_se_mueve_con_los_minutos():
    assert render_face(10, 0, 0) != render_face(10, 30, 0)
    antes = mascara(render_face(10, 0, 0, color=True), C_HOUR_HAND)
    despues = mascara(render_face(10, 30, 0, color=True), C_HOUR_HAND)
    assert antes, "no se encontro el horario"
    assert antes != despues


def prueba_face_mismo_instante_mismo_dibujo():
    assert render_face(7, 20, 15) == render_face(7, 20, 15)
    # 13:00 y 01:00 se ven igual en una esfera de 12 horas.
    assert render_face(13, 0, 0) == render_face(1, 0, 0)


def prueba_face_sin_color_no_tiene_ansi():
    texto = render_face(10, 8, 30, color=False)
    assert "\x1b" not in texto
    assert strip_ansi(texto) == texto


def prueba_face_con_color_tiene_ansi():
    texto = render_face(10, 8, 30, color=True)
    assert "\x1b[" in texto
    assert "38;5;" in texto


def prueba_face_tiene_los_doce_numeros():
    texto = strip_ansi(render_face(2, 10, 22, color=True))
    for numero in range(1, 13):
        assert str(numero) in texto, numero


def prueba_face_alerta_pinta_el_bisel():
    normal = render_face(10, 8, 30, color=True)
    alerta = render_face(10, 8, 30, color=True, alert=True)
    assert normal != alerta
    assert not mascara(normal, C_BEZEL_ALERT)
    assert mascara(alerta, C_BEZEL_ALERT)


def prueba_face_a_ascii_es_solo_ascii():
    texto = to_ascii(render_face(10, 8, 30))
    for letra in texto:
        assert letra < "\x80", repr(letra)


def prueba_draw_face_respeta_unicode():
    estado = guardar_display()
    try:
        DISPLAY.unicode = True
        DISPLAY.color = False
        assert draw_face(4, 5, 6) == render_face(4, 5, 6)
        DISPLAY.unicode = False
        assert draw_face(4, 5, 6) == render_dial(4, 5, 6)
    finally:
        restaurar_display(estado)


# ======================================================================
# render_big_time / render_big_time_ascii
# ======================================================================
def prueba_big_time_alto_y_ancho():
    estado = guardar_display()
    try:
        DISPLAY.unicode = True
        lineas = render_big_time("10:08:30", color=True).split("\n")
        assert len(lineas) == 5, len(lineas)
        # 6 digitos de 6 + 2 dos puntos de 2 + 7 espacios de 2 = 54 columnas.
        for linea in lineas:
            assert visible_len(linea) == 54, visible_len(linea)
        sin_color = render_big_time("10:08:30").split("\n")
        assert len(sin_color) == 5
        assert "\x1b" not in "\n".join(sin_color)
    finally:
        restaurar_display(estado)


def prueba_big_time_digitos_distintos():
    estado = guardar_display()
    try:
        DISPLAY.unicode = True
        dibujos = [render_big_time(str(d)) for d in range(10)]
        for i in range(10):
            assert len(dibujos[i].split("\n")) == 5, i
            for j in range(i + 1, 10):
                assert dibujos[i] != dibujos[j], (i, j)
    finally:
        restaurar_display(estado)


def prueba_big_time_ocho_enciende_todo():
    estado = guardar_display()
    try:
        DISPLAY.unicode = True
        ocho = render_big_time("8").split("\n")
        # Fila de arriba, del medio y de abajo: trazo completo de 6 pixeles.
        assert ocho[0] == "█" * 6, ocho
        assert ocho[4] == "█" * 6, ocho
        uno = render_big_time("1").split("\n")
        for linea in uno:
            assert linea.strip() == "██", uno
    finally:
        restaurar_display(estado)


def prueba_big_time_sin_unicode_usa_ascii():
    estado = guardar_display()
    try:
        DISPLAY.unicode = False
        assert render_big_time("12:34") == render_big_time_ascii("12:34")
    finally:
        restaurar_display(estado)


def prueba_big_time_ascii_alto_y_digitos():
    dibujos = [render_big_time_ascii(str(d)) for d in range(10)]
    for i in range(10):
        assert len(dibujos[i].split("\n")) == 3, i
        for letra in dibujos[i]:
            assert letra in " _|\n", (i, letra)
        for j in range(i + 1, 10):
            assert dibujos[i] != dibujos[j], (i, j)
    assert render_big_time_ascii("8") == " _\n|_|\n|_|"
    assert len(render_big_time_ascii("10:08:30").split("\n")) == 3


# ======================================================================
# strip_ansi / visible_len / pad / to_ascii / paint / show
# ======================================================================
def prueba_strip_ansi():
    assert strip_ansi("hola") == "hola"
    assert strip_ansi("") == ""
    assert strip_ansi("\x1b[1;38;5;220mHola\x1b[0m mundo") == "Hola mundo"
    assert strip_ansi("\x1b[2J\x1b[Hx\x1b[K") == "x"
    assert strip_ansi("\x1b[?25lA\x1b[?25h") == "A"
    assert strip_ansi("abc\x1b[") == "abc"
    assert strip_ansi("█\x1b[38;5;1m▀") == "█▀"


def prueba_visible_len():
    assert visible_len("") == 0
    assert visible_len("abc") == 3
    assert visible_len("\x1b[38;5;214mabc\x1b[0m") == 3
    assert visible_len("╔══╗") == 4


def prueba_pad():
    assert pad("ab", 5) == "ab   "
    assert pad("abcdef", 3) == "abcdef"
    coloreado = "\x1b[1mab\x1b[0m"
    assert pad(coloreado, 5) == coloreado + "   "
    assert visible_len(pad(coloreado, 5)) == 5


def prueba_to_ascii():
    assert to_ascii("hola 123") == "hola 123"
    assert to_ascii("█▀▄") == '#".'
    assert to_ascii("╔═╗║╚╝╟─╢│·") == "+=+|+++-+|-"
    assert to_ascii("ñ") == "?"
    assert to_ascii("\x1b[0m") == "\x1b[0m"


def prueba_paint_respeta_color():
    estado = guardar_display()
    try:
        DISPLAY.color = True
        assert paint("x", 1) == "\x1b[38;5;1mx\x1b[0m"
        assert paint("x", 1, 2, bold=True) == "\x1b[1;38;5;1;48;5;2mx\x1b[0m"
        assert paint("", 1) == ""
        DISPLAY.color = False
        assert paint("x", 1, 2, bold=True) == "x"
    finally:
        restaurar_display(estado)


def prueba_show_pasa_a_ascii_si_falla_unicode():
    estado = guardar_display()
    original = espacio["print"]
    impreso = []

    def print_cp1252(texto="", end="\n", flush=False):
        for letra in texto:
            if letra >= "\x80":
                raise UnicodeEncodeError("cp1252", texto, 0, 1, "prueba")
        impreso.append(texto + end)

    try:
        DISPLAY.unicode = True
        DISPLAY.color = True
        DISPLAY.ansi = True
        espacio["print"] = print_cp1252
        show("\x1b[1m█ hora\x1b[0m")
        assert impreso == ["# hora\n"], impreso
        assert DISPLAY.unicode is False and DISPLAY.color is False and DISPLAY.ansi is False
    finally:
        espacio["print"] = original
        restaurar_display(estado)


# ======================================================================
# App.step
# ======================================================================
def estado_app(app):
    return (app.clock.text(), app.clock.days, app.stopwatch.elapsed,
            app.timer.remaining, app.timer.running, vaciar(app.notifications))


def app_preparada(hora, minuto, segundo):
    app = app_silenciosa()
    app.clock.set(hora, minuto, segundo)
    app.stopwatch.running = True
    app.timer.start(1)
    app.alarms.add(7, 0, "Despertar")
    return app


def prueba_app_step_igual_que_advance_1():
    for hora, minuto, segundo in ((6, 59, 59), (10, 0, 0), (23, 59, 59), (6, 59, 58)):
        con_step = app_preparada(hora, minuto, segundo)
        con_advance = app_preparada(hora, minuto, segundo)
        con_step.step()
        con_advance.advance(1)
        assert estado_app(con_step) == estado_app(con_advance), (hora, minuto, segundo)


def prueba_app_step_avanza_todo():
    app = app_preparada(6, 59, 59)
    app.step()
    assert app.clock.text() == "07:00:00"
    assert app.stopwatch.elapsed == 1
    assert app.timer.remaining == 0 and app.timer.running is False
    assert vaciar(app.notifications) == [
        "TEMPORIZADOR: el tiempo termino a las 07:00:00",
        "ALARMA 07:00  Despertar",
    ]


def prueba_app_step_no_guarda_mensajes():
    app = app_silenciosa()
    app.step()
    assert app.messages == []
    assert app.clock.text() == "00:00:01"


def prueba_app_step_medianoche():
    app = app_silenciosa()
    app.clock.set(23, 59, 59)
    app.step()
    assert app.clock.text() == "00:00:00" and app.clock.days == 1


def prueba_app_clock_lines_cabe_en_la_consola():
    estado = guardar_display()
    try:
        for color in (True, False):
            DISPLAY.unicode = True
            DISPLAY.color = color
            app = app_silenciosa()
            app.clock.set(10, 8, 30)
            app.alarms.add(11, 0, "x")
            app.timer.start(60)
            app.stopwatch.running = True
            lineas = app.clock_lines("RELOJ", "Enter: menu", ["ALARMA 11:00  x"])
            assert len(lineas) <= 30, len(lineas)
            for linea in lineas:
                assert visible_len(linea) <= 80, visible_len(linea)
    finally:
        restaurar_display(estado)


# ======================================================================
# parse_decimal
# ======================================================================
def prueba_parse_decimal_validos():
    casos = (("12", 12.0), ("12.5", 12.5), ("12,5", 12.5), ("0.5", 0.5),
             ("10", 10.0), ("007", 7.0), ("99999999999", 99999999999.0))
    for texto, esperado in casos:
        assert parse_decimal(texto) == esperado, (texto, parse_decimal(texto))


def prueba_parse_decimal_invalidos():
    for texto in ("", "0", "0.0", "-5", "+5", "abc", "1.2.3", "1,2.3", ".5", "5.",
                  ".", "1e5", " 5", "5 ", "1_0", "1234567890123"):
        assert parse_decimal(texto) is None, (texto, parse_decimal(texto))


# ======================================================================
# Calibracion
# ======================================================================
def prueba_wait_one_second_con_pocas_vueltas():
    estado = guardar_display()
    try:
        DISPLAY.loops_per_second = 10
        assert wait_one_second() is None
        DISPLAY.loops_per_second = 0
        assert wait_one_second() is None
    finally:
        restaurar_display(estado)


def prueba_calibracion_valor_inicial():
    assert LOOPS_PER_SECOND > 0
    assert espacio["Display"]().loops_per_second == LOOPS_PER_SECOND


def prueba_calibracion_mas_alarga_el_segundo():
    estado = guardar_display()
    try:
        DISPLAY.loops_per_second = 100000
        con_respuestas(Respuestas("+", "0"), app_silenciosa().calibrate_menu)
        assert DISPLAY.loops_per_second == 105000, DISPLAY.loops_per_second
    finally:
        restaurar_display(estado)


def prueba_calibracion_menos_acorta_el_segundo():
    estado = guardar_display()
    try:
        DISPLAY.loops_per_second = 100000
        con_respuestas(Respuestas("-", "0"), app_silenciosa().calibrate_menu)
        assert DISPLAY.loops_per_second == 95000, DISPLAY.loops_per_second
        DISPLAY.loops_per_second = 1000
        con_respuestas(Respuestas("-", "0"), app_silenciosa().calibrate_menu)
        assert DISPLAY.loops_per_second == 1000, DISPLAY.loops_per_second
    finally:
        restaurar_display(estado)


def prueba_calibracion_escribir_valor():
    estado = guardar_display()
    try:
        DISPLAY.loops_per_second = 100000
        con_respuestas(Respuestas("e", "5000", "0"), app_silenciosa().calibrate_menu)
        assert DISPLAY.loops_per_second == 5000
        # Menos del minimo (1000) no se acepta y el valor no cambia.
        con_respuestas(Respuestas("e", "999", "0"), app_silenciosa().calibrate_menu)
        assert DISPLAY.loops_per_second == 5000
        con_respuestas(Respuestas("e", "abc", "0"), app_silenciosa().calibrate_menu)
        assert DISPLAY.loops_per_second == 5000
    finally:
        restaurar_display(estado)


def prueba_calibracion_programa_lento_baja_las_vueltas():
    # 10 segundos del programa duraron 20 reales: cada segundo es muy largo,
    # asi que hay que dar menos vueltas (la mitad).
    estado = guardar_display()
    try:
        DISPLAY.loops_per_second = 4000
        con_respuestas(Respuestas("", "20"), app_silenciosa().calibration_test)
        assert DISPLAY.loops_per_second == 2000, DISPLAY.loops_per_second
    finally:
        restaurar_display(estado)


def prueba_calibracion_programa_rapido_sube_las_vueltas():
    # 10 segundos del programa duraron 5 reales: hay que dar el doble de vueltas.
    estado = guardar_display()
    try:
        DISPLAY.loops_per_second = 2000
        con_respuestas(Respuestas("", "5"), app_silenciosa().calibration_test)
        assert DISPLAY.loops_per_second == 4000, DISPLAY.loops_per_second
        DISPLAY.loops_per_second = 2000
        con_respuestas(Respuestas("", "12,5"), app_silenciosa().calibration_test)
        assert DISPLAY.loops_per_second == 1600, DISPLAY.loops_per_second
    finally:
        restaurar_display(estado)


def prueba_calibracion_exacta_no_cambia():
    estado = guardar_display()
    try:
        DISPLAY.loops_per_second = 3000
        con_respuestas(Respuestas("", "10"), app_silenciosa().calibration_test)
        assert DISPLAY.loops_per_second == 3000
    finally:
        restaurar_display(estado)


def prueba_calibracion_respeta_el_minimo_y_entrada_invalida():
    estado = guardar_display()
    try:
        DISPLAY.loops_per_second = 1500
        con_respuestas(Respuestas("", "100"), app_silenciosa().calibration_test)
        assert DISPLAY.loops_per_second == 1000, DISPLAY.loops_per_second
        DISPLAY.loops_per_second = 2000
        app = app_silenciosa()
        con_respuestas(Respuestas("", "abc"), app.calibration_test)
        assert DISPLAY.loops_per_second == 2000
        assert ("Numero no valido; la velocidad no cambio.", False) in app.messages
    finally:
        restaurar_display(estado)


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
