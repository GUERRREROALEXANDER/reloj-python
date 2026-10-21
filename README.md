# Reloj de consola

Reloj para el taller de estructuras de datos. Corre en la terminal y tiene esfera analógica dibujada con texto, alarmas, cronómetro, temporizador y reloj mundial.

**Regla del taller:** Python puro, sin librerías y sin ninguna importación. Ni `import math`, ni `import time`, ni módulos propios. Todo lo que el programa necesita está escrito en `reloj.py`.

## Por qué el reloj es simulado

Python no tiene funciones integradas (built-ins) para leer la hora del sistema ni para esperar un segundo. Eso está en los módulos `time` y `datetime`, que la regla no permite importar. Por eso:

1. Al iniciar, el programa pide la hora actual (`hh:mm` o `hh:mm:ss`).
2. El tiempo no corre solo: avanza cuando el usuario lo pide con la opción "Avanzar tiempo".

Formatos aceptados para avanzar (y para el temporizador):

| Entrada   | Significa             |
|-----------|-----------------------|
| `30`      | 30 segundos           |
| `90s`     | 90 segundos           |
| `5m`      | 5 minutos             |
| `2h`      | 2 horas               |
| `1:30:00` | 1 hora 30 minutos     |
| `5:00`    | 5 minutos (`mm:ss`)   |

Reglas de validación (función `is_digits`):

- Cada número debe tener solo dígitos 0-9. Se rechazan signos (`-5`, `+5`), guiones bajos (`1_0`) y decimales (`1.5`), aunque `int()` acepte algunos de ellos.
- En el formato con dos puntos, las partes después de la primera deben estar entre 0 y 59: `5:00` vale (5 minutos), `0:90` no.
- La hora (`hh:mm` o `hh:mm:ss`) sigue las mismas reglas, con horas de 0 a 23.
- Avanzar acepta como máximo 366 días por vez (constante `MAX_ADVANCE`); si se pide más, muestra `Maximo 366 dias por vez.` y no avanza.
- El temporizador no acepta una duración de cero.

Al avanzar, el reloj da un "tick" por cada segundo, así que alarmas, cronómetro y temporizador se actualizan igual que si el tiempo hubiera pasado de verdad.

## Archivos

| Archivo      | Contenido |
|--------------|-----------|
| `reloj.py`   | El programa completo: estructuras de datos, matemática, lógica del reloj y menú de consola. |
| `pruebas.py` | Pruebas sin imports. Carga `reloj.py` con `open` + `exec` (en lugar de `import`) y revisa las estructuras y las funciones. |

## Cómo ejecutarlo

Requiere Python 3. No hay nada que instalar.

```
python reloj.py
```

Para correr las pruebas:

```
python pruebas.py
```

Como el programa lee todo con `input()`, también se le pueden pasar los comandos por la entrada estándar. En PowerShell:

```powershell
"10:08:30`n1`n0`n" | python reloj.py
```

Eso ajusta la hora a 10:08:30, muestra el reloj (opción 1) y sale (opción 0).

Si la entrada se acaba antes de elegir `0`, o se presiona Ctrl+C, el programa sale sin traza de error y muestra `Hasta luego.`.

## Menú

```
1. Ver reloj        2. Ajustar hora     3. Avanzar tiempo
4. Alarmas          5. Cronometro       6. Temporizador
7. Reloj mundial    0. Salir
```

| Opción | Qué hace |
|--------|----------|
| 1. Ver reloj | Dibuja la esfera analógica, muestra la hora en 24 h y 12 h, el día, la próxima alarma y el estado del cronómetro y el temporizador si están corriendo. |
| 2. Ajustar hora | Pone el reloj en otra hora. Repite la pregunta hasta recibir una hora válida. |
| 3. Avanzar tiempo | Hace pasar el tiempo (ver formatos arriba, máximo 366 días) y muestra los avisos que se hayan disparado. |
| 4. Alarmas | Agregar (hora y nombre), borrar y activar/desactivar alarmas. Se listan ordenadas por hora. |
| 5. Cronómetro | Iniciar/pausar, marcar vueltas (solo con el cronómetro corriendo) y reiniciar. Marca la vuelta más rápida y la más lenta solo si duran distinto; si todas son iguales no marca ninguna. |
| 6. Temporizador | Cuenta regresiva: nuevo, pausar/continuar y cancelar. Avisa al llegar a cero. |
| 7. Reloj mundial | Hora en 9 ciudades, con la esfera de la ciudad seleccionada. Se recorre con siguiente/anterior y cualquier ciudad se puede usar como zona local. Indica si allá es ayer o mañana. |

Los submenús 4 a 7 tienen la opción `t` para avanzar el tiempo sin salir de ellos.

### Ejemplo de la esfera

Salida real de `"10:08:30`n1`n0`n" | python reloj.py`:

```
              . . . + . . .
          + .               . +
        .          12           .
     . .   11               1    . .
    .                               .
   +                                 +
  .  10                      *    2   .
 .           #            ****         .
