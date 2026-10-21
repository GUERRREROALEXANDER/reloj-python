# Reloj de consola

Reloj para el taller de estructuras de datos. Corre en la terminal y tiene esfera analógica de alta resolución, hora digital grande, colores, modo en vivo, alarmas, cronómetro, temporizador y reloj mundial.

## Regla del proyecto

**Python puro, sin librerías, sin dependencias y sin ninguna importación.**

- No hay `import` en ningún archivo: ni `math`, ni `time`, ni `sys`, ni `os`, ni módulos propios.
- No hay nada que instalar (`pip`, `requirements.txt`, entornos virtuales): no hace falta.
- Todo lo que el programa necesita está escrito en `reloj.py`, y se ejecuta solo con:

```
python reloj.py
```

### Cómo se logra cada efecto sin librerías

| Efecto | Cómo se hace |
|--------|--------------|
| Esfera con bloques | Texto impreso con `print`: cada carácter `▀`, `▄` o `█` muestra dos "píxeles" (arriba y abajo). La clase `PixelCanvas` arma la matriz y la convierte en líneas de texto. |
| Colores, borrar pantalla, mover el cursor | Códigos de escape ANSI, que también son texto: `"\x1b[" + parámetros + letra`, impresos con `print`. |
| Ubicar números y manecillas | `sin` y `cos` escritos a mano (serie de Taylor); `PI` es una constante en el código. Las líneas se trazan con el algoritmo de Bresenham (solo sumas y restas de enteros). |
| Hora digital grande | Dígitos de 7 segmentos definidos en el código (diccionario `SEGMENTS`) y dibujados en un `PixelCanvas`. |
| Esperar un segundo | Un ciclo vacío (`for _ in range(n): pass`) de `LOOPS_PER_SECOND` vueltas. Sin `time` no se puede medir el tiempo real, así que el valor se calibra desde el menú. |
| Saber si la salida es una consola | La función integrada `open(fd, ..., closefd=False).isatty()` sobre el descriptor 0 (teclado) y 1 (pantalla). |
| No caerse si la salida no acepta Unicode | `show` captura `UnicodeEncodeError` y repite el texto en ASCII (`#`, `"`, `.`, `+`, `-`, `|`). |
| Cargar el programa en las pruebas | `pruebas.py` lee `reloj.py` con `open` y lo ejecuta con `exec`, en lugar de `import reloj`. |

## Por qué el reloj es simulado

Python no tiene funciones integradas para leer la hora del sistema. Eso está en `time` y `datetime`, que la regla no permite importar. Por eso:

1. Al iniciar, el programa pide la hora actual (`hh:mm` o `hh:mm:ss`).
2. Apenas se escribe la hora arranca el **modo en vivo**: el reloj avanza solo, un segundo a la vez. Ctrl+C lo detiene y lleva al menú.
3. Desde el menú, el tiempo también se puede adelantar a mano con "Avanzar tiempo".

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
| `reloj.py`   | El programa completo: estructuras de datos, matemática, lienzo de píxeles, pantalla, lógica del reloj y menú de consola. |
| `pruebas.py` | Pruebas sin imports. Carga `reloj.py` con `open` + `exec` y revisa las estructuras y las funciones. |

## Cómo ejecutarlo

Requiere Python 3. No hay nada que instalar.

```
python reloj.py
```

**Consola recomendada: Windows Terminal.** Muestra bien los bloques, los marcos y los colores de 256. Si en otra consola aparecen códigos raros como `[0m` o `[2J`, apaga "Colores" y "Pantalla limpia" en Ajustes (opción 9); si aparecen `?` en lugar de bloques, apaga "Unicode".

Como el programa lee todo con `input()`, también se le pueden pasar los comandos por la entrada estándar. En PowerShell:

```powershell
"10:08:30`n1`n`n0`n" | python reloj.py
```

Eso ajusta la hora a 10:08:30, muestra el reloj (opción 1), vuelve al menú (Enter) y sale (opción 0). Cuando la entrada viene de una tubería el modo en vivo no arranca solo, porque nadie podría detenerlo con Ctrl+C. Cuando la salida va a un archivo o tubería, se apagan los códigos ANSI; si además esa salida no acepta Unicode (en Windows suele ser cp1252), todo pasa a ASCII.

Si la entrada se acaba antes de elegir `0`, o se presiona Ctrl+C en una pregunta, el programa sale sin traza de error, deja el cursor visible y muestra `Hasta luego.`.

