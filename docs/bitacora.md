# Bitacora: ROG Ally con look PS5

Proyecto: llevar el modo juego de Bazzite en la ROG Ally (Z1 Extreme) al estilo del concepto
"PlayStation 5 User Interface Concept" (Dribbble 10863887, video de referencia en este folder).
Se documenta paso a paso para un video y un reel.

## Equipo

- ROG Ally RC71L, Bazzite (Fedora 44), kernel 7.2.11-ogc4.1, pantalla 1920x1080.
- Acceso por SSH desde la red local.
- Capturas del modo juego: `gamescopectl screenshot <ruta>` por SSH
  (con `XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=gamescope-0`). Sale PNG 1920x1080
  sin tocar la pantalla del Ally.

## 2026-10-26 — Punto de partida

Captura: `capturas/01-home-original.png` (home del modo juego, sin modificar).

Como esta el home hoy:
- Arte del juego seleccionado a pantalla completa (Clair Obscur: Expedition 33).
- Titulo y "PLAYTIME: 35.5 HRS" encima de la fila.
- Fila de recientes abajo con caratulas verticales (portrait); a la izquierda un bloque azul
  "Moonlight" (acceso no-Steam sin arte).
- Barra superior: busqueda, almacenamiento, notificaciones, wifi, bateria, hora, avatar.
- Leyenda de botones abajo: MENU / OPTIONS / SELECT / BACK.

Diferencias contra el concepto PS5:
- Caratulas: verticales y grandes -> cuadradas, mas chicas, marco blanco en la seleccionada.
- Fila: ocupa todo el borde inferior -> flotando a media altura sobre el arte.
- Arriba: no hay pestañas de categorias (ALL / RACING / ...); la barra va a la derecha y en
  el concepto se reparte (hora/wifi a la izquierda, perfil a la derecha).
- Tipografia: Steam usa su sans; el concepto usa sans fina con titulos grandes.
- El bloque "Moonlight" sin arte rompe la fila: ponerle arte en Steam.

Nota: a las 20:50 todos los plugins de Decky (CSS Loader, SteamGridDB, ProtonDB Badges) se
desinstalaron desde el propio Ally; Decky sigue activo. Quedan temas viejos en
~/homebrew/themes (Mini Carousel, Switch Like Home...) sin cargar.

## Como trabajamos el tema

Sin plugins: el cliente de Steam tiene la depuracion remota de CEF activa
(`~/.steam/steam/.cef-enable-remote-debugging`, puerto 8080 local del Ally). Desde la maquina de desarrollo:
- tunel: `ssh -f -N -L 18080:127.0.0.1:8080 <usuario>@<ally-tailnet-ip>`
- `tools/cdp.mjs`: evalua JS en la pestaña "Steam Big Picture Mode" (la del modo juego).
- `tools/inject.sh <nombre> [captura]`: mete `theme/<nombre>.css` como `<style id="ps5-<nombre>">`
  y saca captura. Re-inyectar reemplaza el estilo, asi se itera en vivo.
- `tools/shot.sh <nombre>`: solo captura.
Lo inyectado se pierde si Steam se reinicia. Para dejarlo fijo: empaquetar como tema de CSS Loader.

Dato util: la ventana de Steam mide 902x508 px CSS con devicePixelRatio 2.13 (= 1920x1080).
Las clases de Steam estan ofuscadas (`_1pwP4eeP1zQD7PEgmsep0W`); pueden cambiar con updates.

## Paso 1 — Caratulas cuadradas

Archivo: `theme/home-cuadros.css`. Captura: `capturas/02-home-cuadros.png`.

Que hace: en las celdas de la fila de recientes que tienen caratula vertical
(`library_600x900` o `library_capsule`), pone 1:1 la caratula y sus capas (fondo, overlay de
insignias) y recorta la imagen con `object-fit: cover`, anclada arriba para no cortar el logo.
Moonlight (sin arte) no se toca.

