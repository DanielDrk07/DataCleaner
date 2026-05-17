# DataCleaner ✨

Herramienta visual de limpieza y transformación de datasets CSV/Excel. Carga tu archivo, aplica operaciones de limpieza con un clic y exporta el resultado listo para análisis, **sin escribir código**.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red)
![Tests](https://img.shields.io/badge/tests-78%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Interfaz

La app corre en el navegador y tiene dos zonas principales:

**Panel izquierdo (sidebar oscuro)**
- Cargador de archivos CSV / Excel
- Resumen del archivo cargado (filas × columnas)
- 8 operaciones de limpieza en acordeones expandibles
- Botón **↩ Deshacer** para revertir la última operación
- Exportar resultado como CSV o Excel + log de cambios

**Área principal (5 pestañas)**

| Pestaña | Contenido |
|---------|-----------|
| 📊 Vista de Datos | Tabla interactiva con buscador de texto en tiempo real |
| 🔍 Diagnóstico & IA | Score de salud, gráfico de nulos, detalle por columna, recomendaciones automáticas + IA Groq |
| 📈 Estadísticas | Resumen descriptivo, histograma, violin/box plot, frecuencias categóricas, comparación de medias |
| 🔗 Correlaciones | Matriz de calor de Pearson con anotaciones y guía de interpretación |
| 📋 Historial | Log de todas las operaciones realizadas (descargable) |

---

## Requisitos

- **Python 3.9 o superior**
- Dependencias listadas en `requirements.txt` (Pandas, Streamlit, Plotly, etc.)
- **Groq API key** (gratuita, sin tarjeta) — solo necesaria para recomendaciones con IA

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/datacleaner.git
cd datacleaner

# 2. Crear entorno virtual (recomendado)
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / Mac
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

---

## Uso

### Opción A — Script directo (Windows)

```bat
run.bat
```

El script verifica Python, instala dependencias y abre la app automáticamente.

### Opción B — Línea de comandos

```bash
streamlit run app.py
```

Abre tu navegador en **http://localhost:8501**.

---

## Configurar IA (opcional)

Las recomendaciones de inteligencia artificial usan la **API gratuita de Groq** (modelo `llama-3.1-8b-instant`). No requiere tarjeta de crédito.

1. Crea una cuenta en [console.groq.com](https://console.groq.com) y genera una API key
2. Copia `.env.example` a `.env` en la raíz del proyecto:

```bash
cp .env.example .env   # Linux / Mac
copy .env.example .env  # Windows CMD
```

3. Edita `.env` y añade tu clave:

```env
GROQ_API_KEY=gsk_tu_clave_aqui
```

Sin `.env`, la app funciona con normalidad — las recomendaciones IA simplemente no aparecen.

> **Seguridad:** el archivo `.env` está en `.gitignore` y nunca se sube al repositorio.

---

## Variables de entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `GROQ_API_KEY` | No | API key de Groq para recomendaciones con IA. Obtener en [console.groq.com/keys](https://console.groq.com/keys) |

---

## Operaciones disponibles

| Operación | Descripción |
|-----------|-------------|
| 🔸 Tratar nulos | Eliminar filas con nulos o rellenar con media / mediana / moda / valor personalizado |
| 🔁 Eliminar duplicados | Filas completamente idénticas en todo el dataset |
| 🔤 Normalizar texto | Minúsculas, recorte de espacios, colapsar espacios internos |
| 🔄 Convertir tipo | `int` · `float` · `str` · `datetime` |
| ✏️ Renombrar columna | Edición directa del nombre |
| 🔍 Filtrar / eliminar filas | Por condición sobre cualquier columna (`==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `startswith`) |
| 🗑️ Eliminar columna | Con soporte de deshacer |
| 📉 Eliminar outliers (IQR) | Factor configurable (1.5 estándar · 3.0 solo extremos) |

Cada operación es reversible con **↩ Deshacer** (historial de hasta 20 pasos).

---

## Formatos de archivo soportados

- **CSV** — autodetecta separador (`,` `;` `\t` `|`) y codificación (UTF-8, Latin-1, CP1252)
- **Excel** `.xlsx` y `.xls`

---

## Estructura del proyecto

```
datacleaner/
├── app.py                      # UI principal (Streamlit)
├── model/
│   ├── cleaning_model.py       # Lógica de limpieza + historial undo
│   ├── data_validator.py       # Análisis y diagnóstico del dataset
│   └── recommender.py          # Recomendaciones locales + Groq IA
├── tests/
│   ├── test_cleaning_model.py  # 26 tests del motor de limpieza
│   ├── test_data_validator.py  # 30 tests del validador
│   └── test_recommender.py     # 22 tests del recomendador
├── .streamlit/
│   └── config.toml             # Tema visual (colores, fuentes)
├── .github/
│   └── ISSUE_TEMPLATE/
│       └── bug_report.md       # Plantilla para reportes de bugs
├── .env.example                # Plantilla de variables de entorno
├── requirements.txt            # Dependencias de producción
├── requirements-dev.txt        # Dependencias para tests (pytest)
└── run.bat                     # Lanzador rápido para Windows
```

---

## Tests

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar todos los tests
pytest tests/

# Con reporte de cobertura
pytest tests/ -v
```

78 tests unitarios — modelo de limpieza, validador y recomendador cubiertos.

---

## Licencia

MIT
