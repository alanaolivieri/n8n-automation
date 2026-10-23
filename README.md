# Observatorio de valoraciones

Sistema para recibir valoraciones por correo, guardarlas en un Excel de GitHub y consultarlas en un dashboard de Streamlit. Las valoraciones inferiores a 2 generan una alerta en Discord.

La aplicación está en castellano y utiliza un diseño sencillo: cabecera verde oscuro, tarjetas de indicadores, filtros en la página principal y gráficos interactivos.

## Cómo funciona

```text
Correo en Gmail con etiqueta REVIEWS
                  ↓
       n8n extrae y valida los datos
                  ↓
   Actualiza el Excel de GitHub sin duplicados
                  ↓
     Si la valoración es inferior a 2
         envía una alerta a Discord

Streamlit consulta el Excel de GitHub
y muestra las valoraciones en el dashboard.
```

El flujo completo está operativo. El workflow se gestiona desde el [proyecto de n8n](https://aolivieri.app.n8n.cloud/projects/ZIu9u1X9EtRIOQIH/workflows), cuyo acceso requiere los permisos correspondientes.

## Estructura del proyecto

```text
n8n-automation/
├── app.py                    # Aplicación Streamlit
├── requirements.txt          # Dependencias de Python
├── README.md
└── data/
    └── reviews-clients.xlsx  # Archivo de valoraciones
```

## Iniciar la aplicación

Necesitas **Python 3.10 o posterior**. Abre una terminal en la carpeta del proyecto.

Crea el entorno virtual:

```powershell
python -m venv .venv
```

Instala las dependencias:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Inicia Streamlit:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abre en el navegador la dirección que indique la terminal. Para detener la aplicación, pulsa **Ctrl+C**.

En las siguientes sesiones basta con ejecutar el último comando. Si cambia `requirements.txt`, vuelve a instalar las dependencias.

## Fuente de datos

La aplicación lee la **primera hoja** de `reviews-clients.xlsx`. La primera fila debe contener las cabeceras.

Al principio de `app.py` se configura la fuente mediante `DATA`. Mantén **una sola línea activa**.

### Leer desde GitHub

Esta opción permite consultar el archivo que actualiza n8n:

```python
# DATA = ROOT / "data" / "reviews-clients.xlsx"
DATA = "https://raw.githubusercontent.com/alanaolivieri/n8n-automation/main/data/reviews-clients.xlsx"
```

La URL debe corresponder al repositorio, la rama y la ruta del Excel. Esta forma de lectura requiere que el archivo sea accesible sin autenticación.

### Leer desde el equipo local

Para trabajar con una copia local:

```python
DATA = ROOT / "data" / "reviews-clients.xlsx"
# DATA = "https://raw.githubusercontent.com/alanaolivieri/n8n-automation/main/data/reviews-clients.xlsx"
```

**La copia local no se sincroniza automáticamente con GitHub.** Si n8n actualiza el archivo remoto, esos cambios no aparecerán en el Excel local.

### Actualización de datos

El botón **Actualizar datos** borra la caché de lectura y vuelve a consultar la fuente configurada.

La caché tiene una duración de **cinco minutos**. Su caducidad permite una nueva lectura en la siguiente ejecución de la aplicación, pero **no refresca por sí sola una página abierta**. Una actualización en GitHub tampoco provoca una actualización inmediata de Streamlit.

En modo local, la caché también se invalida cuando cambia la fecha de modificación del Excel.

Si falta el archivo o no puede abrirse, la aplicación muestra un aviso y no genera datos ficticios.

## Formato del Excel

| Columna | Contenido |
| --- | --- |
| `Nombre` | Nombre de la persona. Opcional. |
| `Apellido` | Apellido de la persona. Opcional. |
| `Review` | Texto del comentario. |
| `valoración` | Puntuación numérica. |
| `Email_ID` | Identificador que utiliza n8n para evitar duplicados. No se muestra en el dashboard. |

La aplicación reconoce `Review` o `Comentario` para el texto, y `valoración`, `rating`, `estrellas` o el nombre anterior `estrellitas` para la puntuación. Las cabeceras se reconocen sin distinguir mayúsculas ni tildes.

Mantén **una única columna de puntuación** para evitar ambigüedades entre la escritura de n8n y la lectura de Streamlit.

Se aceptan decimales con coma o punto. Las filas con puntuaciones vacías, no numéricas o infinitas se excluyen y se muestra cuántas se han descartado.

El dashboard no limita las puntuaciones a cinco estrellas: muestra los valores numéricos del archivo. La validación de los nuevos correos depende de las reglas configuradas en n8n.

**Streamlit solo lee el Excel; n8n se encarga de actualizarlo.**

## Dashboard

Los filtros aparecen sobre los indicadores y permiten:

- Buscar por persona o por contenido del comentario.
- Seleccionar un intervalo de puntuación.
- Ordenar la tabla por valoración o por nombre.

Todos los indicadores, el gráfico, los comentarios destacados y la tabla reflejan los filtros activos.

El dashboard incluye:

| Elemento | Qué muestra |
| --- | --- |
| Comentarios visibles | Número de valoraciones seleccionadas. |
| Valoración media | Media de las puntuaciones seleccionadas. |
| Menor y mayor valoración | Extremos de la selección. |
| Distribución | Gráfico interactivo de Plotly con las valoraciones en el eje Y y el número de comentarios en el eje X. |
| Peores comentarios | Hasta cinco comentarios con las puntuaciones más bajas. |
| Tabla completa | Personas, comentarios y valoraciones de la selección. |

El gráfico permite consultar valores al pasar el cursor, ampliar, desplazar y restablecer la vista.

## Automatización con n8n

El workflow conecta [**Gmail, GitHub y Discord**](https://aolivieri.app.n8n.cloud/projects/ZIu9u1X9EtRIOQIH/workflows):

1. Detecta correos sin leer con la etiqueta `REVIEWS`.
2. Extrae y valida los datos de la valoración.
3. Consulta el Excel de GitHub y comprueba el `Email_ID` para evitar duplicados.
4. Añade las nuevas valoraciones conservando las filas existentes.
5. Guarda el Excel actualizado en GitHub.
6. Marca los correos procesados como leídos.
7. Envía una alerta a Discord si la valoración es inferior a 2.

El flujo también contempla avisos por errores de lectura o escritura en GitHub.

### Etiquetado automático en Gmail

El filtro configurado en Gmail aplica esta regla:

> Si el asunto contiene **Nueva valoración de cliente**, aplicar la etiqueta **REVIEWS**.

El filtro debe dejar desmarcada la opción **Marcar como leído**, ya que el workflow busca mensajes pendientes de lectura.

### Correo de ejemplo

**Asunto:**

```text
Nueva valoración de cliente — prueba
```

**Cuerpo:**

```text
Nombre: Ana
Apellido: Prueba
Cliente: Ana Prueba
Valoración: 1
Comentario: El pedido llegó tarde y no recibí información sobre el retraso.
```

Este ejemplo debe generar una nueva fila y una alerta en Discord, siempre que cumpla el formato del nodo de extracción. Una prueba real modifica el Excel y puede enviar mensajes al canal configurado.

## Organización del código

Las rutas, los colores y la configuración visual se definen al principio de `app.py`, después de las importaciones.

Las funciones de lectura, validación, filtros, métricas y presentación están definidas a nivel de módulo, sin funciones anidadas. La función `main()` coordina la aplicación.

Las dependencias se mantienen en `requirements.txt`.

## Resolución de problemas

| Problema | Qué comprobar |
| --- | --- |
| No aparecen las nuevas valoraciones | Verifica que `DATA` apunte a GitHub y pulsa **Actualizar datos**. |
| Se excluyen filas | Comprueba que `valoración` contenga números y que no haya otra columna de puntuación con datos diferentes. |
| No se encuentra el Excel remoto | Revisa el acceso al repositorio, la rama `main` y la ruta `data/reviews-clients.xlsx`. |
| n8n no detecta el correo | Comprueba la etiqueta `REVIEWS`, que esté sin leer y que el workflow esté publicado. |
| No llega la alerta a Discord | Revisa que la valoración sea inferior a 2, que la escritura en GitHub haya funcionado y que el webhook esté configurado. |
| Falla la actualización de GitHub | Consulta la ejecución de n8n y el error del nodo de lectura o escritura. |

## Privacidad y credenciales

Las credenciales de Gmail y GitHub, junto con la configuración del webhook de Discord, se gestionan en n8n. No deben añadirse al código, al README ni al repositorio.

Los datos se procesan en el equipo o servidor donde se ejecuta Streamlit y son visibles para quienes accedan al dashboard.

Si el repositorio es público, el Excel también será público. Utiliza datos simulados o anonimizados para las demostraciones.