Iteraciones (en `capturas/pruebas/`):
1. aspect-ratio solo en la celda: no cambio nada visible, la imagen va en absoluto con alto fijo.
2. con `:has()` y alto 100% en el wrapper: la celda medía 94x94 pero la imagen seguia en 141.
3. `inset:0` en el wrapper: el contenedor de referencia no era la celda, siguio igual.
4. aspect-ratio en la imagen misma: cuadrados, pero quedaba debajo el fondo oscuro de 2:3 y un
   juego (Sephiria, `library_capsule`) no entraba en el selector.
5. aspect-ratio en las cuatro capas y ambos tipos de caratula: limpio. Esta es la buena.

Pendiente de este paso: los cuadros quedan arriba de una celda 2:3, con una franja vacia
debajo. Lo resuelve el paso siguiente (fila mas chica y flotando sobre el arte, como el PS5).

## Paso 2 — Seleccionado sin bloque azul y arte a pantalla completa

Archivos: `theme/home-cuadros.css` (corregido), `theme/home-hero.css`.
Captura: `capturas/03-home-cuadros-hero-completo.png` (pruebas: `pruebas/estado-6`, `hero-1`, `hero-2`).

Lo que se vio en el paso 1: el juego seleccionado seguia con un bloque debajo del cuadro, y
el arte se cortaba arriba de la fila.

- Bloque bajo el seleccionado: el 2:3 de Steam no es un alto, es `padding-top: 150%` en el
  wrapper de la imagen (`._3Ehhd5MxErV_bXQE4qVhzB`). Con aspect-ratio no se va; se cambia a
  `padding-top: 100%`. Eso sustituye el truco del paso 1.
- Arte a pantalla completa: el hero vive en `.QNkOtW3xS-yj6LviWHvnd` (902x356, ~70% del alto)
  con una mascara que lo desvanece al 90%. Se pone a 100vh, sin mascara, imagen en cover.
  Al ser mas alto, el arte se recorta a los lados (igual que en el PS5).
- Franja oscura y brillo azul bajo la fila: no era fondo, era un reflejo de cada caratula
  (`._1H3KfkJV5jxe2CR41DtUi0`, filtro saturate(3) brightness(2) blur(3px)) desbordado hacia
  abajo. Se oculta.

Pendiente: barra inferior de botones con fondo oscuro; bloque Moonlight sin arte; fila aun pegada
abajo (en el PS5 flota a media altura).

## Paso 3 — El jugado mas reciente tambien en cuadro

Archivo: `theme/home-primero.css`. Captura: `capturas/04-home-primero-cuadrado.png`.

Steam da al ultimo juego una celda ancha con arte horizontal: 442px contra 146px de las demas
(px internos de la fila, que va escalada). La fila es una grilla virtualizada de React con cada
celda en `position:absolute` y `left` inline, asi que la primera se reconoce por `left: 0px`.
- Primera celda a 146px, y su contenido (`._1HIFN...` traia `width: 430px` inline) a 134px, 1:1,
  imagen en cover.
- Las demas celdas se corren `translateX(-296px)` (442-146) para cerrar el hueco.
Medidas tomadas en la Ally a 1920x1080; en otra resolucion habria que remedirlas.
En la captura el seleccionado es Moonlight, que no tiene arte (por eso el fondo liso).

Por probar a mano: que al moverse por la fila con el mando el scroll siga al foco bien, porque
Steam calcula el scroll con sus medidas originales.

## Paso 4 — Barra inferior sin fondo

Archivo: `theme/home-footer.css`. Captura: `capturas/05-home-barra-sin-fondo.png`.

La barra de botones (`._3T1iFy2maYycwqgFuzERyf`) tenia fondo negro al 50% y un borde superior
gris de 1px. Se quitan los dos; los botones quedan flotando sobre el arte.
Primera prueba (`pruebas/footer-1`) solo quito el fondo y dejo visible la linea.

## Vista de juego — punto de partida

Captura: `capturas/06-juego-original.png` (Clair Obscur: Expedition 33). Con los estilos del
home inyectados; ninguno toca esta vista salvo la barra de botones.