## Menú

```
╔══════════════════════════════════════════════════════════════════╗
║  RELOJ DE CONSOLA                               10:08:30  Dia 1  ║
╟──────────────────────────────────────────────────────────────────╢
║  8  Modo en vivo: el reloj anda solo (Ctrl+C vuelve aqui).       ║
╟──────────────────────────────────────────────────────────────────╢
║  1  Ver reloj         2  Ajustar hora      3  Avanzar tiempo     ║
║  4  Alarmas           5  Cronometro        6  Temporizador       ║
║  7  Reloj mundial     8  Modo en vivo      9  Ajustes            ║
║  0  Salir                                                        ║
╚══════════════════════════════════════════════════════════════════╝
```

| Opción | Qué hace |
|--------|----------|
| 1. Ver reloj | Muestra la esfera, la hora digital grande, la hora en 12 h, el día de la semana, la próxima alarma y el estado del cronómetro y el temporizador si están corriendo. En esa pantalla se puede escribir directamente la siguiente opción del menú. |
| 2. Ajustar hora | Pone el reloj en otra hora. Repite la pregunta hasta recibir una hora válida. |
| 3. Avanzar tiempo | Hace pasar el tiempo (ver formatos arriba, máximo 366 días) y muestra los avisos que se hayan disparado. |
| 4. Alarmas | Agregar (hora y nombre), borrar y activar/desactivar alarmas. Se listan ordenadas por hora. |
| 5. Cronómetro | Iniciar/pausar, marcar vueltas (solo con el cronómetro corriendo) y reiniciar. Marca la vuelta más rápida y la más lenta solo si duran distinto. |
| 6. Temporizador | Cuenta regresiva: nuevo, pausar/continuar y cancelar. Avisa al llegar a cero. |
| 7. Reloj mundial | Hora en 9 ciudades, con la esfera de la ciudad seleccionada al lado de la lista. Se recorre con siguiente/anterior y cualquier ciudad se puede usar como zona local. Indica si allá es ayer o mañana. |
| 8. Modo en vivo | El reloj anda solo, segundo a segundo, hasta presionar Ctrl+C (ver abajo). |
| 9. Ajustes | Colores, ANSI, Unicode y calibrar el reloj (ver abajo). |
| 0. Salir | Restaura la consola y termina. |

Los submenús 4 a 7 tienen la opción `t` para avanzar el tiempo sin salir de ellos. Todas las pantallas van dentro de un marco de línea doble con el título y la hora actual arriba a la derecha.

## Modo en vivo

- Arranca solo después de escribir la hora al iniciar, y también con la opción 8.
- Cada segundo redibuja la pantalla en el mismo lugar (lleva el cursor arriba con ANSI en vez de borrar todo, así no parpadea), espera con el ciclo vacío y avanza el reloj un tick.
- Alarmas, cronómetro y temporizador siguen funcionando. Un aviso aparece en una franja roja durante 10 segundos (`ALERT_SECONDS`), el bisel de la esfera parpadea en rojo y la consola suena (carácter campana `\a`).
- **Ctrl+C** vuelve al menú; el reloj conserva la hora a la que llegó.

### Calibrar el reloj

El segundo del modo en vivo es un ciclo vacío de `LOOPS_PER_SECOND` vueltas (97 000 000 por defecto, medido con Python 3.13 en Windows 11). Cada computador es distinto, así que puede adelantarse o atrasarse. Se corrige en **Ajustes > `v` Calibrar reloj**:

| Tecla | Qué hace |
|-------|----------|
| `p` | Prueba de 10 s: la pantalla cuenta de 10 a 0 dibujando la esfera completa (igual que el modo en vivo). Se mide con el cronómetro del celular, se escribe cuánto tardó (por ejemplo `11.5` o `11,5`) y el programa corrige solo: nuevo valor = actual × 10 / medido. |
| `+` | El reloj va adelantado: alarga el segundo un 5 %. |
| `-` | El reloj va atrasado: acorta el segundo un 5 %. |
| `e` | Escribir el valor a mano (de 1000 a 9 999 999 999 ciclos por segundo). |

El valor calibrado dura mientras el programa está abierto; no se guarda en disco. Para dejarlo fijo, cambia la constante `LOOPS_PER_SECOND` en `reloj.py`.

## Ajustes