.            ###        **              .
.               ###   **                .
+   9               O               3   +
.                   :                   .
.                   :                   .
 .                  :                  .
  .   8             :             4   .
   +                :                +
    .               :               .
     . .    7       :       5    . .
        .           6           .
          + .               . +
              . . . + . . .

   10:08:30   (10:08 a.m.)   dia 1
```

| Símbolo | Significado |
|---------|-------------|
| `#` | Horario |
| `*` | Minutero |
| `:` | Segundero |
| `O` | Centro |
| `+` / `.` | Marcas de cada 5 minutos / de cada minuto |

Los caracteres de la consola son más altos que anchos, así que la coordenada x se multiplica por 2 para que la esfera se vea redonda.

Los números están en el radio `r - 2` (con `r = DIAL_RADIUS = 10`). Las manecillas son más cortas para no taparlos: segundero `r * 0.7`, minutero `r * 0.6`, horario `r * 0.45`.

## Estructuras de datos

Las tres están implementadas a mano en `reloj.py`; no se usan `collections.deque` ni nada parecido.

### `CircularDoublyLinkedList` (lista circular doblemente enlazada)

Cada `Node` apunta a su anterior y a su siguiente; el último apunta al primero y el primero al último. Recorrerla nunca llega a un final, que es justo lo que pasa con las horas de un reloj: después del 59 viene el 0.

| Operación | Complejidad |
|-----------|-------------|
| `append`, `prepend` | O(1) |
| `insert_after(nodo, valor)` | O(1) |
| `remove_node(nodo)`, `pop_front` | O(1) |
| `insert_sorted` | O(n) |
| `node_at(i)` | O(n), camina por el lado más corto (a lo sumo n/2 pasos) |
| Recorrido completo | O(n) |

### `RingCursor`

Puntero sobre una lista circular que avanza (`forward`) o retrocede (`backward`) siguiendo los enlaces. `seek` busca un valor en las dos direcciones a la vez.

- Un paso negativo mueve en sentido contrario: `forward(-2)` equivale a `backward(2)`.
- Si el cursor se creó con la lista vacía, o su nodo fue borrado de la lista, vuelve a la cabeza antes de moverse.
- Con la lista vacía, `value`, `forward` y `backward` lanzan `IndexError`, y `seek` devuelve `False`.

| Operación | Complejidad |
|-----------|-------------|
| `value` | O(1) |
| `forward(k)`, `backward(k)` | O(k) |
| `seek` | O(n), a lo sumo n/2 + 1 pasos |

### `LinkedQueue`

Cola FIFO construida sobre la lista circular: encola con `append` y desencola con `pop_front`.

| Operación | Complejidad |
|-----------|-------------|
| `enqueue`, `dequeue`, `is_empty` | O(1) |

### Dónde se usa cada una

| Uso | Estructura | Detalle |
|-----|------------|---------|
| Hora del reloj (`Clock`) | 3 listas circulares (24 horas, 60 minutos, 60 segundos) + 3 `RingCursor` | Cada manecilla es un cursor. `tick` mueve el segundero un nodo; si vuelve a 0, arrastra al minutero, y este al horario (acarreo, como engranajes). Si el horario vuelve a 0, suma un día. Un tick es O(1). Ajustar la hora usa `seek`; `Clock.set` valida primero y lanza `ValueError` si la hora está fuera de rango, así el reloj nunca queda a medio ajustar. |
| Alarmas (`AlarmManager`) | Lista circular ordenada | `insert_sorted` por hora y minuto, así el listado sale ordenado sin ordenar aparte. Borrar y activar usan `node_at`. |
| Vueltas del cronómetro (`Stopwatch`) | Lista circular | Cada vuelta se agrega con `append` en O(1). |
| Ciudades (`WorldClock`) | Lista circular + `RingCursor` | "Siguiente" desde la última ciudad vuelve a la primera, y "anterior" desde la primera va a la última, sin casos especiales. |
| Notificaciones (`App`) | `LinkedQueue` | Alarmas y fin del temporizador se encolan mientras avanza el tiempo y se muestran en orden de llegada al terminar. |
| Marcas de la esfera | Lista circular de 60 posiciones | Se recorre para dibujar las marcas de minuto. |

Avanzar `s` segundos cuesta O(s) en ticks, más una revisión de las alarmas cada vez que cambia el minuto.

## Hecho a mano en vez de usar librerías