Como esta hoy:
- Arte del juego a pantalla completa, logo del juego abajo a la izquierda.
- Franja inferior oscura con: boton verde "Play" + flecha de opciones, LAST PLAYED (Sep 17),
  PLAY TIME (35.5 hours), y a la derecha botones de mando y ajustes.
- Debajo, otra franja con "STEAM CLOUD: UP TO DATE" y una linea, y la barra de botones.

Contra la ficha del concepto PS5:
- PS5: panel oscuro a la izquierda con titulo en texto, cifras grandes (tiempo jugado, espacio,
  addons, amigos) y pestañas PLAY / MULTIPLAYER / TROPHIES / STORE...; arte recortado a la derecha;
  barra de progreso de trofeos y boton "START THE GAME" con contorno blanco.
- Steam ya tiene: arte, logo, Play, ultima vez jugado, tiempo de juego, estado de la nube. Al
  bajar con el mando aparecen las secciones (actividad, logros, etc.).
- Lo mas cercano sin reorganizar: boton Play blanco con contorno en vez de verde, cifras con
  tipografia grande y etiqueta chica, franjas oscuras fuera, y logo/cifras/Play agrupados abajo a
  la izquierda sobre un degradado.

## Paso 5 — Ficha de juego, opcion 1 (estilo sin reorganizar)

Archivo: `theme/juego-ficha.css`. Captura: `capturas/07-juego-ps5-opcion1.png`
(pruebas: `pruebas/ficha-1` a `ficha-5`).

- Boton Play: fondo negro al 35% con contorno blanco fino; con foco, contorno blanco de 2px.
  Texto en mayusculas espaciadas ("PLAY"). La flecha de opciones sigue la misma linea.
  `text-transform` necesito `!important`: sin el, Steam lo dejaba en "Play".
- Cifras: etiqueta a 8px en mayusculas, valor a 22px semibold.
- Botones de mando y ajustes: cuadros con contorno, sin relleno.
- Fuera franjas: la de Play/cifras (`._3scbHORk...`, 33% oscuro), la capa de 25% que cubre todo
  lo de abajo (`._3fp5y6...`) y las lineas a los lados de STEAM CLOUD.
- Arte a pantalla completa. Aqui costo: la franja de STEAM CLOUD parecia un fondo, pero no habia
  ningun elemento con fondo ahi. Con `elementsFromPoint` y un contorno rojo de depuracion salio
  que la vista tiene DOS imagenes del arte: la nitida (`library_hero`, 1920x620, 92% del alto) y
  una de 192x62 px difuminada (`library_hero_blur`) que ocupa toda la pantalla como fondo. La
  franja era esa version borrosa asomando. Se estira la nitida a 100vh en cover.
  (ficha-2 a ficha-4 apuntaban a la imagen equivocada.)
- Probado y descartado: degradado oscuro a la izquierda en la franja de Play; deja un borde duro
  arriba.

## Ficha de juego, seccion Activity — punto de partida

Captura: `capturas/08-juego-actividad-original.png` (bajando desde la ficha con el mando).
Sin estilos propios en esta vista todavia.

Como esta: barra de pestañas arriba con L1 / R1 en cuadros blancos y pestañas ACTIVITY (pildora
blanca seleccionada) / YOUR STUFF / COMMUNITY / GAME INFO. Fondo gris pizarra liso. Secciones
Friends (played previously) y Activity (caja para comentar, noticias, logros por fecha) en
tarjetas gris claro. Boton azul "SCROLL TO TOP" abajo al centro.

Es la parte de Steam que mas se parece a la ficha del concepto: el PS5 tambien tiene L1 / R1 y
pestañas (PLAY / MULTIPLAYER / TROPHIES / STORE...) sobre un panel oscuro, con listas debajo.
Diferencias: en el PS5 las pestañas son texto chico en mayusculas y la seleccionada es una
pildora con contorno azul (no relleno blanco); L1 / R1 son etiquetas chicas con contorno; el
panel es casi negro y las listas son filas con miniatura, sin tarjetas grises.

