"""
Recommender
Genera recomendaciones de limpieza a partir de un DiagnosticReport.
Motor de reglas local + Groq API gratuita (llama3).
"""
import os
from typing import List
from model.data_validator import DiagnosticReport

# ── Groq API (gratuita, sin tarjeta) ────────────────────────────────────────
# Configura tu clave mediante variable de entorno (NUNCA hardcodear en código):
#   Windows CMD:  set GROQ_API_KEY=gsk_...
#   PowerShell:   $env:GROQ_API_KEY = "gsk_..."
#   Linux/Mac:    export GROQ_API_KEY=gsk_...
# 1. Crea cuenta en: https://console.groq.com
# 2. Genera una API key en: https://console.groq.com/keys
# 3. Instala el paquete:  pip install groq
GROQ_MODEL = "llama-3.1-8b-instant"
# ────────────────────────────────────────────────────────────────────────────


def _build_context(report: DiagnosticReport) -> str:
    """Convierte un DiagnosticReport en texto plano para el prompt de la IA.

    Args:
        report: Reporte de diagnóstico del dataset.

    Returns:
        Cadena de texto con el resumen del dataset y el detalle por columna,
        lista para incluirse en el prompt de Groq.
    """
    lines = [
        f"Dataset: {report.total_rows} filas, {report.total_cols} columnas.",
        f"Filas duplicadas: {report.duplicate_rows}.",
        f"Total de valores nulos: {report.total_nulls}.",
        "Detalle por columna:",
    ]
    for col in report.columns:
        lines.append(
            f"  - {col.name} ({col.dtype}): "
            f"{col.null_count} nulos ({col.null_pct}%), "
            f"{col.unique_count} valores únicos."
        )
    return "\n".join(lines)


def get_ai_recommendation(report: DiagnosticReport) -> str:
    """Llama a Groq para obtener recomendaciones en lenguaje natural.

    Requiere que la variable de entorno ``GROQ_API_KEY`` esté configurada.
    Si no lo está, retorna cadena vacía sin hacer ninguna llamada de red.
    Los errores de red o de la API se traducen en mensajes legibles en lugar
    de propagar excepciones.

    Args:
        report: Reporte de diagnóstico con métricas del dataset.

    Returns:
        Texto con 3–5 recomendaciones priorizadas generadas por el LLM,
        un mensaje de error legible entre corchetes, o cadena vacía si no
        hay API key configurada.
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return ""
    try:
        from groq import Groq  # pip install groq
        client = Groq(api_key=api_key)
        prompt = (
            "Eres un experto en limpieza y calidad de datos. "
            "Analiza el siguiente reporte de un dataset y proporciona "
            "entre 3 y 5 recomendaciones concretas, breves y priorizadas en español. "
            "Usa viñetas y sé directo.\n\n"
            + _build_context(report)
        )
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
    except ImportError:
        return "[Instala groq para usar IA: pip install groq]"
    except Exception as exc:
        msg = str(exc).lower()
        if "429" in msg or "rate_limit" in msg or "rate limit" in msg:
            return "[IA: límite de solicitudes alcanzado. Intenta en unos segundos.]"
        if "401" in msg or "invalid_api_key" in msg or "authentication" in msg:
            return "[IA: API key inválida. Verifica la variable de entorno GROQ_API_KEY.]"
        return "[IA: error inesperado. Revisa la consola para más detalles.]"


def get_local_recommendations(report: DiagnosticReport) -> List[str]:
    """Genera recomendaciones basadas en reglas determinísticas (sin red).

    Evalúa el reporte en orden de prioridad: duplicados → nulos críticos →
    nulos moderados → columnas con un solo valor → columnas identificador.
    Si no se detecta ningún problema, retorna un mensaje de dataset limpio.

    Args:
        report: Reporte de diagnóstico del dataset.

    Returns:
        Lista de cadenas con recomendaciones accionables en español.
    """
    recs: List[str] = []

    if report.duplicate_rows > 0:
        recs.append(
            f"Elimina las {report.duplicate_rows} filas duplicadas "
            "con la operación 'Eliminar duplicados'."
        )

    for col in report.columns:
        if col.null_pct > 50:
            recs.append(
                f"'{col.name}' tiene {col.null_pct}% de nulos — "
                "considera eliminar esa columna."
            )
        elif col.null_pct > 0:
            strategy = "la moda" if col.dtype in ("object", "str") else "la media o la mediana"
            recs.append(
                f"Rellena los {col.null_count} nulos de '{col.name}' "
                f"({col.null_pct}%) con {strategy}."
            )

    for col in report.columns:
        if col.dtype in ("object", "str") and col.unique_count == 1 and report.total_rows > 1:
            recs.append(
                f"'{col.name}' tiene un único valor en todas las filas — "
                "evalúa si aporta información útil."
            )
        if col.unique_count == report.total_rows and report.total_rows > 1:
            recs.append(
                f"'{col.name}' tiene un valor distinto por fila — "
                "probablemente es un identificador único."
            )

    if not recs:
        recs.append(
            "El dataset luce limpio. Puedes proceder al análisis o exportarlo."
        )

    return recs


def get_recommendations(report: DiagnosticReport) -> dict:
    """Combina recomendaciones locales y de IA en un solo resultado.

    Args:
        report: Reporte de diagnóstico del dataset.

    Returns:
        Diccionario con claves:
        - ``"local"``: lista de recomendaciones determinísticas.
        - ``"ai"``: texto de Groq, cadena vacía si no hay API key.
    """
    return {
        "local": get_local_recommendations(report),
        "ai": get_ai_recommendation(report),
    }