| Necesidad | Normalmente | Aquí |
|-----------|-------------|------|
| Seno y coseno para ubicar números y manecillas | `math.sin`, `math.cos` | `sin(x)` por serie de Taylor (11 términos) después de llevar `x` al rango [-π, π]; `cos(x) = sin(x + π/2)`. `PI` está escrito como constante. |
| Formato `hh:mm:ss` y `UTC-5` | `time.strftime`, f-strings con `:02d` | `two(n)` rellena con un cero; `format_seconds` y `format_offset` arman el texto con divisiones enteras y módulo. |
| Leer horas (`7:30`, `07:30:15`) | `datetime.strptime` | `parse_time`: separa por `:`, revisa cada parte con `is_digits`, convierte con `int` y valida rangos. |
| Leer duraciones (`90`, `5m`, `1:30:00`) | `re` o `datetime.timedelta` | `parse_duration`: revisa el sufijo `h`/`m`/`s` o acumula partes separadas por `:` (las que siguen a la primera, de 0 a 59). Cada número pasa por `is_digits`. |
| Validar que un texto sea un número | `str.isdigit` acepta otros dígitos Unicode; `int` acepta signos y `_` | `is_digits`: compara cada carácter con el rango `"0"`-`"9"`. |
| Hora en otra zona | `zoneinfo` | `WorldClock.time_in`: suma la diferencia de desfase en segundos y usa `%` y `//` para obtener la hora y si es ayer o mañana. |
| Cargar el programa en las pruebas | `import reloj` | `pruebas.py` lee el archivo con `open` y lo ejecuta con `exec`. |
| Correr las pruebas | `unittest`, `pytest` | Corredor propio en `pruebas.py` (ver abajo). |

## Pruebas

`pruebas.py` tiene 62 pruebas y no usa `unittest` ni `pytest`:

- Lee `reloj.py` con `open` y lo ejecuta con `exec` en un diccionario propio con `__name__ = "reloj"`, así el menú no arranca.
- Reemplaza `print` dentro de ese diccionario para que `App.advance` no escriba durante las pruebas.
- El corredor busca todas las funciones que empiezan con `prueba_`, imprime `OK` o `FALLA` por cada una y al final un resumen. Si hay fallas, termina con código de salida 1.

| Grupo | Qué revisa |
|-------|------------|
| `CircularDoublyLinkedList` | `append`, `prepend`, `insert_sorted` (orden y estabilidad), `remove_node`, `node_at` con índices negativos y mayores que el tamaño, circularidad de `next`/`prev`, `IndexError` en lista vacía. |
| `RingCursor` | Avanzar y retroceder dando la vuelta, `seek` en ambas direcciones y en listas de varios tamaños, valor no encontrado, lista vacía. |
| `LinkedQueue` | Orden FIFO e `IndexError` al desencolar vacía. |
| `sin` / `cos` | Valores conocidos y `sin² + cos² = 1`. |
| `Clock` | `set`, `tick`, acarreo de 59 a 0, medianoche y varios días seguidos. |
| `render_dial` | Tamaño de la esfera, centro `O`, marcas y números visibles, dirección del segundero. |
| Funciones | Alarmas (orden, disparo, activar/desactivar, borrar, próxima alarma), cronómetro, temporizador y reloj mundial (media hora, ayer y mañana, recorrido de ciudades). |
| Lectura de datos | `parse_time` y `parse_duration` con entradas válidas e inválidas, incluidas partes negativas. |
| `App.advance` | Hora y cronómetro, alarmas y temporizador en la cola, alarma a medianoche y orden FIFO de los avisos. |

Resumen real de `python pruebas.py` (después de una línea `OK` por prueba):

```
62 pruebas, 0 fallas
```

## Limitaciones

- **Hora simulada.** El reloj no sabe la hora real ni avanza solo; hay que ajustarlo al iniciar y hacerlo avanzar con comandos. Sin `time` no hay forma de leer el reloj del sistema ni de esperar.
- **Sin horario de verano.** El reloj mundial usa los desfases estándar fijos (Nueva York UTC-5, Londres UTC+0, Madrid UTC+1, Sidney UTC+10, etc.). En las fechas en que esas ciudades aplican horario de verano, la hora mostrada queda una hora atrás. Tampoco hay calendario: solo se cuenta el número de día.
- **Zona local inicial fija.** Se asume UTC-5 (Bogotá) hasta que se elija otra ciudad con `z`.
- **Avanzar mucho tiempo tarda.** Se simula segundo a segundo: un día son 86 400 ticks. En una medición con Python 3.13 en Windows 11, avanzar un día tomó cerca de 0,03 s, 100 días unos 3 s y 366 días unos 12 s. Por eso cada avance está limitado a 366 días (`MAX_ADVANCE`); sin ese límite, algo como `99999h` dejaría el programa ocupado varios minutos.