| Tecla | Ajuste | Para qué |
|-------|--------|----------|
| `c` | Colores ANSI | Colores de 256 de la esfera, los dígitos y los marcos. |
| `l` | Pantalla limpia (ANSI) | Borrar la pantalla y mover el cursor con códigos ANSI. Apagado, cada pantalla se imprime debajo de la anterior. |
| `u` | Esfera Unicode | Bloques y marcos Unicode. Apagado, usa la esfera ASCII y los dígitos con `_` y `\|`. |
| `v` | Calibrar reloj | Ver la sección anterior. |

Si la salida no acepta Unicode, el programa apaga solo los tres primeros (`Display.use_ascii`).

## La esfera

### Ejemplo

Salida real de `render_face(10, 8, 30)` y `render_big_time("10:08:30")`, sin colores:

```
             ▄▄▄█████████▄▄▄
         ▄▄██▀▀▀▄ ▄▄█▄▄ ▄▀▀▀██▄▄
       ▄██▀▄ ▀     ▀█▀     ▀ ▄▀██▄
     ▄█▀▄ ▀▀▄      12       ▄▀▀ ▄▀█▄
   ▄██ ▀    11            1      ▀ ██▄
  ▄█▀▄▀                           ▀▄▀█▄
 ▄█▀▄  ▀10                  ▄█▄  ▀  ▄▀▀▄
 ██▄         ▄▄▄    ▄    ▄███▀ 2     ▄██
██ ▀         █████▄▀█▀▄▄██▀▀         ▀ ██
██ ▀▄         ▀▀███▀▀▀██▀           ▄▀ ██
██▀██▀9          ▀▀█▀█           3 ▀█▀ ██
██ ▀                █                ▀ ██
▀█▄█                █                █▄█▀
 ██ ▄   8      PYTHO█ PURO     4    ▄ ██
  ██ ▄▄▀            █            ▀▄▄ ██
   ██▄▀      7      █     5       ▀▄██
    ▀█▄▀▄   ▄      6█       ▄   ▄▀▄█▀
      ▀█▄▄▀█        █        █▀▄▄█▀
        ▀██▄▄▀ ▄▄ ▄▀▀▀▄ ▄▄ ▀▄▄██▀
           ▀▀███▄▄▄▄▄▄▄▄▄███▀▀
                ▀▀▀▀▀▀▀▀▀

    ██  ██████      ██████  ██████      ██████  ██████
    ██  ██  ██  ██  ██  ██  ██  ██  ██      ██  ██  ██
    ██  ██  ██      ██  ██  ██████      ██████  ██  ██
    ██  ██  ██  ██  ██  ██  ██  ██  ██      ██  ██  ██
    ██  ██████      ██████  ██████      ██████  ██████
```

Con colores, el bisel es dorado (más claro arriba a la izquierda y más oscuro abajo a la derecha), el fondo es gris oscuro, el horario blanco, el minutero azul acero, el segundero rojo y los dígitos ámbar. El rótulo `PYTHON PURO` queda debajo de las manecillas: aquí el segundero lo cruza.

### Cómo se dibuja

- **Píxeles cuadrados.** Un carácter de consola es casi el doble de alto que de ancho, así que cada carácter muestra dos píxeles con medios bloques. La esfera mide 41 × 41 píxeles = 41 columnas × 21 líneas, y sale redonda.
- **Capas.** Fondo y bisel (anillo entre los radios 18.5 y 20.5), marcas (punto por minuto, raya por hora, raya gruesa dorada en 12, 3, 6 y 9), manecillas, eje central y, al final, los números como letras encima, para que nada los tape.
- **Manecillas.** Líneas de Bresenham con pinceles de distinto grosor: horario 3 × 3 (largo 7.5), minutero en cruz (largo 11), segundero fino (largo 15.5, con cola y contrapeso). El horario y el minutero avanzan de forma continua: a las 10:30 el horario está a mitad de camino entre el 10 y el 11.
- **Hora grande.** Cada dígito es un rectángulo de 6 × 10 píxeles (5 líneas) con trazos de 2 píxeles de grueso.

### Respaldo ASCII

Cuando Unicode está apagado se usa la esfera original `render_dial` (`+`/`.` marcas, `#` horario, `*` minutero, `:` segundero, `O` centro), con la x multiplicada por 2 para que se vea redonda, y los dígitos de 3 líneas de `render_big_time_ascii`:

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

     _     _   _     _   _
  | | | . | | |_| .  _| | |
  | |_| . |_| |_| .  _| |_|
