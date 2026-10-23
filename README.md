# Observatorio de valoraciones

Aplicación Streamlit en castellano inspirada en dashboard-valoraciones: cabecera verde oscuro, tarjetas de indicadores y diseño claro, sin menú lateral.

## Iniciar la aplicación

Necesitas Python 3.10 o posterior. Abre una terminal en esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Si ya tienes el entorno instalado, actualiza las dependencias para incorporar Plotly. Para detener la aplicación pulsa Ctrl+C.

## Fuente de datos

La primera hoja de `data/reviews-clients.xlsx` alimenta el dashboard. En el inicio de app.py, después de las librerías, hay dos alternativas:

```python
DATA = ROOT / "data" / "reviews-clients.xlsx"
# DATA = "https://raw.githubusercontent.com/alanaolivieri/n8n-automation/main/data/reviews-clients.xlsx"
```

Para usar GitHub, comenta la línea local y descomenta la remota. Mantén una sola activa. Comprueba que repositorio, rama y archivo correspondan a la URL y que el Excel sea accesible sin autenticación. El remoto configurado en esta copia es `alanaolivieri/n8n-automation`; estos cambios se guardan solo en local.

El botón «Actualizar datos» fuerza una nueva lectura. La caché remota dura cinco minutos; la local también se invalida al cambiar la fecha de modificación del Excel. Si falta el archivo o no es accesible, aparece un aviso sin crear datos ficticios.

## Columnas

| Columna | Uso |
| --- | --- |
| Nombre | Nombre de la persona, opcional |
| Apellido | Se une al nombre, opcional |
| Review | Comentario |
| estrellitas | Puntuación numérica |

Se admiten también Comentario y Valoración (con o sin tilde), rating o estrellas. Se aceptan decimales con coma o punto. Las puntuaciones vacías, no numéricas o infinitas se excluyen con un aviso. No se presupone una escala de cinco estrellas. El Excel original no se modifica.

## Dashboard

Los filtros están en una fila sobre los indicadores: búsqueda por persona o comentario, intervalo de puntuación y orden de la tabla. Todos los resultados siguen la selección.

Se muestran número de comentarios, media, mínimo y máximo; un gráfico interactivo de Plotly con valoraciones en el eje Y y número de comentarios en X; los cinco comentarios peor valorados; y la tabla completa. El gráfico ofrece detalles al pasar el cursor y controles para ampliar, desplazar y restablecer la vista.

## Organización del código

Las rutas, colores y configuración visual están al principio, después de las librerías. Las funciones de lectura, validación, filtros, métricas y presentación son independientes y están definidas a nivel de módulo. main coordina la aplicación.

## Privacidad

El código no incluye datos reales ni secretos. El Excel se procesa en el equipo o servidor donde se ejecute Streamlit. Quienes accedan a la aplicación podrán ver sus datos. No subas datos personales a un repositorio público. No se incluye un flujo de n8n ni envío de mensajes.
