# DataCleaner

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-6C63FF)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-78%2F78%20passing-22C55E?logo=pytest&logoColor=white)](tests/)

Limpia, diagnostica y exporta datasets CSV/Excel desde el navegador, sin escribir código.

## Motivación

Los analistas dedican gran parte de su tiempo a limpiar datos antes de poder analizarlos: Excel no escala y Pandas exige saber programar. DataCleaner expone la potencia de Pandas en una interfaz visual con diagnóstico automático de calidad, recomendaciones de IA e historial reversible, para que cualquier persona pueda dejar un dataset listo para análisis en minutos.

## Características

- 8 operaciones de limpieza reversibles: tratar nulos, eliminar duplicados, normalizar texto, convertir tipos, renombrar columnas, filtrar filas, eliminar columnas y eliminar outliers (IQR).
- Diagnóstico de calidad con score de salud (0–100), conteo de nulos y duplicados por columna.
- Recomendaciones de limpieza locales (determinísticas) y opcionales con IA vía Groq (Llama 3).
- Visualizaciones interactivas: histogramas, violin plots, frecuencias categóricas y matriz de correlación de Pearson.
- Historial de cambios con deshacer (hasta 20 pasos) y log descargable.
- Carga con autodetección de separador y codificación en CSV; exportación a CSV y Excel.

## Stack tecnológico

- **Lenguaje:** Python 3.9+
- **UI:** Streamlit
- **Visualización:** Plotly
- **Procesamiento de datos:** Pandas
- **Lectura de Excel:** openpyxl (`.xlsx`), xlrd (`.xls`)
- **IA (opcional):** Groq API · Llama 3
- **Configuración:** python-dotenv
- **Tests:** pytest

## Primeros pasos

### Requisitos previos

- Python 3.9 o superior
- `pip` para instalar dependencias

### Configurar el archivo .env (opcional)

La IA es opcional; la app funciona sin ella. Para habilitar las recomendaciones con IA, copia la plantilla y añade tu clave gratuita de Groq ([console.groq.com](https://console.groq.com/keys)):

```bash
cp .env.example .env    # Linux / Mac
copy .env.example .env  # Windows
```

```env
GROQ_API_KEY=gsk_tu_clave_aqui
```

Sin `GROQ_API_KEY` definida, las recomendaciones locales siguen funcionando y la sección de IA simplemente queda deshabilitada.

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/DanielDrk07/datacleaner.git
cd datacleaner

# 2. Crear y activar un entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / Mac

# 3. Instalar dependencias
pip install -r requirements.txt
```

### Ejecución

```bash
streamlit run app.py
```

Abre el navegador en **http://localhost:8501**. En Windows también puedes ejecutar `run.bat`, que verifica Python, instala dependencias y arranca la app automáticamente.

## Estructura del proyecto

```
datacleaner/
├── app.py                      # Entry point: configuración y arranque de Streamlit
├── ui/
│   ├── styles.py               # CSS personalizado
│   ├── utils.py                # Constantes, helpers de sesión y funciones cacheadas
│   ├── sidebar.py              # Panel lateral con las operaciones de limpieza
│   └── tabs.py                 # Pestañas del área principal (datos, diagnóstico, etc.)
├── model/
│   ├── cleaning_model.py       # Motor de limpieza + historial undo (Pandas, sin UI)
│   ├── data_validator.py       # Diagnóstico de calidad — solo lectura
│   └── recommender.py          # Reglas locales + integración con Groq API
├── tests/
│   ├── test_cleaning_model.py  # Tests del motor de limpieza
│   ├── test_data_validator.py  # Tests del validador
│   └── test_recommender.py     # Tests del recomendador
├── .streamlit/config.toml      # Tema visual
├── .env.example                # Plantilla de variables de entorno
├── requirements.txt            # Dependencias
└── run.bat                     # Lanzador rápido para Windows
```

La capa `model/` es Python puro y no importa Streamlit, por lo que puede testearse de forma aislada con pytest.

## Uso

**Flujo en la interfaz:** carga un CSV o Excel desde el panel lateral, aplica operaciones de limpieza (cada una registra un paso reversible), revisa el diagnóstico de calidad y exporta el resultado a CSV o Excel.

**Uso de la capa de modelo desde Python** (sin levantar la UI):

```python
import pandas as pd
from model.cleaning_model import CleaningModel
from model.data_validator import DataValidator

df = pd.read_csv("datos.csv")

model = CleaningModel()
model.load(df)
model.drop_duplicates()
model.fill_nulls("edad", strategy="median")
model.normalize_text("ciudad")

# Diagnóstico de calidad
report = DataValidator().analyze(model.df)
print(report.total_rows, report.total_nulls, report.duplicate_rows)

# Deshacer la última operación
model.undo()
```

Ejecutar los tests:

```bash
pytest tests/ -v
```

## Licencia

MIT — ver [LICENSE](LICENSE).