```

## Estructuras de datos

Están implementadas a mano en `reloj.py`; no se usan `collections.deque` ni nada parecido.

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

### `PixelCanvas` (matriz de píxeles)

Lista de listas de `alto × ancho`; cada celda guarda un color o `None` (vacío).

| Operación | Complejidad |
|-----------|-------------|
| `plot`, `get` | O(1), ignora puntos fuera del lienzo |
| `line` (Bresenham) | O(largo × tamaño del pincel) |
| `disc` | O(r²) |
| `to_text` | O(ancho × alto): junta dos filas de píxeles en una línea de texto y solo emite un código de color cuando el color cambia |

### `Display` (ajustes de pantalla)

Objeto único `DISPLAY` con cuatro campos: `color`, `ansi`, `unicode` y `loops_per_second`. Todas las funciones de dibujo lo consultan: `paint` no pinta si `color` está apagado, `clear_screen` no usa ANSI si `ansi` está apagado, `draw_face` elige entre `render_face` y `render_dial` según `unicode`, y `wait_one_second` usa `loops_per_second`.

### Dónde se usa cada una

| Uso | Estructura | Detalle |
|-----|------------|---------|
| Hora del reloj (`Clock`) | 3 listas circulares (24 horas, 60 minutos, 60 segundos) + 3 `RingCursor` | Cada manecilla es un cursor. `tick` mueve el segundero un nodo; si vuelve a 0, arrastra al minutero, y este al horario (acarreo, como engranajes). Si el horario vuelve a 0, suma un día. Un tick es O(1). Ajustar la hora usa `seek`; `Clock.set` valida primero y lanza `ValueError` si la hora está fuera de rango, así el reloj nunca queda a medio ajustar. |
| Alarmas (`AlarmManager`) | Lista circular ordenada | `insert_sorted` por hora y minuto, así el listado sale ordenado sin ordenar aparte. Borrar y activar usan `node_at`. |
| Vueltas del cronómetro (`Stopwatch`) | Lista circular | Cada vuelta se agrega con `append` en O(1). |
| Ciudades (`WorldClock`) | Lista circular + `RingCursor` | "Siguiente" desde la última ciudad vuelve a la primera, y "anterior" desde la primera va a la última, sin casos especiales. |
| Notificaciones (`App`) | `LinkedQueue` | Alarmas y fin del temporizador se encolan con cada tick y se muestran en orden de llegada. |
| Marcas de la esfera | Lista circular de 60 posiciones | Se recorre para dibujar las marcas de minuto. |
| Esfera y dígitos grandes | `PixelCanvas` | Se dibuja en píxeles y se imprime como texto. |

Avanzar `s` segundos cuesta O(s) en ticks, más una revisión de las alarmas cada vez que cambia el minuto.

## Hecho a mano en vez de usar librerías

| Necesidad | Normalmente | Aquí |
|-----------|-------------|------|
| Seno y coseno | `math.sin`, `math.cos` | `sin(x)` por serie de Taylor (11 términos) después de llevar `x` al rango [-π, π]; `cos(x) = sin(x + π/2)`. `PI` está escrito como constante. |
| Esperar un segundo | `time.sleep(1)` | `wait_one_second`: ciclo vacío de `DISPLAY.loops_per_second` vueltas, calibrable desde Ajustes. |
| Colores y control de la pantalla | `colorama`, `curses`, `os.system("cls")` | Códigos ANSI como texto (`style_code`, `paint`, `CLEAR_SCREEN`, `CURSOR_HOME`). `strip_ansi` los quita y `visible_len` mide el texto sin ellos para alinear los marcos. |
| Saber si la salida es una consola | `sys.stdout.isatty()` | `is_terminal`: `open(fd, modo, buffering=0, closefd=False).isatty()`. |
| Salida segura sin Unicode | `sys.stdout.reconfigure(encoding=...)` | `show`: captura `UnicodeEncodeError` y repite el texto con `to_ascii`. |
| Dibujar líneas y círculos | `PIL`, `turtle` | `PixelCanvas.line` (Bresenham) y `PixelCanvas.disc`. |
| Formato `hh:mm:ss` y `UTC-5` | `time.strftime`, f-strings con `:02d` | `two(n)` rellena con un cero; `format_seconds` y `format_offset` arman el texto con divisiones enteras y módulo. |
| Leer horas (`7:30`, `07:30:15`) | `datetime.strptime` | `parse_time`: separa por `:`, revisa cada parte con `is_digits`, convierte con `int` y valida rangos. |
| Leer duraciones (`90`, `5m`, `1:30:00`) | `re` o `datetime.timedelta` | `parse_duration`: revisa el sufijo `h`/`m`/`s` o acumula partes separadas por `:` (las que siguen a la primera, de 0 a 59). |
| Leer decimales (`11.5`, `11,5`) | `float()` directo | `parse_decimal`: acepta punto o coma y valida cada parte con `is_digits`. |
| Validar que un texto sea un número | `str.isdigit` acepta otros dígitos Unicode; `int` acepta signos y `_` | `is_digits`: compara cada carácter con el rango `"0"`-`"9"`. |
| Hora en otra zona | `zoneinfo` | `WorldClock.time_in`: suma la diferencia de desfase en segundos y usa `%` y `//` para obtener la hora y si es ayer o mañana. |
| Correr las pruebas | `unittest`, `pytest` | Corredor propio en `pruebas.py` (ver abajo). |

