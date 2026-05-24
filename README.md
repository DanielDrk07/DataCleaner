# DataCleaner

**Limpia datasets CSV/Excel desde el navegador — sin escribir una sola línea de código.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-5.20%2B-3F4F75?logo=plotly&logoColor=white)](https://plotly.com)
[![Tests](https://img.shields.io/badge/tests-78%20passing-22C55E?logo=pytest&logoColor=white)](tests/)
[![License](https://img.shields.io/badge/license-MIT-6C63FF)](LICENSE)

---

## El problema que resuelve

Los analistas de datos pierden entre el 60 % y el 80 % de su tiempo limpiando datos antes de poder analizarlos. Las alternativas comunes son:

- **Excel / Sheets** — no escala, tedioso, sin historial de cambios
- **Python / Pandas** — requiere saber programar, curva de aprendizaje alta
- **Herramientas enterprise** — costosas, lentas de configurar

DataCleaner ofrece un punto medio: la potencia de Pandas expuesta en una interfaz visual, con diagnóstico automático, recomendaciones de IA y exportación lista para análisis.

**Para quién:** analistas de datos, investigadores, estudiantes y cualquiera que trabaje con CSV o Excel.

---

## Tecnologías

| Capa | Herramienta | Rol |
|------|-------------|-----|
| UI | [Streamlit](https://streamlit.io) | Framework web reactivo |
| Visualización | [Plotly](https://plotly.com) | Gráficos interactivos |
| Procesamiento | [Pandas](https://pandas.pydata.org) | Motor de limpieza |
| IA | [Groq API](https://groq.com) · Llama 3 | Recomendaciones en lenguaje natural |
| Tests | [pytest](https://pytest.org) | 78 tests unitarios |

---

## Funcionalidades

**8 operaciones de limpieza, todas reversibles con un clic:**

| Operación | Descripción |
|-----------|-------------|
| Tratar nulos | Eliminar filas o rellenar con media / mediana / moda / valor propio |
| Eliminar duplicados | Filas completamente idénticas en todo el dataset |
| Normalizar texto | Minúsculas, recorte de espacios, colapso de espacios internos |
| Convertir tipo | `int` · `float` · `str` · `datetime` |
| Renombrar columna | Edición directa del nombre |
| Filtrar / eliminar filas | Por condición (`==` `!=` `>` `<` `>=` `<=` `contains` `startswith`) |
| Eliminar columna | Con soporte de deshacer |
| Eliminar outliers (IQR) | Factor configurable: 1.5 estándar · 3.0 solo extremos |

**Panel de análisis en 5 pestañas:**
- Vista de datos con búsqueda en tiempo real
- Diagnóstico de calidad con score de salud (0–100) y recomendaciones IA
- Estadísticas descriptivas, histogramas, violin plots, frecuencias categóricas
- Matriz de correlación de Pearson interactiva
- Historial descargable de todas las operaciones realizadas

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/DanielDrk07/datacleaner.git
cd datacleaner

# 2. Crear entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / Mac
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar la aplicación
streamlit run app.py
```

Abre tu navegador en **http://localhost:8501**

> En Windows puedes usar `run.bat` — verifica Python, instala dependencias y abre la app automáticamente.

---

## Configurar IA (opcional)

Las recomendaciones de IA usan la **API gratuita de Groq** (sin tarjeta de crédito).

```bash
# 1. Crea cuenta en https://console.groq.com y genera una API key
# 2. Copia el archivo de ejemplo
cp .env.example .env   # Linux / Mac
copy .env.example .env  # Windows

# 3. Edita .env y añade tu clave
GROQ_API_KEY=gsk_tu_clave_aqui
```

Sin `.env`, la app funciona con normalidad — las recomendaciones IA simplemente no aparecen.

---

## Formatos soportados

- **CSV** — autodetecta separador (`,` `;` `\t` `|`) y codificación (UTF-8, Latin-1, CP1252)
- **Excel** — `.xlsx` (openpyxl) y `.xls` (xlrd)

---

## Estructura del proyecto

```
datacleaner/
├── app.py                      # Entry point — configuración y arranque
├── ui/
│   ├── styles.py               # CSS personalizado
│   ├── utils.py                # Constantes, helpers y funciones cacheadas
│   ├── sidebar.py              # Panel lateral con operaciones de limpieza
│   └── tabs.py                 # 5 pestañas del área principal
├── model/
│   ├── cleaning_model.py       # Motor de limpieza + historial undo (20 pasos)
│   ├── data_validator.py       # Diagnóstico de calidad — solo lectura
│   └── recommender.py          # Reglas locales + Groq API
├── tests/
│   ├── test_cleaning_model.py  # 26 tests del motor de limpieza
│   ├── test_data_validator.py  # 30 tests del validador
│   └── test_recommender.py     # 22 tests del recomendador
├── .streamlit/
│   └── config.toml             # Tema visual
├── .github/
│   └── ISSUE_TEMPLATE/
│       └── bug_report.md
├── .env.example                # Plantilla de variables de entorno
├── requirements.txt            # Dependencias
└── run.bat                     # Lanzador rápido para Windows
```

---

## Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

78 tests unitarios que cubren el motor de limpieza, el validador y el recomendador. La capa de modelo está completamente desacoplada de Streamlit y se puede testear sin levantar la app.

---

## Sobre el proyecto

### Decisiones de arquitectura

**Separación modelo / UI:** `CleaningModel`, `DataValidator` y `recommender.py` son Python puro — no importan nada de Streamlit. Esto permite testearlos con pytest sin necesitar un navegador y facilita migrar la UI a otro framework en el futuro.

**Historial con undo:** cada operación guarda una copia del DataFrame antes de ejecutarse. El límite de 20 estados se gestiona con un `deque(maxlen=20)` en O(1). Implementado como pila LIFO.

**IA como capa opcional:** las recomendaciones locales son determinísticas y funcionan siempre. La IA de Groq es un enriquecimiento opcional que no bloquea el flujo principal si falta la API key o hay un error de red.

**Autodetección de CSV:** el parser prueba 12 combinaciones (3 encodings × 4 separadores) y acepta la primera que produzca más de una columna. Funciona con la mayoría de archivos del mundo real sin configuración.

### Lo que aprendí

- Gestión de estado reactivo en Streamlit con `st.session_state` para evitar recargas innecesarias
- Uso de `@st.cache_data` para cachear operaciones costosas sin que el usuario note la latencia
- Diseño de APIs que devuelven `(bool, str)` en lugar de lanzar excepciones, simplificando el manejo de errores en la capa de UI
- Integración de LLMs como capa de valor añadido sin crear dependencia dura

---

## Licencia

MIT — ver [LICENSE](LICENSE)
