"""Reloj de consola escrito en Python puro, sin importar ninguna libreria.

Python no trae ninguna funcion integrada para leer la hora del computador ni
para esperar un segundo (eso vive en los modulos ``time`` y ``datetime``), asi
que este reloj es simulado: la hora se ajusta a mano y el tiempo avanza con
comandos o en el modo en vivo, que espera cada segundo con un ciclo vacio
calibrable. Todo lo demas esta hecho aqui mismo: la lista circular doble, la
cola, el seno y el coseno, el lienzo de pixeles con medios bloques, las lineas
de Bresenham, los digitos de 7 segmentos y los colores ANSI (que son texto).

Uso: python reloj.py
"""

PI = 3.141592653589793
TWO_PI = 2 * PI
SECONDS_PER_DAY = 24 * 60 * 60
MAX_ADVANCE = 366 * SECONDS_PER_DAY


# ======================================================================
# Estructuras de datos
# ======================================================================
class Node:
    """Nodo que conoce a su vecino anterior y al siguiente."""

    def __init__(self, value):
        self.value = value
        self.next = self
        self.prev = self


class CircularDoublyLinkedList:
    """Lista doblemente enlazada circular.

    El ultimo nodo apunta al primero y el primero al ultimo, asi que recorrerla
    nunca llega a un final. Por eso pasar del segundo 59 al 0, o de la ultima
    ciudad a la primera, es solo seguir ``next``.
    """

    def __init__(self, items=()):
        self.head = None
        self.size = 0
        for item in items:
            self.append(item)

    def __len__(self):
        return self.size

    def is_empty(self):
        return self.size == 0

    def append(self, value):
        node = Node(value)
        if self.head is None:
            self.head = node
        else:
            self._link_after(self.head.prev, node)
        self.size += 1
        return node

    def prepend(self, value):
        node = self.append(value)
        self.head = node
        return node

    def insert_after(self, anchor, value):
        node = Node(value)
        self._link_after(anchor, node)
        self.size += 1
        return node

    def insert_sorted(self, value, key):
        """Inserta manteniendo la lista ordenada de menor a mayor por ``key``."""
        if self.head is None or key(value) < key(self.head.value):
            return self.prepend(value)
        current = self.head
        while current.next is not self.head and key(current.next.value) <= key(value):
            current = current.next
        return self.insert_after(current, value)

    def remove_node(self, node):
        if self.head is None:
            raise IndexError("la lista esta vacia")
        if self.size == 1:
            self.head = None
        else:
            node.prev.next = node.next
            node.next.prev = node.prev
            if node is self.head:
                self.head = node.next
        node.next = node.prev = node
        self.size -= 1
        return node.value

    def pop_front(self):
        if self.head is None:
            raise IndexError("la lista esta vacia")
        return self.remove_node(self.head)

    def node_at(self, index):
        """Nodo en la posicion ``index``; los indices dan la vuelta al circulo."""
        if self.head is None:
            raise IndexError("la lista esta vacia")
        index %= self.size
        node = self.head
        # Camina en la direccion mas corta.
        if index <= self.size // 2:
            for _ in range(index):
                node = node.next
        else:
            for _ in range(self.size - index):
                node = node.prev
        return node

    def clear(self):
        # Desengancha cada nodo para que ningun cursor siga caminando por
        # nodos que ya no pertenecen a la lista.
        node = self.head
        for _ in range(self.size):
            following = node.next
            node.next = node.prev = node
            node = following
        self.head = None
        self.size = 0

    def nodes(self):
        node = self.head
        for _ in range(self.size):
            yield node
            node = node.next

    def __iter__(self):
        for node in self.nodes():
            yield node.value

    @staticmethod
    def _link_after(anchor, node):
        node.prev = anchor
        node.next = anchor.next
        anchor.next.prev = node
        anchor.next = node