## Paso 6 — Secciones de la ficha (Activity...) estilo PS5

Archivo: `theme/juego-secciones.css`. Captura: `capturas/09-juego-actividad-ps5.png`
(pruebas: `pruebas/actividad-sin-estilos`, `secciones-1`, `secciones-2`).

Antes se comprobo que el fondo gris liso es de Steam y no efecto de nuestros estilos: con
`juego-ficha` desactivado (`<style>.disabled = true`) se ve igual.

- Fondo de la vista (`._3lDczhul...`): gris pizarra -> #15171c.
- Pestañas: texto 10px en mayusculas espaciadas; la activa (`._3Gp1bACHx...`) pasa de pildora
  blanca rellena a contorno azul #2d7ff9.
- L1 / R1: el glifo es una imagen (cuadro blanco con letras caladas). Invertirla con
  `filter: invert(1)` + `mix-blend-mode: screen` dejo cuadros negros con letras ilegibles
  (secciones-1). Se oculta la imagen y se escribe "L1" / "R1" con `::after` sobre un contorno.
- Titulos de seccion (Friends, Activity) como etiquetas chicas en mayusculas; "Played
  previously" mas tenue.
- Tarjetas grises -> filas transparentes con separador de 1px; caja de comentario con contorno.
- SCROLL TO TOP: de pestaña azul a contorno blanco sobre negro.
- Barra de pestañas con fondo solido degradado: al bajar, el arte estirado de la ficha (paso 5)
  asomaba arriba con el texto STEAM CLOUD (secciones-1).

## Paso 7 — Fondo de vidrio negro (glassmorphic) en las secciones