## Pruebas

```
python pruebas.py
```

`pruebas.py` no usa `unittest`, `pytest` ni ningún `import`:

- Lee `reloj.py` con `open` y lo ejecuta con `exec` en un diccionario propio con `__name__ = "reloj"`, así el menú no arranca.
- Reemplaza `print` dentro de ese diccionario para que el programa no escriba durante las pruebas.
- El corredor busca todas las funciones que empiezan con `prueba_`, imprime `OK` o `FALLA` por cada una y al final un resumen con el total de pruebas y de fallas. Si hay fallas, termina con código de salida 1.

Cubren, en general:

- Las estructuras de datos (lista circular, cursor, cola): operaciones, circularidad y casos de lista vacía.
- La matemática propia (`sin`, `cos`) y el formato de horas.
- El reloj (`Clock`): ajuste, ticks, acarreo y cambio de día.
- El dibujo: esfera ASCII y de alta resolución, lienzo de píxeles y dígitos grandes.
- Alarmas, cronómetro, temporizador y reloj mundial.
- La lectura de datos (`parse_time`, `parse_duration` y similares) con entradas válidas e inválidas.
- `App`: avance del tiempo, avisos en la cola y su orden.

## Limitaciones

- **Hora simulada.** El reloj no sabe la hora real; hay que ajustarlo al iniciar. Sin `time` no hay forma de leer el reloj del sistema.
- **El modo en vivo no es exacto.** El segundo es un ciclo vacío, así que depende de la velocidad del computador, de lo que esté haciendo en ese momento y de cuánto tarde en dibujar la consola. Aun calibrado puede adelantarse o atrasarse algunos segundos por hora. La calibración no se guarda al salir.
- **Uso de CPU en el modo en vivo.** Mientras el reloj anda, el ciclo de espera mantiene un núcleo del procesador al 100 %. Es el costo de esperar sin `time.sleep`. En el menú no pasa, porque `input()` espera sin gastar CPU.
- **Depende de la consola.** Los bloques, los marcos y los colores de 256 se ven bien en Windows Terminal. En consolas viejas pueden verse códigos como `[0m` o signos `?`; se arreglan apagando colores, ANSI o Unicode en Ajustes. La pantalla del reloj ocupa 29 líneas y 68 columnas, así que la consola debe medir al menos 80 × 30.
- **Sin horario de verano.** El reloj mundial usa los desfases estándar fijos (Nueva York UTC-5, Londres UTC+0, Madrid UTC+1, Sidney UTC+10, etc.). En las fechas en que esas ciudades aplican horario de verano, la hora mostrada queda una hora atrás. Tampoco hay calendario: solo se cuenta el número de día y un día de la semana que empieza en lunes.
- **Zona local inicial fija.** Se asume UTC-5 (Bogotá) hasta que se elija otra ciudad con `z`.
- **Avanzar mucho tiempo tarda.** Se simula segundo a segundo: un día son 86 400 ticks. En una medición con Python 3.13 en Windows 11, avanzar un día tomó cerca de 0,03 s, 100 días unos 3 s y 366 días unos 12 s. Por eso cada avance está limitado a 366 días (`MAX_ADVANCE`).