class RingCursor:
    """Puntero que se mueve sobre una lista circular, hacia adelante o atras."""

    def __init__(self, ring):
        self.ring = ring
        self.node = ring.head

    def _current(self):
        """Nodo actual, reenganchado a la cabeza si la lista cambio.

        Si el cursor se creo con la lista vacia, o su nodo fue borrado (un nodo
        borrado queda apuntandose a si mismo), vuelve a la cabeza de la lista.
        """
        if self.ring.head is None:
            self.node = None
            raise IndexError("la lista esta vacia")
        node = self.node
        if node is None or (node.next is node and node is not self.ring.head):
            self.node = self.ring.head
        return self.node

    @property
    def value(self):
        return self._current().value

    def forward(self, steps=1):
        node = self._current()
        if steps < 0:
            return self.backward(-steps)
        for _ in range(steps):
            node = node.next
        self.node = node
        return node.value

    def backward(self, steps=1):
        node = self._current()
        if steps < 0:
            return self.forward(-steps)
        for _ in range(steps):
            node = node.prev
        self.node = node
        return node.value

    def seek(self, predicate):
        """Mueve el cursor al nodo mas cercano que cumpla ``predicate``.

        Busca en las dos direcciones a la vez, asi que llega en a lo sumo
        ``len(ring) // 2`` pasos.
        """
        if self.ring.head is None:
            self.node = None
            return False
        self._current()
        if predicate(self.node.value):
            return True
        ahead, behind = self.node.next, self.node.prev
        for _ in range(len(self.ring) // 2 + 1):
            if predicate(ahead.value):
                self.node = ahead
                return True
            if predicate(behind.value):
                self.node = behind
                return True
            ahead, behind = ahead.next, behind.prev
        return False


class LinkedQueue:
    """Cola FIFO: entra por el final y sale por el frente, ambas en O(1)."""

    def __init__(self):
        self._items = CircularDoublyLinkedList()

    def enqueue(self, value):
        self._items.append(value)

    def dequeue(self):
        if self._items.is_empty():
            raise IndexError("la cola esta vacia")
        return self._items.pop_front()

    def is_empty(self):
        return self._items.is_empty()

    def __len__(self):
        return len(self._items)


# ======================================================================
# Matematica propia (reemplaza al modulo math)
# ======================================================================
def sin(x):
    """Seno por serie de Taylor, despues de llevar ``x`` al rango [-pi, pi]."""
    x %= TWO_PI
    if x > PI:
        x -= TWO_PI
    term = x
    total = x
    for n in range(1, 12):
        term *= -x * x / ((2 * n) * (2 * n + 1))
        total += term
    return total


def cos(x):
    return sin(x + PI / 2)


def two(n):
    """Numero con dos digitos: 7 -> '07'."""
    return str(n) if n >= 10 else "0" + str(n)


def format_seconds(total):
    """Segundos a texto hh:mm:ss (las horas pueden pasar de 24)."""
    return two(total // 3600) + ":" + two(total // 60 % 60) + ":" + two(total % 60)


def format_offset(minutes):
    sign = "+" if minutes >= 0 else "-"
    minutes = abs(minutes)
    text = "UTC" + sign + str(minutes // 60)
    if minutes % 60:
        text += ":" + two(minutes % 60)
    return text


# ======================================================================
# Reloj
# ======================================================================
class Clock:
    """Hora del dia guardada en tres anillos: 24 horas, 60 minutos, 60 segundos.

    Cada anillo es una lista circular y cada manecilla es un cursor sobre ella.
    Cuando el segundero da la vuelta y vuelve a 0, arrastra al minutero, y este
    al horario, igual que los engranajes de un reloj real.
    """

    def __init__(self):
        self.hours = RingCursor(CircularDoublyLinkedList(range(24)))
        self.minutes = RingCursor(CircularDoublyLinkedList(range(60)))
        self.seconds = RingCursor(CircularDoublyLinkedList(range(60)))
        self.days = 0

    @property
    def hour(self):
        return self.hours.value

    @property
    def minute(self):
        return self.minutes.value

    @property
    def second(self):
        return self.seconds.value

    def set(self, hour, minute, second=0):
        # Se valida antes de mover nada: si un valor no existe en su anillo,
        # seek no encuentra nada y el reloj quedaria a medio ajustar.
        if not (0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60):
            raise ValueError("hora fuera de rango")
        self.hours.seek(lambda v: v == hour)
        self.minutes.seek(lambda v: v == minute)
        self.seconds.seek(lambda v: v == second)

    def tick(self):
        """Avanza un segundo. Devuelve True si cambio el minuto."""
        if self.seconds.forward() != 0:
            return False
        if self.minutes.forward() == 0 and self.hours.forward() == 0:
            self.days += 1
        return True

    def seconds_of_day(self):
        return self.hour * 3600 + self.minute * 60 + self.second

    def text(self):
        return two(self.hour) + ":" + two(self.minute) + ":" + two(self.second)


# ======================================================================
# Pantalla: ajustes, colores ANSI y salida segura
# ======================================================================
# Ciclos vacios que tarda un segundo. Se midio con Python 3.13 en Windows 11
# (unos 100 millones por segundo dentro de una funcion, menos lo que tarda
# dibujar cada cuadro); cada computador es distinto, por eso el menu de
# ajustes permite calibrarlo.
LOOPS_PER_SECOND = 97000000


class Display:
    """Ajustes de pantalla que el usuario puede cambiar desde el menu."""

    def __init__(self):
        self.color = True        # colores ANSI
        self.ansi = True         # borrar la pantalla y mover el cursor con ANSI
        self.unicode = True      # se apaga solo si la salida no acepta Unicode
        self.loops_per_second = LOOPS_PER_SECOND

    def use_ascii(self):
        """Pasa a modo de respaldo: solo caracteres ASCII y sin codigos ANSI.

        Si la salida no acepta Unicode casi seguro no es una consola sino un
        archivo o una tuberia, donde los codigos ANSI solo ensucian.
        """
        self.unicode = False
        self.color = False
        self.ansi = False


DISPLAY = Display()

# Los codigos de escape ANSI son texto comun: ESC + "[" + parametros + letra.
ESC = "\x1b["
RESET = ESC + "0m"
CLEAR_SCREEN = ESC + "2J" + ESC + "H"   # borra todo y lleva el cursor arriba
CURSOR_HOME = ESC + "H"                 # cursor a la esquina superior izquierda
CLEAR_LINE_END = ESC + "K"              # borra hasta el final de la linea
CLEAR_BELOW = ESC + "J"                 # borra desde el cursor hacia abajo
HIDE_CURSOR = ESC + "?25l"
SHOW_CURSOR = ESC + "?25h"
BELL = "\a"                             # campana: la consola hace un sonido

# Paleta de 256 colores: bisel dorado, esfera oscura, manecillas plateada,
# azul acero y roja, digitos color ambar.
C_FACE = 234             # fondo de la esfera
C_BEZEL = 178            # bisel dorado
C_BEZEL_LIGHT = 222      # bisel iluminado (arriba a la izquierda)
C_BEZEL_DARK = 94        # bisel en sombra (abajo a la derecha)
C_BEZEL_ALERT = 160      # bisel cuando suena una alarma
C_MINUTE_MARK = 240
C_HOUR_MARK = 250
C_QUARTER_MARK = 178     # marcas de 12, 3, 6 y 9
C_NUMBER = 230
C_NUMBER_MAIN = 220      # numeros 12, 3, 6 y 9
C_LABEL = 137
C_HOUR_HAND = 255
C_MINUTE_HAND = 110
C_SECOND_HAND = 196
C_AXLE = 178
C_DIGITS = 214
C_FRAME = 136
C_TITLE = 220
C_KEY = 214
C_TEXT = 252
C_TEXT_DIM = 244
C_ALERT_FG = 231
C_ALERT_BG = 160

# Reemplazos ASCII para cuando la salida no acepta Unicode.
ASCII_FALLBACK = {
    "█": "#", "▀": '"', "▄": ".",
    "═": "=", "║": "|", "╔": "+", "╗": "+",
    "╚": "+", "╝": "+", "╟": "+", "╢": "+",
    "─": "-", "│": "|", "·": "-",
}


def strip_ansi(text):
    """Quita los codigos de escape ANSI (ESC [ ... letra) de un texto."""
    out = []
    i = 0
    while i < len(text):
        if text[i] == "\x1b":
            i += 1
            if i < len(text) and text[i] == "[":
                i += 1
                # Los parametros terminan en un caracter entre '@' y '~'.
                while i < len(text) and not ("@" <= text[i] <= "~"):
                    i += 1
            i += 1
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def visible_len(text):
    """Largo del texto tal como se ve, sin contar los codigos ANSI."""
    return len(strip_ansi(text))


def pad(text, width):
    """Rellena con espacios hasta ``width`` columnas visibles."""
    return text + " " * max(width - visible_len(text), 0)


def to_ascii(text):
    """Cambia los caracteres que no son ASCII por un equivalente ASCII."""
    out = []
    for char in text:
        if char < "\x80":
            out.append(char)
        else:
            out.append(ASCII_FALLBACK.get(char, "?"))
    return "".join(out)


def show(text="", end="\n", flush=False):
    """``print`` que nunca se cae por la codificacion de la salida.

    Si la salida se redirige a un archivo o tuberia en Windows, Python la
    codifica en cp1252 y ``print`` lanza UnicodeEncodeError con los bloques y
    las cajas. Sin poder importar ``sys`` no se puede cambiar esa codificacion,
    asi que se captura el error y se repite el texto en ASCII.
    """
    if DISPLAY.unicode:
        try:
            print(text, end=end, flush=flush)
            return
        except UnicodeEncodeError:
            DISPLAY.use_ascii()
            text = strip_ansi(text)
    print(to_ascii(text), end=end, flush=flush)


def is_terminal(fd, mode):
    """True si el descriptor ``fd`` (0 = teclado, 1 = pantalla) es una consola.

    Usa solo ``open``, que es una funcion integrada: abre el descriptor sin
    cerrarlo al final (``closefd=False``) y le pregunta ``isatty``. Si algo
    falla se supone que si es una consola.
    """
    try:
        with open(fd, mode, buffering=0, closefd=False) as stream:
            return stream.isatty()
    except (OSError, ValueError):
        return True


def style_code(fg=None, bg=None, bold=False):
    """Codigo ANSI que pone negrita, color de letra y color de fondo."""
    codes = []
    if bold:
        codes.append("1")
    if fg is not None:
        codes.append("38;5;" + str(fg))
    if bg is not None:
        codes.append("48;5;" + str(bg))
    if not codes:
        return ""
    return ESC + ";".join(codes) + "m"


def paint(text, fg=None, bg=None, bold=False):
    """Pinta ``text`` con colores ANSI; sin colores lo devuelve igual."""
    if not DISPLAY.color or text == "":
        return text
    return style_code(fg, bg, bold) + text + RESET


def clear_screen():
    if DISPLAY.ansi:
        show(CLEAR_SCREEN, end="")
    else:
        show()


def wait_one_second():
    """Espera mas o menos un segundo dando vueltas en un ciclo vacio.

    Sin el modulo ``time`` no hay reloj del sistema: la unica forma de dejar
    pasar el tiempo es hacer trabajo inutil. Cuantas vueltas son un segundo
    depende del computador; se ajusta en Ajustes > Calibrar velocidad.
    """
    for _ in range(DISPLAY.loops_per_second):
        pass


# ======================================================================
# Lienzo de pixeles
# ======================================================================
class PixelCanvas:
    """Matriz de pixeles de colores que se imprime con medios bloques.

    Un caracter de la consola mide mas o menos el doble de alto que de ancho.
    Cada caracter muestra dos pixeles, uno arriba y otro abajo, con
    ``▀`` (mitad de arriba), ``▄`` (mitad de abajo) y ``█``
    (las dos). Asi cada pixel es casi cuadrado y un circulo sale redondo.
    ``None`` es un pixel vacio; cualquier otro valor es su color.
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.pixels = [[None] * width for _ in range(height)]

    def plot(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = color

    def get(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.pixels[y][x]
        return None

    def stamp(self, x, y, color, brush):
        """Pinta el pincel ``brush`` (lista de desplazamientos) en (x, y)."""
        for dx, dy in brush:
            self.plot(x + dx, y + dy, color)

    def line(self, x0, y0, x1, y1, color, brush=((0, 0),)):
        """Linea de Bresenham: solo sumas y restas de enteros.

        ``err`` guarda cuanto se aleja la linea dibujada de la ideal; segun su
        signo se avanza en x, en y o en las dos.
        """
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.stamp(x0, y0, color, brush)
            if x0 == x1 and y0 == y1:
                return
            doubled = 2 * err
            if doubled >= dy:
                err += dy
                x0 += sx
            if doubled <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, radius, color):
        """Circulo relleno."""
        limit = radius * radius
        for y in range(int(cy - radius) - 1, int(cy + radius) + 2):
            for x in range(int(cx - radius) - 1, int(cx + radius) + 2):
                if (x - cx) ** 2 + (y - cy) ** 2 <= limit:
                    self.plot(x, y, color)

    def to_text(self, overlays=None, color=False, background=None):
        """Convierte el lienzo en texto, dos filas de pixeles por linea.

        ``overlays`` pone letras encima del dibujo: {(fila, columna):
        (letra, color, negrita, debajo)}. Si ``debajo`` es True la letra solo
        se ve donde no hay nada dibujado (como un rotulo bajo las manecillas).
        ``background`` es el color que en modo sin color cuenta como vacio.
        """
        if overlays is None:
            overlays = {}
        lines = []
        for row in range((self.height + 1) // 2):
            cells = []
            for col in range(self.width):
                cells.append(self._cell(col, row, overlays.get((row, col)), color, background))
            lines.append(join_cells(cells, color))
        return "\n".join(lines)

    def _cell(self, col, row, overlay, color, background):
        """Letra y colores (letra, fondo, negrita) de una celda de texto."""
        top = self.get(col, 2 * row)
        bottom = self.get(col, 2 * row + 1)
        if not color:
            # Sin colores, el fondo de la esfera se llenaria de bloques.
            if top == background:
                top = None
            if bottom == background:
                bottom = None
        if overlay is not None:
            char, fg, bold, under = overlay
            covered = top not in (None, background) or bottom not in (None, background)
            if not (under and covered):
                return char, fg, background, bold
        if top is None and bottom is None:
            return " ", None, None, False
        if top == bottom:
            return "█", top, None, False
        if bottom is None:
            return "▀", top, None, False
        if top is None:
            return "▄", bottom, None, False
        # Dos colores distintos: la letra pinta arriba y el fondo abajo.
        return "▀", top, bottom, False


def join_cells(cells, color):
    """Une las celdas de una linea; con color solo cambia el estilo si hace falta."""
    if not color:
        return "".join(cell[0] for cell in cells).rstrip()
    out = []
    current = None
    for char, fg, bg, bold in cells:
        style = (fg, bg, bold)
        if char == " " and bg is None:
            style = (None, None, False)
        if style != current:
            out.append(RESET + style_code(*style))
            current = style
        out.append(char)
    out.append(RESET)
    return "".join(out)


# ======================================================================
# Esferas
# ======================================================================
DIAL_RADIUS = 10
MINUTE_MARKS = CircularDoublyLinkedList(range(60))


def render_dial(hour, minute, second):
    """Esfera compacta en ASCII (version original).

    Las letras de la consola son el doble de altas que de anchas, por eso la
    coordenada x se multiplica por 2: asi la esfera se ve redonda. Se usa
    cuando la salida no acepta Unicode; la esfera normal es ``render_face``.
    """
    r = DIAL_RADIUS
    grid = [[" "] * (4 * r + 1) for _ in range(2 * r + 1)]

    def put(degrees, radius, text):
        angle = degrees * PI / 180
        x = 2 * r + round(2 * radius * sin(angle)) - len(text) // 2
        y = r - round(radius * cos(angle))
        for i in range(len(text)):
            grid[y][x + i] = text[i]

    for mark in MINUTE_MARKS:
        put(mark * 6, r, "+" if mark % 5 == 0 else ".")
    for number in range(1, 13):
        put(number * 30, r - 2, str(number))

    hands = (
        # Los numeros estan en el radio r - 2; las manecillas no deben llegar ahi.
        (second * 6, r * 0.7, ":"),
        ((minute + second / 60) * 6, r * 0.6, "*"),
        ((hour % 12 + minute / 60) * 30, r * 0.45, "#"),
    )
    for degrees, length, char in hands:
        step = 1.0
        while step <= length:
            put(degrees, step, char)
            step += 0.5
    grid[r][2 * r] = "O"
    return "\n".join("".join(row).rstrip() for row in grid)


# Medidas de la esfera de alta resolucion, en pixeles.
FACE_SIZE = 41                  # 41 x 41 pixeles = 41 columnas x 21 lineas
FACE_CENTER = FACE_SIZE // 2    # el centro es el pixel (20, 20)
BEZEL_OUTER = 20.5              # bisel: anillo entre estos dos radios
BEZEL_INNER = 18.5
MARK_RADIUS = 17.5              # punta exterior de las marcas
NUMBER_RADIUS = 13              # centro de los numeros
HOUR_HAND_LENGTH = 7.5          # las manecillas no llegan a los numeros
MINUTE_HAND_LENGTH = 11
SECOND_HAND_LENGTH = 15.5       # el segundero es fino y pasa bajo los numeros
SECOND_HAND_TAIL = 4
FACE_LABEL = "PYTHON PURO"

# Pinceles: desplazamientos que se pintan en cada punto de una linea.
BRUSH_THIN = ((0, 0),)
BRUSH_PLUS = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))
BRUSH_THICK = tuple((dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1))


def polar(degrees, radius):
    """Punto a ``radius`` pixeles del centro; 0 grados = las 12, sentido horario."""
    angle = degrees * PI / 180
    return FACE_CENTER + radius * sin(angle), FACE_CENTER - radius * cos(angle)


def radial_line(canvas, degrees, start, end, color, brush):
    """Linea sobre un rayo que sale del centro, del radio ``start`` al ``end``."""
    x0, y0 = polar(degrees, start)
    x1, y1 = polar(degrees, end)
    canvas.line(round(x0), round(y0), round(x1), round(y1), color, brush)


def bezel_color(dx, dy, distance, alert):
    """Color del bisel segun de donde viene la luz (arriba a la izquierda)."""
    if alert:
        return C_BEZEL_ALERT
    light = -(dx + dy) / (distance * 1.4142)
    if light > 0.4:
        return C_BEZEL_LIGHT
    if light < -0.4:
        return C_BEZEL_DARK
    return C_BEZEL


def render_face(hour, minute, second, color=False, alert=False):
    """Esfera analogica de alta resolucion (41 columnas x 21 lineas).

    Se dibuja en un ``PixelCanvas``: fondo y bisel, marcas, manecillas con
    lineas de Bresenham y eje. Los numeros se ponen al final como letras, asi
    nada los tapa. El horario y el minutero se mueven de forma continua: el
    horario avanza un poco cada minuto y el minutero un poco cada segundo.
    Con ``alert`` el bisel se pinta de rojo.
    """
    size = FACE_SIZE
    c = FACE_CENTER
    canvas = PixelCanvas(size, size)

    # 1. Fondo de la esfera y bisel con luz y sombra.
    for y in range(size):
        for x in range(size):
            dx = x - c
            dy = y - c
            distance = (dx * dx + dy * dy) ** 0.5
            if distance <= BEZEL_INNER:
                canvas.plot(x, y, C_FACE)
            elif distance <= BEZEL_OUTER:
                canvas.plot(x, y, bezel_color(dx, dy, distance, alert))

    # 2. Marcas: un punto por minuto, una raya por hora y una mas gruesa
    #    y dorada en 12, 3, 6 y 9.
    for mark in MINUTE_MARKS:
        degrees = mark * 6
        if mark % 15 == 0:
            # Mas corta porque el pincel en cruz la ensancha un pixel por lado.
            radial_line(canvas, degrees, 15.5, MARK_RADIUS - 1, C_QUARTER_MARK, BRUSH_PLUS)
        elif mark % 5 == 0:
            radial_line(canvas, degrees, 15.5, MARK_RADIUS, C_HOUR_MARK, BRUSH_THIN)
        else:
            x, y = polar(degrees, MARK_RADIUS)
            canvas.plot(round(x), round(y), C_MINUTE_MARK)

    # 3. Manecillas. Los angulos incluyen las fracciones: a las 10:30 el
    #    horario esta a mitad de camino entre el 10 y el 11.
    hour_degrees = (hour % 12 + minute / 60 + second / 3600) * 30
    minute_degrees = (minute + second / 60) * 6
    second_degrees = second * 6
    radial_line(canvas, hour_degrees, 0, HOUR_HAND_LENGTH, C_HOUR_HAND, BRUSH_THICK)
    radial_line(canvas, minute_degrees, 0, MINUTE_HAND_LENGTH, C_MINUTE_HAND, BRUSH_PLUS)
    radial_line(canvas, second_degrees + 180, 0, SECOND_HAND_TAIL, C_SECOND_HAND, BRUSH_THIN)
    radial_line(canvas, second_degrees, 0, SECOND_HAND_LENGTH, C_SECOND_HAND, BRUSH_THIN)
    tail_x, tail_y = polar(second_degrees + 180, SECOND_HAND_TAIL)
    canvas.disc(round(tail_x), round(tail_y), 1, C_SECOND_HAND)   # contrapeso

    # 4. Eje central: disco dorado con un punto rojo en el medio.
    canvas.disc(c, c, 1.5, C_AXLE)
    canvas.plot(c, c, C_SECOND_HAND)

    # 5. Numeros y rotulo, como letras encima de los pixeles.
    overlays = {}
    for number in range(1, 13):
        x, y = polar(number * 30, NUMBER_RADIUS)
        text = str(number)
        row = round(y) // 2
        col = int(x - len(text) / 2 + 0.5)
        main = number % 3 == 0
        for i in range(len(text)):
            overlays[(row, col + i)] = (text[i], C_NUMBER_MAIN if main else C_NUMBER, True, False)
    label_row = (c + 7) // 2
    label_col = c - len(FACE_LABEL) // 2
    for i in range(len(FACE_LABEL)):
        if FACE_LABEL[i] != " ":
            overlays[(label_row, label_col + i)] = (FACE_LABEL[i], C_LABEL, False, True)

    return canvas.to_text(overlays, color, C_FACE)


# ======================================================================
# Hora digital grande (7 segmentos)
# ======================================================================
#   aaa
#  f   b      Cada digito enciende algunos de los 7 segmentos.
#   ggg
#  e   c
#   ddd
SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
}
DIGIT_WIDTH = 6     # pixeles; cada trazo mide 2 pixeles de grueso
DIGIT_HEIGHT = 10   # 10 pixeles = 5 lineas de texto
COLON_WIDTH = 2
DIGIT_GAP = 2


def render_big_time(text, color=False):
    """Hora como ``10:08:30`` en digitos grandes de 7 segmentos (5 lineas).

    Se dibuja en un lienzo de pixeles igual que la esfera; cada segmento es un
    rectangulo de 2 pixeles de grueso. Sin Unicode usa la version clasica de
    3 lineas hecha con ``_`` y ``|``.
    """
    if not DISPLAY.unicode:
        return render_big_time_ascii(text)
    width = 0
    for char in text:
        width += (COLON_WIDTH if char == ":" else DIGIT_WIDTH) + DIGIT_GAP
    canvas = PixelCanvas(width - DIGIT_GAP, DIGIT_HEIGHT)
    x = 0
    right = DIGIT_WIDTH - 2         # columna donde empieza el trazo derecho
    for char in text:
        if char == ":":
            for dx in range(COLON_WIDTH):
                for y in (2, 3, 6, 7):
                    canvas.plot(x + dx, y, C_DIGITS)
            x += COLON_WIDTH + DIGIT_GAP
            continue
        lit = SEGMENTS.get(char, "")
        # Segmento: (nombre, x inicial, y inicial, x final, y final).
        pieces = (
            ("a", 0, 0, right + 1, 1), ("g", 0, 4, right + 1, 5), ("d", 0, 8, right + 1, 9),
            ("f", 0, 0, 1, 5), ("b", right, 0, right + 1, 5),
            ("e", 0, 4, 1, 9), ("c", right, 4, right + 1, 9),
        )
        for segment, x0, y0, x1, y1 in pieces:
            if segment in lit:
                for y in range(y0, y1 + 1):
                    canvas.line(x + x0, y, x + x1, y, C_DIGITS)
        x += DIGIT_WIDTH + DIGIT_GAP
    return canvas.to_text(None, color)


def render_big_time_ascii(text):
    """Version ASCII de 3 lineas de los digitos de 7 segmentos."""
    rows = ["", "", ""]
    for char in text:
        if char == ":":
            parts = (" ", ".", ".")
        else:
            lit = SEGMENTS.get(char, "")

            def on(segment, mark):
                return mark if segment in lit else " "

            parts = (" " + on("a", "_") + " ",
                     on("f", "|") + on("g", "_") + on("b", "|"),
                     on("e", "|") + on("d", "_") + on("c", "|"))
        for i in range(3):
            rows[i] += parts[i] + " "
    return "\n".join(row.rstrip() for row in rows)


# ======================================================================
# Marcos y menus con caracteres de caja
# ======================================================================
UI_WIDTH = 66                   # ancho interior de los marcos
SCREEN_WIDTH = UI_WIDTH + 2     # ancho total con los bordes


def frame_lines(title, right, sections):
    """Marco de linea doble: titulo, hora a la derecha y secciones separadas.

    Si ``title`` es None el marco no tiene fila de titulo.
    """
    w = UI_WIDTH
    lines = [paint("╔" + "═" * w + "╗", C_FRAME)]
    side = paint("║", C_FRAME)
    if title is not None:
        head = "  " + paint(title, C_TITLE, bold=True)
        tail = paint(right, C_TEXT_DIM) + "  "
        gap = w - visible_len(head) - visible_len(tail)
        lines.append(side + head + " " * max(gap, 1) + tail + side)
    for i in range(len(sections)):
        if i > 0 or title is not None:
            lines.append(paint("╟" + "─" * w + "╢", C_FRAME))
        for row in sections[i]:
            lines.append(side + pad(row, w) + side)
    lines.append(paint("╚" + "═" * w + "╝", C_FRAME))
    return lines


def options_rows(options, columns=3):
    """Acomoda pares (tecla, texto) en columnas: '1  Ver reloj   2  ...'."""
    cell = (UI_WIDTH - 2) // columns
    rows = []
    for start in range(0, len(options), columns):
        row = "  "
        for key, label in options[start:start + columns]:
            row += pad(paint(key, C_KEY, bold=True) + "  " + paint(label, C_TEXT), cell)
        rows.append(row)
    return rows


def title_bar(left, right):
    """Barra de una linea: '== RELOJ ============ Ctrl+C: menu =='."""
    middle = SCREEN_WIDTH - len(left) - len(right) - 8
    return (paint("══ ", C_FRAME) + paint(left, C_TITLE, bold=True)
            + paint(" " + "═" * middle + " ", C_FRAME) + paint(right, C_TEXT_DIM)
            + paint(" ══", C_FRAME))


def center(text, width=SCREEN_WIDTH):
    return " " * max((width - visible_len(text)) // 2, 0) + text


def center_block(text, width=SCREEN_WIDTH):
    """Centra un dibujo de varias lineas moviendolas todas lo mismo."""
    lines = text.split("\n")
    block = 0
    for line in lines:
        block = max(block, visible_len(line))
    margin = " " * max((width - block) // 2, 0)
    return [margin + line for line in lines]


def draw_face(hour, minute, second, alert=False):
    """Esfera segun lo que acepte la salida: alta resolucion o ASCII."""
    if DISPLAY.unicode:
        return render_face(hour, minute, second, DISPLAY.color, alert)
    return render_dial(hour, minute, second)


def on_off(flag):
    return paint("ON ", 114, bold=True) if flag else paint("OFF", C_TEXT_DIM, bold=True)


# ======================================================================
# Funciones del reloj
# ======================================================================
WEEKDAY_NAMES = ("Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom")


class Alarm:
    def __init__(self, hour, minute, label):
        self.hour = hour
        self.minute = minute
        self.label = label
        self.active = True

    def key(self):
        return self.hour * 60 + self.minute

    def text(self):
        state = "ON " if self.active else "OFF"
        return "[" + state + "] " + two(self.hour) + ":" + two(self.minute) + "  " + self.label


class AlarmManager:
    """Alarmas en una lista circular ordenada por hora."""

    def __init__(self):
        self.alarms = CircularDoublyLinkedList()

    def add(self, hour, minute, label):
        self.alarms.insert_sorted(Alarm(hour, minute, label), lambda a: a.key())

    def remove(self, index):
        return self.alarms.remove_node(self.alarms.node_at(index))

    def toggle(self, index):
        alarm = self.alarms.node_at(index).value
        alarm.active = not alarm.active
        return alarm

    def ringing(self, hour, minute):
        for alarm in self.alarms:
            if alarm.active and alarm.hour == hour and alarm.minute == minute:
                yield alarm

    def next_after(self, seconds_of_day):
        """Proxima alarma activa y cuantos segundos faltan para ella."""
        best = None
        best_wait = None
        for alarm in self.alarms:
            if not alarm.active:
                continue
            wait = (alarm.key() * 60 - seconds_of_day) % SECONDS_PER_DAY
            if wait == 0:
                wait = SECONDS_PER_DAY
            if best_wait is None or wait < best_wait:
                best, best_wait = alarm, wait
        return best, best_wait


class Stopwatch:
    def __init__(self):
        self.running = False
        self.elapsed = 0
        self.lap_start = 0
        self.laps = CircularDoublyLinkedList()

    def tick(self):
        if self.running:
            self.elapsed += 1

    def lap(self):
        self.laps.append(self.elapsed - self.lap_start)
        self.lap_start = self.elapsed

    def reset(self):
        self.running = False
        self.elapsed = 0
        self.lap_start = 0
        self.laps.clear()


class CountdownTimer:
    def __init__(self):
        self.running = False
        self.remaining = 0

    def start(self, seconds):
        # Una duracion negativa no tiene sentido: el temporizador queda en cero.
        self.remaining = max(seconds, 0)
        self.running = seconds > 0

    def tick(self):
        """Resta un segundo. Devuelve True en el segundo en que llega a cero."""
        if not self.running:
            return False
        self.remaining -= 1
        if self.remaining == 0:
            self.running = False
            return True
        return False


class WorldClock:
    """Ciudades en una lista circular; un cursor marca la ciudad seleccionada.

    Los desfases son los de horario estandar (sin horario de verano).
    """

    def __init__(self):
        self.local_offset = -5 * 60
        self.cities = CircularDoublyLinkedList((
            ("Bogota", -5 * 60),
            ("Ciudad de Mexico", -6 * 60),
            ("Nueva York", -5 * 60),
            ("Buenos Aires", -3 * 60),
            ("Londres", 0),
            ("Madrid", 1 * 60),
            ("Nueva Delhi", 5 * 60 + 30),
            ("Tokio", 9 * 60),
            ("Sidney", 10 * 60),
        ))
        self.cursor = RingCursor(self.cities)

    def time_in(self, offset, seconds_of_day):
        """Hora en otra zona y si es el dia anterior (-1), el mismo (0) o el siguiente (+1)."""
        shifted = seconds_of_day + (offset - self.local_offset) * 60
        return shifted % SECONDS_PER_DAY, shifted // SECONDS_PER_DAY


# ======================================================================
# Lectura de datos
# ======================================================================
def goodbye():
    """Deja la consola como estaba (color normal y cursor visible) y se despide."""
    if DISPLAY.ansi:
        show(RESET + SHOW_CURSOR, end="")
    show()
    show(paint("Hasta luego.", C_TITLE, bold=True))


def ask(prompt):
    try:
        return input(to_ascii(prompt) if not DISPLAY.unicode else prompt).strip()
    except UnicodeEncodeError:
        DISPLAY.use_ascii()
        return ask(strip_ansi(prompt))
    except (EOFError, KeyboardInterrupt):
        # Fin de la entrada (o Ctrl+C): se sale sin mostrar errores.
        show()
        goodbye()
        raise SystemExit(0)


def is_digits(text):
    """True si ``text`` tiene solo digitos 0-9 (y al menos uno).

    ``int`` acepta tambien signos, espacios y guiones bajos ('+5', ' 7', '1_0'),
    que no son horas ni duraciones validas.
    """
    if text == "":
        return False
    for char in text:
        if not ("0" <= char <= "9"):
            return False
    return True


def parse_time(text):
    """'7:30' o '07:30:15' -> (7, 30, 15). Devuelve None si no es valida."""
    parts = text.strip().split(":")
    if len(parts) not in (2, 3):
        return None
    for part in parts:
        if not is_digits(part):
            return None
    try:
        numbers = [int(p) for p in parts]
    except ValueError:  # numeros de miles de digitos
        return None
    if len(numbers) == 2:
        numbers.append(0)
    hour, minute, second = numbers
    if not (0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60):
        return None
    return hour, minute, second


def parse_duration(text):
    """'90', '90s', '5m', '2h' o '1:30:00' -> segundos. None si no es valido."""
    text = text.lower().replace(" ", "")
    if ":" in text:
        parts = text.split(":")
        if len(parts) > 3:
            return None
        total = 0
        for i in range(len(parts)):
            # Cada parte debe ser un numero sin signo ('1:-2' antes daba 58).
            if not is_digits(parts[i]):
                return None
            try:
                value = int(parts[i])
            except ValueError:  # numeros de miles de digitos
                return None
            # Despues de la primera parte vienen minutos o segundos: 0..59.
            if i > 0 and value >= 60:
                return None
            total = total * 60 + value
        return total
    factor = 1
    if text.endswith("h"):
        factor, text = 3600, text[:-1]
    elif text.endswith("m"):
        factor, text = 60, text[:-1]
    elif text.endswith("s"):
        text = text[:-1]
    if not is_digits(text):
        return None
    try:
        return int(text) * factor
    except ValueError:  # numeros de miles de digitos
        return None


def parse_decimal(text):
    """'12', '12.5' o '12,5' -> numero positivo. None si no es valido."""
    parts = text.replace(",", ".").split(".")
    if len(parts) > 2 or len(text) > 12:
        return None
    for part in parts:
        if not is_digits(part):
            return None
    value = float(".".join(parts))
    return value if value > 0 else None


def ask_int(prompt, low, high):
    text = ask(prompt)
    if not is_digits(text) or len(text) > len(str(high)):
        return None
    value = int(text)
    return value if low <= value <= high else None


# ======================================================================
# Aplicacion de consola
# ======================================================================
ALERT_SECONDS = 10      # segundos que un aviso queda en pantalla en modo en vivo
MAIN_OPTIONS = (
    ("1", "Ver reloj"), ("2", "Ajustar hora"), ("3", "Avanzar tiempo"),
    ("4", "Alarmas"), ("5", "Cronometro"), ("6", "Temporizador"),
    ("7", "Reloj mundial"), ("8", "Modo en vivo"), ("9", "Ajustes"),
    ("0", "Salir"),
)


class App:
    def __init__(self):
        self.clock = Clock()
        self.alarms = AlarmManager()
        self.stopwatch = Stopwatch()
        self.timer = CountdownTimer()
        self.world = WorldClock()
        self.notifications = LinkedQueue()
        # Mensajes para la proxima pantalla: (texto, es_aviso). Como cada menu
        # borra la pantalla, un print suelto se perderia al redibujar.
        self.messages = []
        self.pending_choice = ""

    # --------------------------------------------------------- tiempo
    def step(self):
        """Avanza un segundo todo el sistema y encola los avisos que salten."""
        minute_changed = self.clock.tick()
        self.stopwatch.tick()
        if self.timer.tick():
            self.notifications.enqueue("TEMPORIZADOR: el tiempo termino a las " + self.clock.text())
        if minute_changed:
            for alarm in self.alarms.ringing(self.clock.hour, self.clock.minute):
                self.notifications.enqueue(
                    "ALARMA " + two(alarm.hour) + ":" + two(alarm.minute) + "  " + alarm.label
                )

    def advance(self, seconds):
        """Hace avanzar todo el sistema segundo a segundo."""
        for _ in range(seconds):
            self.step()
        self.say("Hora actual: " + self.clock.text())
        self.show_notifications()

    def show_notifications(self):
        while not self.notifications.is_empty():
            self.say(self.notifications.dequeue(), alert=True)

    def ask_advance(self):
        text = ask("Cuanto avanzar (ej. 30, 5m, 2h, 1:30:00): ")
        seconds = parse_duration(text)
        if seconds is None:
            self.say("Duracion no valida.")
            return
        if seconds > MAX_ADVANCE:
            # El tiempo avanza segundo a segundo; algo como '99999h' dejaria
            # el programa colgado varios minutos.
            self.say("Maximo " + str(MAX_ADVANCE // SECONDS_PER_DAY) + " dias por vez.")
            return
        self.advance(seconds)

    # ------------------------------------------------------- pantalla
    def say(self, text, alert=False):
        """Guarda un mensaje para mostrarlo debajo de la proxima pantalla."""
        self.messages.append((text, alert))

    def flush_messages(self):
        bell = False
        for text, alert in self.messages:
            if alert:
                bell = True
                show("  " + paint(" *** " + text + " *** ", C_ALERT_FG, C_ALERT_BG, bold=True))
            else:
                show("  " + paint(text, C_TEXT))
        if bell:
            show(BELL, end="")
        self.messages = []

    def header_right(self):
        return self.clock.text() + "  Dia " + str(self.clock.days + 1)

    def screen(self, title, body, options):
        """Borra la pantalla y dibuja un menu enmarcado con sus mensajes."""
        clear_screen()
        sections = []
        if body:
            sections.append(body)
        if options:
            sections.append(options_rows(options))
        show("\n".join(frame_lines(title, self.header_right(), sections)))
        self.flush_messages()

    def clock_lines(self, title, hint, alerts=()):
        """Pantalla del reloj: esfera, hora digital grande y lineas de estado.

        Con la esfera de 21 lineas, los digitos de 5 y tres lineas de texto
        ocupa 29 lineas, para que quepa en una consola de 80 x 30.
        """
        clock = self.clock
        flash = len(alerts) > 0 and clock.second % 2 == 0
        lines = [title_bar(title, hint)]
        lines += center_block(draw_face(clock.hour, clock.minute, clock.second, flash))
        lines += center_block(render_big_time(clock.text(), DISPLAY.color))

        # Linea de informacion: a.m./p.m., dia y proxima alarma.
        dot = paint("  ·  ", C_FRAME)
        hour12 = clock.hour % 12 or 12
        suffix = "a.m." if clock.hour < 12 else "p.m."
        info = (paint(str(hour12) + ":" + two(clock.minute) + " " + suffix, C_TITLE, bold=True) + dot
                + paint("Dia " + str(clock.days + 1) + " (" + WEEKDAY_NAMES[clock.days % 7] + ")", C_TEXT))
        alarm, wait = self.alarms.next_after(clock.seconds_of_day())
        if alarm is None:
            info += dot + paint("Sin alarmas activas", C_TEXT_DIM)
        else:
            info += dot + paint("Proxima alarma " + two(alarm.hour) + ":" + two(alarm.minute)
                                + " (en " + format_seconds(wait) + ")", C_TEXT)
        lines.append(center(info))

        status = []
        if self.timer.running:
            status.append("Temporizador " + format_seconds(self.timer.remaining))
        if self.stopwatch.running:
            status.append("Cronometro " + format_seconds(self.stopwatch.elapsed))
        if status:
            lines.append(center(paint("   |   ".join(status), C_MINUTE_HAND)))
        if alerts:
            text = " *** " + "  |  ".join(alerts) + " *** "
            lines.append(center(paint(text, C_ALERT_FG, C_ALERT_BG, bold=True)))
        return lines

    # ----------------------------------------------------------- menus
    def run(self):
        live_keyboard = is_terminal(0, "rb")
        if not is_terminal(1, "wb"):
            # Salida a un archivo o tuberia: nada de codigos ANSI.
            DISPLAY.color = False
            DISPLAY.ansi = False
        self.screen("RELOJ DE CONSOLA", [
            "  Reloj analogico simulado en Python puro, sin librerias.",
            "  Escribe la hora actual para ponerlo en marcha.",
        ], [])
        self.ask_set_time()
        # Lo primero que se ve es el reloj andando. Si la entrada viene de una
        # tuberia nadie podria detenerlo con Ctrl+C, asi que se salta.
        if live_keyboard:
            self.live_mode()
        options = {
            "1": self.show_clock,
            "2": self.ask_set_time,
            "3": self.ask_advance,
            "4": self.alarm_menu,
            "5": self.stopwatch_menu,
            "6": self.timer_menu,
            "7": self.world_menu,
            "8": self.live_mode,
            "9": self.settings_menu,
        }
        while True:
            self.screen("RELOJ DE CONSOLA", [
                "  " + paint("8  Modo en vivo", C_KEY, bold=True)
                + paint(": el reloj anda solo (Ctrl+C vuelve aqui).", C_TEXT_DIM),
            ], MAIN_OPTIONS)
            # Si en la pantalla del reloj ya se escribio una opcion, se usa esa.
            choice = self.pending_choice or ask("> ")
            self.pending_choice = ""
            if choice == "":
                continue
            if choice == "0":
                goodbye()
                return
            action = options.get(choice)
            if action is None:
                self.say("Opcion no valida.")
            else:
                action()

    def ask_set_time(self):
        while True:
            parsed = parse_time(ask("Hora actual (hh:mm o hh:mm:ss): "))
            if parsed is not None:
                self.clock.set(*parsed)
                self.say("Reloj en " + self.clock.text())
                return
            show("  " + paint("Hora no valida.", C_ALERT_BG, bold=True))

    def show_clock(self):
        clear_screen()
        show("\n".join(self.clock_lines("RELOJ", "Enter: menu")))
        self.flush_messages()
        self.pending_choice = ask("Enter: menu, o escribe una opcion > ")

    def live_mode(self):
        """El reloj avanza solo, segundo a segundo, hasta que se presione Ctrl+C.

        Cada vuelta dibuja la pantalla en el mismo lugar (cursor arriba, sin
        borrar todo para que no parpadee), espera un segundo y llama a
        ``step``, asi alarmas, cronometro y temporizador siguen funcionando.
        """
        alerts = []     # [texto, segundos que le quedan en pantalla]
        try:
            if DISPLAY.ansi:
                show(HIDE_CURSOR + CLEAR_SCREEN, end="")
            while True:
                fresh = False
                while not self.notifications.is_empty():
                    alerts.append([self.notifications.dequeue(), ALERT_SECONDS])
                    fresh = True
                lines = self.clock_lines("RELOJ EN VIVO", "Ctrl+C: menu", [a[0] for a in alerts])
                self.draw_live(lines, fresh)
                wait_one_second()
                self.step()
                for alert in alerts:
                    alert[1] -= 1
                alerts = [alert for alert in alerts if alert[1] > 0]
        except KeyboardInterrupt:
            pass
        finally:
            if DISPLAY.ansi:
                show(RESET + SHOW_CURSOR, end="", flush=True)

    def draw_live(self, lines, bell=False):
        if DISPLAY.ansi:
            # Sin salto de linea al final: asi la pantalla no se desplaza.
            text = CURSOR_HOME + (CLEAR_LINE_END + "\n").join(lines) + CLEAR_LINE_END + CLEAR_BELOW
            show(text + (BELL if bell else ""), end="", flush=True)
        else:
            show("\n".join(lines) + (BELL if bell else ""), flush=True)
            show()

    def settings_menu(self):
        while True:
            self.screen("AJUSTES", [
                "  Colores ANSI                  " + on_off(DISPLAY.color),
                "  Pantalla limpia (ANSI)        " + on_off(DISPLAY.ansi),
                "  Esfera Unicode                " + on_off(DISPLAY.unicode),
                "  Velocidad                     " + paint(str(DISPLAY.loops_per_second), C_KEY)
                + " ciclos por segundo",
                "",
                paint("  Si ves simbolos raros como  [0m  o  [2J  apaga las dos", C_TEXT_DIM),
                paint("  opciones ANSI; si ves  ?  en lugar de bloques, apaga Unicode.", C_TEXT_DIM),
            ], (("c", "Colores"), ("l", "Pantalla limpia"), ("u", "Unicode"),
                ("v", "Calibrar reloj"), ("0", "Volver")))
            choice = ask("> ").lower()
            if choice == "0":
                return
            if choice == "c":
                DISPLAY.color = not DISPLAY.color
            elif choice == "l":
                DISPLAY.ansi = not DISPLAY.ansi
            elif choice == "u":
                DISPLAY.unicode = not DISPLAY.unicode
            elif choice == "v":
                self.calibrate_menu()
            else:
                self.say("Opcion no valida.")

    def calibrate_menu(self):
        while True:
            self.screen("CALIBRAR VELOCIDAD", [
                "  Ciclos vacios por segundo: " + paint(str(DISPLAY.loops_per_second), C_KEY, bold=True),
                "",
                "  p: cuenta 10 segundos en pantalla; mide con el cronometro del",
                "     celular cuanto tardo y el programa corrige solo.",
                "  +: el reloj va adelantado (alarga el segundo un 5 %).",
                "  -: el reloj va atrasado (acorta el segundo un 5 %).",
            ], (("p", "Prueba de 10 s"), ("+", "Mas lento"), ("-", "Mas rapido"),
                ("e", "Escribir valor"), ("0", "Volver")))
            choice = ask("> ").lower()
            if choice == "0":
                return
            if choice == "p":
                self.calibration_test()
            elif choice == "+":
                DISPLAY.loops_per_second = DISPLAY.loops_per_second * 105 // 100
            elif choice == "-":
                DISPLAY.loops_per_second = max(DISPLAY.loops_per_second * 95 // 100, 1000)
            elif choice == "e":
                value = ask_int("Ciclos por segundo (1000 a 9999999999): ", 1000, 9999999999)
                if value is None:
                    self.say("Numero no valido.")
                else:
                    DISPLAY.loops_per_second = value
            else:
                self.say("Opcion no valida.")

    def calibration_test(self):
        """Cuenta de 10 a 0 dibujando lo mismo que el modo en vivo.

        Dibujar tambien toma tiempo, por eso la prueba dibuja la esfera
        completa en cada segundo: asi se mide lo mismo que se va a usar.
        """
        ask("Prepara el cronometro del celular. Enter para empezar > ")
        try:
            if DISPLAY.ansi:
                show(HIDE_CURSOR + CLEAR_SCREEN, end="")
            for remaining in range(10, -1, -1):
                clock = self.clock
                lines = [title_bar("PRUEBA DE VELOCIDAD", "Ctrl+C: cancelar")]
                lines += center_block(draw_face(clock.hour, clock.minute, clock.second))
                lines += center_block(render_big_time("00:" + two(remaining), DISPLAY.color))
                lines.append(center(paint("Inicia el cronometro en 10 y detenlo en 0", C_TEXT)))
                self.draw_live(lines)
                if remaining > 0:
                    wait_one_second()
        except KeyboardInterrupt:
            self.say("Prueba cancelada.")
            return
        finally:
            if DISPLAY.ansi:
                show(RESET + SHOW_CURSOR, end="", flush=True)
        show()
        measured = parse_decimal(ask("Cuantos segundos marco el celular? (ej. 11.5): "))
        if measured is None:
            self.say("Numero no valido; la velocidad no cambio.")
            return
        # Si 10 segundos del programa duraron 'measured' segundos reales, cada
        # segundo necesita 10 / measured veces los ciclos actuales.
        new_value = int(DISPLAY.loops_per_second * 10 / measured)
        DISPLAY.loops_per_second = min(max(new_value, 1000), 9999999999)
        self.say("Nueva velocidad: " + str(DISPLAY.loops_per_second) + " ciclos por segundo.")

    def alarm_menu(self):
        while True:
            body = []
            if self.alarms.alarms.is_empty():
                body.append(paint("  (no hay alarmas)", C_TEXT_DIM))
            number = 1
            for alarm in self.alarms.alarms:
                body.append("  " + paint(str(number) + ".", C_KEY, bold=True) + " " + alarm.text())
                number += 1
            self.screen("ALARMAS", body, (("a", "Agregar"), ("b", "Borrar"), ("c", "Activar/apagar"),
                                          ("t", "Avanzar tiempo"), ("0", "Volver")))
            choice = ask("> ").lower()
            if choice == "0":
                return
            if choice == "a":
                parsed = parse_time(ask("Hora de la alarma (hh:mm): "))
                if parsed is None:
                    self.say("Hora no valida.")
                    continue
                label = ask("Nombre (opcional): ") or "Alarma"
                self.alarms.add(parsed[0], parsed[1], label)
            elif choice in ("b", "c"):
                total = len(self.alarms.alarms)
                if total == 0:
                    self.say("No hay alarmas.")
                    continue
                index = ask_int("Numero de alarma: ", 1, total)
                if index is None:
                    self.say("Numero no valido.")
                elif choice == "b":
                    self.alarms.remove(index - 1)
                else:
                    self.alarms.toggle(index - 1)
            elif choice == "t":
                self.ask_advance()
            else:
                self.say("Opcion no valida.")

    def stopwatch_menu(self):
        watch = self.stopwatch
        while True:
            state = "corriendo" if watch.running else "detenido"
            body = ["  " + paint(format_seconds(watch.elapsed), C_DIGITS, bold=True) + "  (" + state + ")"]
            if not watch.laps.is_empty():
                fastest = min(watch.laps)
                slowest = max(watch.laps)
                number = 1
                for lap in watch.laps:
                    mark = ""
                    # Si todas las vueltas duran lo mismo no hay rapida ni lenta.
                    if fastest != slowest and lap == fastest:
                        mark = paint("  <- mas rapida", 114)
                    elif fastest != slowest and lap == slowest:
                        mark = paint("  <- mas lenta", C_ALERT_BG)
                    body.append("  Vuelta " + str(number) + ": " + format_seconds(lap) + mark)
                    number += 1
            self.screen("CRONOMETRO", body, (("i", "Iniciar/pausar"), ("v", "Vuelta"), ("r", "Reiniciar"),
                                             ("t", "Avanzar tiempo"), ("0", "Volver")))
            choice = ask("> ").lower()
            if choice == "0":
                return
            if choice == "i":
                watch.running = not watch.running
            elif choice == "v":
                if watch.running:
                    watch.lap()
                else:
                    self.say("El cronometro esta detenido.")
            elif choice == "r":
                watch.reset()
            elif choice == "t":
                self.ask_advance()
            else:
                self.say("Opcion no valida.")

    def timer_menu(self):
        timer = self.timer
        while True:
            state = "corriendo" if timer.running else "detenido"
            body = ["  " + paint(format_seconds(timer.remaining), C_DIGITS, bold=True) + "  (" + state + ")"]
            self.screen("TEMPORIZADOR", body, (("n", "Nuevo"), ("p", "Pausar/seguir"), ("c", "Cancelar"),
                                               ("t", "Avanzar tiempo"), ("0", "Volver")))
            choice = ask("> ").lower()
            if choice == "0":
                return
            if choice == "n":
                seconds = parse_duration(ask("Duracion (ej. 90, 5m, 1:00:00): "))
                if not seconds:
                    self.say("Duracion no valida.")
                else:
                    timer.start(seconds)
            elif choice == "p":
                timer.running = not timer.running and timer.remaining > 0
            elif choice == "c":
                timer.start(0)
            elif choice == "t":
                self.ask_advance()
            else:
                self.say("Opcion no valida.")

    def world_menu(self):
        world = self.world
        day_words = {-1: "ayer", 0: "", 1: "manana"}
        while True:
            now = self.clock.seconds_of_day()
            name, offset = world.cursor.value
            seconds, day = world.time_in(offset, now)

            # Panel a la derecha de la esfera: lista de ciudades y detalle.
            panel = [paint("CIUDADES", C_TITLE, bold=True), ""]
            for city, city_offset in world.cities:
                city_seconds, city_day = world.time_in(city_offset, now)
                selected = city == name
                row = ("> " if selected else "  ") + (city + " " * 16)[:16] + "  " \
                    + format_seconds(city_seconds) + "  " + day_words[city_day]
                panel.append(paint(row, C_KEY, bold=True) if selected else paint(row, C_TEXT))
            panel += ["",
                      paint(name, C_TITLE, bold=True),
                      paint(format_seconds(seconds) + "  " + day_words[day], C_DIGITS, bold=True),
                      paint(format_offset(offset), C_TEXT),
                      paint("Zona local: " + format_offset(world.local_offset), C_TEXT_DIM)]

            clear_screen()
            show("\n".join(frame_lines("RELOJ MUNDIAL", self.header_right(), [])))
            face = draw_face(seconds // 3600, seconds // 60 % 60, seconds % 60).split("\n")
            for i in range(max(len(face), len(panel))):
                left = face[i] if i < len(face) else ""
                right = panel[i] if i < len(panel) else ""
                show(pad(left, FACE_SIZE) + "  " + right)
            show("\n".join(frame_lines(None, "", [options_rows(
                (("s", "Siguiente"), ("a", "Anterior"), ("z", "Zona local"),
                 ("t", "Avanzar tiempo"), ("0", "Volver")))])))
            self.flush_messages()
            choice = ask("> ").lower()
            if choice == "0":
                return
            if choice == "s":
                world.cursor.forward()
            elif choice == "a":
                world.cursor.backward()
            elif choice == "z":
                # La hora local no cambia; solo cambia contra que zona se comparan las demas.
                world.local_offset = offset
            elif choice == "t":
                self.ask_advance()
            else:
                self.say("Opcion no valida.")


if __name__ == "__main__":
    App().run()
