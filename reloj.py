"""Reloj de consola escrito en Python puro, sin importar ninguna libreria.

Python no trae ninguna funcion integrada para leer la hora del computador ni
para esperar un segundo (eso vive en los modulos ``time`` y ``datetime``), asi
que este reloj es simulado: la hora se ajusta a mano y el tiempo avanza con
comandos. Todo lo demas esta hecho aqui mismo: la lista circular doble, la
cola, el seno y el coseno, y el dibujo de la esfera.

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


DIAL_RADIUS = 10
MINUTE_MARKS = CircularDoublyLinkedList(range(60))


def render_dial(hour, minute, second):
    """Dibuja la esfera analogica con caracteres.

    Las letras de la consola son el doble de altas que de anchas, por eso la
    coordenada x se multiplica por 2: asi la esfera se ve redonda.
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
def ask(prompt):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        # Fin de la entrada (o Ctrl+C): se sale sin mostrar errores.
        print()
        print("Hasta luego.")
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


def ask_int(prompt, low, high):
    text = ask(prompt)
    if not is_digits(text) or len(text) > len(str(high)):
        return None
    value = int(text)
    return value if low <= value <= high else None


# ======================================================================
# Aplicacion de consola
# ======================================================================
class App:
    def __init__(self):
        self.clock = Clock()
        self.alarms = AlarmManager()
        self.stopwatch = Stopwatch()
        self.timer = CountdownTimer()
        self.world = WorldClock()
        self.notifications = LinkedQueue()

    # --------------------------------------------------------- tiempo
    def advance(self, seconds):
        """Hace avanzar todo el sistema segundo a segundo."""
        for _ in range(seconds):
            minute_changed = self.clock.tick()
            self.stopwatch.tick()
            if self.timer.tick():
                self.notifications.enqueue("TEMPORIZADOR: el tiempo termino a las " + self.clock.text())
            if minute_changed:
                for alarm in self.alarms.ringing(self.clock.hour, self.clock.minute):
                    self.notifications.enqueue(
                        "ALARMA " + two(alarm.hour) + ":" + two(alarm.minute) + "  " + alarm.label
                    )
        print("Hora actual: " + self.clock.text())
        self.show_notifications()

    def show_notifications(self):
        while not self.notifications.is_empty():
            print("  *** " + self.notifications.dequeue() + " ***")

    def ask_advance(self):
        text = ask("Cuanto avanzar (ej. 30, 5m, 2h, 1:30:00): ")
        seconds = parse_duration(text)
        if seconds is None:
            print("Duracion no valida.")
            return
        if seconds > MAX_ADVANCE:
            # El tiempo avanza segundo a segundo; algo como '99999h' dejaria
            # el programa colgado varios minutos.
            print("Maximo " + str(MAX_ADVANCE // SECONDS_PER_DAY) + " dias por vez.")
            return
        self.advance(seconds)

    # ----------------------------------------------------------- menus
    def run(self):
        print("RELOJ  (simulado, sin librerias)")
        self.ask_set_time()
        options = {
            "1": self.show_clock,
            "2": self.ask_set_time,
            "3": self.ask_advance,
            "4": self.alarm_menu,
            "5": self.stopwatch_menu,
            "6": self.timer_menu,
            "7": self.world_menu,
        }
        while True:
            print()
            print("1. Ver reloj        2. Ajustar hora     3. Avanzar tiempo")
            print("4. Alarmas          5. Cronometro       6. Temporizador")
            print("7. Reloj mundial    0. Salir")
            choice = ask("> ")
            if choice == "0":
                print("Hasta luego.")
                return
            action = options.get(choice)
            if action is None:
                print("Opcion no valida.")
            else:
                action()

    def ask_set_time(self):
        while True:
            parsed = parse_time(ask("Hora actual (hh:mm o hh:mm:ss): "))
            if parsed is not None:
                self.clock.set(*parsed)
                print("Reloj en " + self.clock.text())
                return
            print("Hora no valida.")

    def show_clock(self):
        clock = self.clock
        print(render_dial(clock.hour, clock.minute, clock.second))
        hour12 = clock.hour % 12 or 12
        suffix = "a.m." if clock.hour < 12 else "p.m."
        print()
        print("   " + clock.text() + "   (" + str(hour12) + ":" + two(clock.minute) + " " + suffix
              + ")   dia " + str(clock.days + 1))
        alarm, wait = self.alarms.next_after(clock.seconds_of_day())
        if alarm is not None:
            print("   Proxima alarma: " + two(alarm.hour) + ":" + two(alarm.minute)
                  + " (en " + format_seconds(wait) + ")")
        if self.timer.running:
            print("   Temporizador: " + format_seconds(self.timer.remaining))
        if self.stopwatch.running:
            print("   Cronometro: " + format_seconds(self.stopwatch.elapsed))

    def alarm_menu(self):
        while True:
            print()
            print("ALARMAS")
            if self.alarms.alarms.is_empty():
                print("  (no hay alarmas)")
            number = 1
            for alarm in self.alarms.alarms:
                print("  " + str(number) + ". " + alarm.text())
                number += 1
            print("a. Agregar   b. Borrar   c. Activar/desactivar   t. Avanzar tiempo   0. Volver")
            choice = ask("> ").lower()
            if choice == "0":
                return
            if choice == "a":
                parsed = parse_time(ask("Hora de la alarma (hh:mm): "))
                if parsed is None:
                    print("Hora no valida.")
                    continue
                label = ask("Nombre (opcional): ") or "Alarma"
                self.alarms.add(parsed[0], parsed[1], label)
            elif choice in ("b", "c"):
                total = len(self.alarms.alarms)
                if total == 0:
                    print("No hay alarmas.")
                    continue
                index = ask_int("Numero de alarma: ", 1, total)
                if index is None:
                    print("Numero no valido.")
                elif choice == "b":
                    self.alarms.remove(index - 1)
                else:
                    self.alarms.toggle(index - 1)
            elif choice == "t":
                self.ask_advance()
            else:
                print("Opcion no valida.")

    def stopwatch_menu(self):
        watch = self.stopwatch
        while True:
            print()
            state = "corriendo" if watch.running else "detenido"
            print("CRONOMETRO  " + format_seconds(watch.elapsed) + "  (" + state + ")")
            if not watch.laps.is_empty():
                fastest = min(watch.laps)
                slowest = max(watch.laps)
                number = 1
                for lap in watch.laps:
                    mark = ""
                    # Si todas las vueltas duran lo mismo no hay rapida ni lenta.
                    if fastest != slowest and lap == fastest:
                        mark = "  <- mas rapida"
                    elif fastest != slowest and lap == slowest:
                        mark = "  <- mas lenta"
                    print("  Vuelta " + str(number) + ": " + format_seconds(lap) + mark)
                    number += 1
            print("i. Iniciar/pausar   v. Vuelta   r. Reiniciar   t. Avanzar tiempo   0. Volver")
            choice = ask("> ").lower()
            if choice == "0":
                return
            if choice == "i":
                watch.running = not watch.running
            elif choice == "v":
                if watch.running:
                    watch.lap()
                else:
                    print("El cronometro esta detenido.")
            elif choice == "r":
                watch.reset()
            elif choice == "t":
                self.ask_advance()
            else:
                print("Opcion no valida.")

    def timer_menu(self):
        timer = self.timer
        while True:
            print()
            state = "corriendo" if timer.running else "detenido"
            print("TEMPORIZADOR  " + format_seconds(timer.remaining) + "  (" + state + ")")
            print("n. Nuevo   p. Pausar/continuar   c. Cancelar   t. Avanzar tiempo   0. Volver")
            choice = ask("> ").lower()
            if choice == "0":
                return
            if choice == "n":
                seconds = parse_duration(ask("Duracion (ej. 90, 5m, 1:00:00): "))
                if not seconds:
                    print("Duracion no valida.")
                else:
                    timer.start(seconds)
            elif choice == "p":
                timer.running = not timer.running and timer.remaining > 0
            elif choice == "c":
                timer.start(0)
            elif choice == "t":
                self.ask_advance()
            else:
                print("Opcion no valida.")

    def world_menu(self):
        world = self.world
        day_words = {-1: " (ayer)", 0: "", 1: " (manana)"}
        while True:
            now = self.clock.seconds_of_day()
            name, offset = world.cursor.value
            seconds, day = world.time_in(offset, now)
            print()
            print("RELOJ MUNDIAL   zona local: " + format_offset(world.local_offset))
            print(render_dial(seconds // 3600, seconds // 60 % 60, seconds % 60))
            print("   " + name + "  " + format_seconds(seconds) + day_words[day])
            print()
            for city, city_offset in world.cities:
                city_seconds, city_day = world.time_in(city_offset, now)
                pointer = ">" if city == name else " "
                print(" " + pointer + " " + (city + " " * 18)[:18] + format_seconds(city_seconds)
                      + "  " + format_offset(city_offset) + day_words[city_day])
            print("s. Siguiente   a. Anterior   z. Usar como zona local   t. Avanzar tiempo   0. Volver")
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
                print("Opcion no valida.")


if __name__ == "__main__":
    App().run()