Archivo: `theme/juego-secciones.css` (reemplaza el fondo #15171c del paso 6).
Captura: `capturas/10-juego-actividad-glass.png` (pruebas: `secciones-3` a `secciones-5`).

No gusto el gris; pidio blur negro estilo glassmorphic.
- Fondo: la version difuminada del arte que Steam ya carga (`library_hero_blur`, 192x62) se fija a
  pantalla completa con `blur(24px) brightness(0.32) saturate(1.3)`. Sale el color del juego, muy
  oscuro. Raiz de la vista en negro por si no hay arte.
- Barra de pestañas: negro al 35% con `backdrop-filter: blur(16px)`.
- Tarjetas (amigos, caja de comentario, entradas de actividad): blanco al 4.5%, borde blanco al 9%,
  radio 6px, `backdrop-filter: blur(12px)`. Cabecera y cuerpo de cada entrada se unen en una.

Lo que costo: con `position: fixed` el fondo seguia moviendose con el scroll (secciones-3 salio
negro: la imagen estaba 496px arriba, fuera de pantalla). Causa: Steam monta la ficha con
`transform-style: preserve-3d` (el parallax del arte) en tres contenedores, y eso los vuelve el
marco de referencia de `fixed`. Se ponen en `flat`. Efecto secundario posible: perder el parallax
del arte al hacer scroll en la parte de arriba de la ficha.

## Menu lateral — punto de partida

Captura: `capturas/11-menu-lateral-original.png` (abierto desde el home con el boton de menu).

Vive en OTRA pestaña de CEF, no en "Steam Big Picture Mode": `MainMenu_uid2`. Los estilos
inyectados hasta ahora no le llegan; hay que inyectar ahi aparte.

Como esta: panel azul marino solido a la izquierda (~27% del ancho), items Home / Library / Store /
Friends & Chat / Media / Downloads / Settings / Power con icono. El seleccionado tiene relleno gris
y una barra azul en el borde izquierdo. Detras, el home oscurecido y difuminado (ya con las
caratulas cuadradas).

El concepto PS5 no muestra este menu. Para que case con lo demas: panel de vidrio negro como las
secciones (paso 7), texto e iconos blancos, y el seleccionado con contorno blanco como el foco de
las caratulas y del boton PLAY, sin la barra azul.

## Paso 8 — Menu lateral de vidrio

Archivo: `theme/menu-lateral.css`, inyectado en la pestaña `MainMenu_uid2`
(`TAB=MainMenu_uid2 tools/inject.sh menu-lateral`; inject.sh ahora acepta TAB).
Captura: `capturas/12-menu-lateral-glass.png` (pruebas: `menu-1` a `menu-3`).

- Panel (`._23IDiI...`, azul marino solido) -> negro al 45% con blur(20px) y borde derecho fino.
  La ventana del menu es transparente fuera del panel, asi que se ve el home difuminado detras.
- Item con foco: contorno blanco 1.5px y relleno blanco al 6%, esquinas de 4px; sin la barra azul
  (`._1uLVHdii...`). Texto de los demas en blanco al 78%.
- menu-1: `._2w9Tp...` resulto ser la clase de TODOS los items, no del seleccionado; todos
  salieron encuadrados y encogidos. El foco se marca con `.gpfocus`.
- menu-2: el contorno se cortaba a la derecha. Steam escala a 1.1 el item con foco y se salia de
  la ventana del menu (240px). Se quita la escala.

## Paso 9 — Menu de opciones del juego

Archivo: `theme/menu-juego.css` (pestaña principal). Captura original
`capturas/13-menu-juego-original.png`, resultado `capturas/14-menu-juego-glass.png`.

Es el menu que sale con OPTIONS sobre un juego (Play, Add to Favorites, Add to, Remove from,
Manage, Developer, Change Artwork, Properties, Cancel). A diferencia del menu lateral, vive en la
pestaña principal, dentro de `.BasicUIContextMenu`. Sus items usan clases legibles
(`contextMenuItem`, `Play`), menos fragiles que las ofuscadas.

- Panel: gris oscuro solido -> vidrio negro (45%, blur 20px, borde fino, radio 8px).
- Items transparentes, texto blanco al 78%; con foco, contorno blanco como en el menu lateral.
- Play: sin el verde; en mayusculas espaciadas como el PLAY de la ficha.
- Separadores: linea negra de 2px -> blanca tenue de 1px.
Salio a la primera. Se aplico sin pasar antes por propuesta porque sigue el mismo lenguaje que
los pasos 7 y 8.

## Paso 10 — Home, parte de abajo (What's New, Recently updated)

Archivo: `theme/home-detalles.css` + correccion en `theme/home-primero.css`.
Captura original `capturas/15-home-detalles-original.png`, resultado
`capturas/16-home-detalles-glass.png` (pruebas: `detalles-0`, `detalles-1`).

BUG NUESTRO encontrado aqui: en la captura original las tarjetas de What's New salian encimadas
(dos titulos y dos fechas uno sobre otro). Era el paso 3: el corrimiento de -296px se aplicaba a
TODAS las grillas virtualizadas del home, no solo a la fila de recientes. Se acoto con
`.ReactVirtualized__Grid__innerScrollContainer:has(._1pwP4eeP1zQD7PEgmsep0W)`. Verificado en el
DOM: la grilla de recientes sigue con la primera celda a 146px y el resto corrido; las otras tres
grillas quedan intactas.

Estilo:
- Fondo del home: azul marino -> casi negro con un degradado leve.
- Pie de las tarjetas de noticias y tarjetas de "Recently updated": vidrio (blanco 4.5%, borde
  9%, blur 12px), esquinas de 6px.
- Titulo de seccion ("Recently updated on this device") y fechas ("3 weeks ago") como etiquetas
  chicas en mayusculas.
- Contador de amigos junto a FRIENDS: pildora verde -> blanco translucido.
- Las pestañas y L1/R1 ya venian con el estilo del paso 6 (mismas clases).

## Paso 11 — Barra superior y busqueda

Archivo: `theme/topbar.css`. Captura original `capturas/17-topbar-busqueda-original.png`,
resultado `capturas/18-topbar-busqueda-glass.png` (pruebas: `topbar-1`, `topbar-2`).

- Busqueda: barra BLANCA a todo lo ancho con texto oscuro -> pildora de vidrio negro (45%,
  blur 16px) con contorno blanco al 35%, texto blanco, placeholder al 50%, lupa y X blancas.
- La franja de la barra es un `::before` con negro al 50% + `backdrop-filter: blur(100px)` (el
  blur se nota con la busqueda abierta). Ya era vidrio; se deja el blur y el negro baja a 35%.
- topbar-1: la pildora se cortaba a la derecha (el margen la empujaba fuera de su contenedor, que
  mide fijo 592px) y la lupa desaparecio: el color se aplico a un svg que no es el de la lupa.
  Se acoto con `max-width: calc(100% - 20px)` y las clases propias de lupa y X
  (`._2Ya83...`, `._1Ka4T...`).
- Probado y descartado: degradado que se desvanece hacia abajo. Encima del blur de 100px se ve
  como una franja con borde duro igual.

## Paso 12 — Resultados de busqueda y teclado en pantalla

Archivo: `theme/busqueda-teclado.css`. Captura original `capturas/19-busqueda-teclado-original.png`,
resultado `capturas/20-busqueda-teclado-glass.png`.

- Las pestañas ALL / LIBRARY / FRIENDS / STORE / TOOLS ya salieron con el contorno azul del
  paso 6: son las mismas clases. Igual la busqueda del paso 11.
- Fondo de resultados (`.P_AlEAb9...`, azul marino propio de esta pagina) -> casi negro del home.
- "IN LIBRARY": etiqueta chica y tenue.
- Teclado (`._45rH7... .DefaultTheme`, en la pestaña principal): panel gris solido -> vidrio
  negro (55%, blur 24px) con borde superior fino. Teclas: de bloques negros pegados a teclas de
  vidrio (blanco 7%, borde 8%, radio 6px); las especiales (Tab, Shift, Caps, Backspace, Paste...,
  por su clase `KeyTheme_*`) mas oscuras. La tecla con foco sigue blanca solida, ahora redondeada.
Salio a la primera.

## Paso 13 — Pestaña LIBRARY de la busqueda y anillo de foco general

Archivo: `theme/foco.css`. Captura original `capturas/21-biblioteca-original.png`, resultado
`capturas/22-busqueda-library-foco.png`.

Ojo: lo que estaba abierto NO es la Biblioteca del menu lateral, es la pestaña LIBRARY de la
pagina de busqueda (misma grilla horizontal con "IN LIBRARY"). Ya venia con el estilo del paso 12.
La Biblioteca de verdad (Menu > Library, pestañas tipo Great on Deck / All games / Installed y
caratulas verticales) queda pendiente.

Lo nuevo: el foco gris claro de las tarjetas no estaba en la tarjeta. Steam dibuja el foco con
un div aparte (`._1wPplsegQqCoe06wXPhzKT`) que se coloca encima del elemento enfocado, con outline
blanco al 60%. Se encontro buscando elementos con el mismo rectangulo que `document.activeElement`
fuera de su arbol. Se pone en blanco solido de 2px, separado 2px y con esquinas de 4px. Como es
el anillo generico, afecta a todas las grillas que lo usen. Arte de los resultados con esquinas.

## Paso 14 — Ajustes (Settings)

Archivo: `theme/settings.css`. Captura original `capturas/23-settings-original.png` (Storage),
resultado `capturas/24-settings-glass.png`.

- Fondo (`._33vqr13...`, azul muy oscuro solido) -> casi negro del home.
- Columna de secciones (`.PageListColumn`): gris solido -> vidrio (blanco 3.5%, blur 20px) con
  borde derecho fino. Contenido (`.DialogContentTransition`): gris solido -> transparente.
- Seccion activa (`._1ELdDY...`): degradado azul -> blanco al 8% con esquinas; con foco, contorno
  blanco como el menu lateral.
- Selector de disco en Storage: pildora blanca rellena con texto negro -> contorno blanco con
  texto e icono blancos.
Salio a la primera. Solo se vio Storage; las demas secciones comparten columna y fondo, pero
pueden tener controles propios (sliders, toggles) sin revisar.

## Paso 15 — Menu de acceso rapido (derecha)

Archivo: `theme/quickaccess.css`, inyectado en la pestaña `QuickAccess_uid2`.
Captura original `capturas/25-quickaccess-original.png`, resultado
`capturas/26-quickaccess-glass.png` (prueba: `pruebas/qa-1`).

- Panel (`.V0cr-SAn...`, azul oscuro solido) -> negro al 50% con blur y borde izquierdo fino.
  Es otra ventana; detras se ve la principal oscurecida y difuminada.
- Columna de iconos: separador fino a la derecha.
- Pestaña activa (`._2QHMua1...`): gris solido -> blanco tenue con contorno blanco.
- Cabecera ("Notifications"): ademas de fondo solido tenia una `box-shadow` difusa del mismo azul
  (0 0 7px 12px) que seguia pintando la franja aunque el fondo ya fuera transparente (qa-1). Se
  quitan las dos.
Solo se vio la pestaña de notificaciones; las demas (amigos, ajustes rapidos, rendimiento,
musica, ayuda, Decky) comparten panel y cabecera pero pueden tener controles propios.

## Paso 16 — Sin barra inferior

Archivos: `theme/sin-barra.css` (pestaña principal), añadidos en `theme/menu-lateral.css` y
`theme/quickaccess.css`. Captura: `capturas/27-sin-barra-quickaccess.png`
(pruebas: `sinbarra-1`, `sinbarra-2`).

Pedido: la barra de botones de abajo corta los menus.
- Pestaña principal: la barra (`._3T1iFy...` y `._2JJDHoMl...`) con `display:none`. Se pierden
  las ayudas MENU / SELECT / BACK en todas las vistas. Deja sin efecto `home-footer.css`.
- Menu lateral: su ventana trae SU PROPIA copia de la barra (`._3kHmfV9...`, 40px). Fuera, y el
  panel a `calc(100vh - 40px)` para que llegue al borde (con `flex-grow` no crecio:
  sinbarra-1 seguia en 429px). Verificado en el DOM: panel de y=40 a y=509 de 509.
  Falta verlo en pantalla con el menu lateral abierto.
- Acceso rapido: aqui NO se puede. La ventana misma mide 429px y termina 40px antes del borde
  (screenY=39); Steam reserva esa franja y el tamaño de ventana no se cambia con CSS. Se cierra
  como tarjeta flotante: borde inferior y esquina inferior izquierda redondeada.

## Paso 17 — Titulo del seleccionado debajo de la fila

Archivo: `theme/home-cuadros.css` (añadido al final). Captura: `capturas/28-home-titulo-abajo.png`.

Se eligio (entre fila arriba / titulo abajo / fila a media altura) dejar la fila donde esta y
bajar el nombre del juego y PLAYTIME de encima a debajo del cuadro.
La etiqueta (`.ZkD6We6MqGbOsa9K3yiY3`) va en absoluto con `top: -64px` en px internos de la fila
(que esta escalada a 0.7). El cuadro mide 134px internos, asi que va a `top: 142px` (134 + 8).
Acotado a la fila de recientes con el mismo `:has(._1pwP...)` del paso 10. Salio a la primera;
cabe porque la barra inferior ya no esta (paso 16).

## Paso 18 — Menu con un juego abierto

Archivo: `theme/menu-en-juego.css` (pestaña `MainMenu_uid2`). Capturas: original
`capturas/29-menu-en-juego-original.png`, resultado `capturas/30-menu-en-juego-glass.png`.

OJO CON LAS CAPTURAS: con un juego en primer plano, `gamescopectl screenshot` saca solo el juego,
sin la capa de Steam encima (salio la pantalla de idioma de Sephiria). Para estas se usa
`tools/cdpshot.mjs <pestaña> <png>` (Page.captureScreenshot de CEF): saca la ventana del menu tal
cual, pero sin el juego detras: lo transparente sale negro. Para el video, mejor grabar la
pantalla del Ally.

Es el mismo menu lateral, en otra forma: riel de iconos (ya con el vidrio del paso 8) + panel del
juego (logo, Resume game, Controller settings, View game details, Achievements, Guides, Notes,
Game Recording, Exit game) + panel derecho con el esquema del mando.
- Panel del juego (`.sfthxkhui...`): azul oscuro solido -> negro al 50% con blur 24px, hasta abajo.
- Columna de opciones (`._12NNtyso...`): degradado azulado con bordes grises de 2px -> vidrio con
  separador fino.
- Opcion con foco (`._2b6L36...`): gris solido -> contorno blanco, sin escala.
- Panel derecho (`.RAI0lLN8...`, 90% opaco) -> transparente.
- Boton "Controller settings": gris -> contorno.

## Paso 19 — Controller Settings y botones de dialogo en general

Archivo: `theme/dialogos.css` (pestaña principal). Capturas (por `cdpshot`, hay juego abierto):
original `capturas/31-controles-original.png`, resultado `capturas/32-controles-glass.png`.

- Botones: Steam usa clases legibles `DialogButton _DialogLayout Primary|Secondary` en todos sus
  dialogos. Se reestilan TODOS a proposito: secundarios en vidrio (blanco 6%, borde 12%, radio 4px),
  primario (antes azul solido, "View Layout") en contorno blanco, y con foco (`.gpfocus`) contorno
  blanco doble. Esto alcanza tambien a dialogos que aun no se han visto (confirmaciones,
  propiedades...): revisar cuando aparezcan.
- Fondo de la pagina (`.APY6j...`) y cabecera (`._20sN9G...`) -> casi negro; panel de Quick
  Settings transparente; filas (`.eKmEXJCm...`, gris solido) -> vidrio con borde y radio 6px.
- El interruptor azul (Enable Extended Buttons) se deja como esta: es estado, no decoracion.
Salio a la primera.

## Paso 20 — View Layout (esquema del mando)

Archivo: `theme/dialogos.css` (añadido). Capturas por `cdpshot`: original
`capturas/33-layout-original.png`, resultado `capturas/34-layout-glass.png`.

- Fondo (`._3TvBVwa... .controller_rog_ally`, azul oscuro solido) -> casi negro.
- Fila con foco (`.QAVElkR0...`, "Left Bumper"): gris solido -> contorno blanco con relleno tenue.
- El dibujo del mando conserva su relleno azul oscuro (es el SVG); no se toco.
Salio a la primera.

## Paso 21 — Ajustes de un boton del mando (Trigger Settings) y fallo de texto en desplegables

Archivo: `theme/dialogos.css` (añadido). Capturas por `cdpshot`: original
`capturas/35-menu-abierto-original.png`, resultado `capturas/36-menu-gatillo-glass.png`.

FALLO NUESTRO encontrado aqui: el desplegable con foco ("Hair Trigger") salia con texto gris
oscuro sobre negro, ilegible. Steam pone texto oscuro al boton de dialogo con foco porque su foco
es fondo blanco; el paso 19 cambio ese fondo a contorno y dejo el texto oscuro. Fix: con
`.gpfocus`, el boton y todo su contenido en blanco.

Estilo de la pagina:
- Fondo del dialogo (`._2FqpD91...`, degradado azul) -> casi negro. Esta clase tambien envuelve
  otras vistas (aparecio en el home): el cambio es global y a proposito.
- Columna izquierda (`._2oua5ZJ...`, blanco 10%) -> vidrio con separador fino.
- Seccion activa: relleno blanco al 8% con esquinas, ajustada al ancho de la columna (se salia
  264px en 240, como en el menu lateral); con foco, contorno blanco y sin escala.
Las filas de la derecha ya venian en vidrio por el paso 19 (misma clase `.eKmEXJCm...`).
