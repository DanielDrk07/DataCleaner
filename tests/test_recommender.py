"""
Tests unitarios de recommender.py — motor de reglas local y mocking de IA.
Ejecutar con: pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
from unittest.mock import patch

from model.data_validator import DataValidator
from model.recommender import get_local_recommendations, get_recommendations
import model.recommender as rec_module


def _make_report(df: pd.DataFrame):
    return DataValidator().analyze(df)


@pytest.fixture
def report_con_nulos():
    df = pd.DataFrame({
        "nombre": ["Ana", None,  "Bob"],
        "edad":   [25,   30,    None],
        "ciudad": ["Bogota", "Medellin", "Cali"],
    })
    return _make_report(df)


@pytest.fixture
def report_con_duplicados():
    df = pd.DataFrame({
        "nombre": ["Ana", "Ana", "Bob"],
        "edad":   [25,    25,    30],
    })
    return _make_report(df)


@pytest.fixture
def report_limpio():
    # Columnas con unique_count < total_rows para no activar la regla
    # "identificador único" (que impediría el mensaje fallback "limpio").
    df = pd.DataFrame({
        "estado": ["activo",   "inactivo", "activo",   "inactivo"],
        "region": ["norte",    "sur",      "sur",      "norte"],
    })
    return _make_report(df)


@pytest.fixture
def report_columna_critica():
    """Columna con >50 % de nulos — debe recomendar eliminarla."""
    df = pd.DataFrame({
        "col_critica": [None, None, "algo", None, None],
        "normal":      [1,    2,    3,      4,    5],
    })
    return _make_report(df)


# ══ Recomendaciones por nulos ══════════════════════════════════════════════════

class TestLocalRecsNulos:
    def test_genera_recomendacion_cuando_hay_nulos(self, report_con_nulos):
        recs = get_local_recommendations(report_con_nulos)
        assert any("nulo" in r.lower() for r in recs)

    def test_columna_critica_sugiere_eliminar_columna(self, report_columna_critica):
        recs = get_local_recommendations(report_columna_critica)
        assert any("eliminar" in r.lower() and "columna" in r.lower() for r in recs)

    def test_columna_object_sugiere_moda(self, report_con_nulos):
        # "nombre" es dtype object con nulos → estrategia "la moda"
        recs = get_local_recommendations(report_con_nulos)
        assert any("moda" in r.lower() for r in recs)

    def test_columna_numerica_sugiere_media_o_mediana(self, report_con_nulos):
        # "edad" es numérica con nulos → estrategia "la media o la mediana"
        recs = get_local_recommendations(report_con_nulos)
        assert any("media" in r.lower() for r in recs)

    def test_menciona_nombre_de_cada_columna_con_nulos(self, report_con_nulos):
        recs = get_local_recommendations(report_con_nulos)
        assert any("nombre" in r for r in recs)
        assert any("edad"   in r for r in recs)

    def test_no_genera_rec_de_nulos_para_columna_limpia(self, report_con_nulos):
        recs = get_local_recommendations(report_con_nulos)
        # "ciudad" no tiene nulos, no debe aparecer en ninguna rec de relleno
        assert not any("ciudad" in r and "nulo" in r.lower() for r in recs)


# ══ Recomendaciones por duplicados ════════════════════════════════════════════

class TestLocalRecsDuplicados:
    def test_genera_recomendacion_cuando_hay_duplicados(self, report_con_duplicados):
        recs = get_local_recommendations(report_con_duplicados)
        assert any("duplicad" in r.lower() for r in recs)

    def test_menciona_cantidad_exacta_de_duplicados(self, report_con_duplicados):
        n_dup = str(report_con_duplicados.duplicate_rows)
        recs = get_local_recommendations(report_con_duplicados)
        assert any(n_dup in r for r in recs)

    def test_recomendacion_duplicados_aparece_primero(self, report_con_duplicados):
        # La regla de duplicados se evalúa antes que las de nulos
        recs = get_local_recommendations(report_con_duplicados)
        assert "duplicad" in recs[0].lower()


# ══ Dataset limpio ════════════════════════════════════════════════════════════

class TestLocalRecsLimpio:
    def test_retorna_al_menos_una_recomendacion(self, report_limpio):
        recs = get_local_recommendations(report_limpio)
        assert len(recs) >= 1

    def test_mensaje_de_dataset_limpio(self, report_limpio):
        recs = get_local_recommendations(report_limpio)
        assert any("limpio" in r.lower() or "exportar" in r.lower() for r in recs)

    def test_no_menciona_nulos_cuando_no_los_hay(self, report_limpio):
        recs = get_local_recommendations(report_limpio)
        assert not any("nulo" in r.lower() for r in recs)

    def test_no_menciona_duplicados_cuando_no_los_hay(self, report_limpio):
        recs = get_local_recommendations(report_limpio)
        assert not any("duplicad" in r.lower() for r in recs)


# ══ Reglas especiales de estructura ═══════════════════════════════════════════

class TestLocalRecsEspeciales:
    def test_detecta_columna_identificador_unico(self):
        # unique_count == total_rows → probablemente ID
        df = pd.DataFrame({
            "id":    [1, 2, 3, 4, 5],
            "valor": ["a", "b", "c", "d", "e"],
        })
        recs = get_local_recommendations(_make_report(df))
        assert any("identificador" in r.lower() for r in recs)

    def test_detecta_columna_con_un_solo_valor(self):
        # dtype==object, unique_count==1, total_rows>1 → valor constante
        df = pd.DataFrame({
            "pais":   ["Colombia", "Colombia", "Colombia"],
            "ciudad": ["Bogota", "Medellin", "Cali"],
        })
        recs = get_local_recommendations(_make_report(df))
        assert any("único valor" in r.lower() for r in recs)

    def test_no_aplica_regla_identificador_con_una_sola_fila(self):
        # total_rows == 1 → la condición total_rows > 1 no se cumple
        df = pd.DataFrame({"id": [42], "val": ["x"]})
        recs = get_local_recommendations(_make_report(df))
        assert not any("identificador" in r.lower() for r in recs)

    def test_no_aplica_regla_valor_unico_con_una_sola_fila(self):
        df = pd.DataFrame({"pais": ["Colombia"]})
        recs = get_local_recommendations(_make_report(df))
        assert not any("único valor" in r.lower() for r in recs)


# ══ get_recommendations — integración y mocking de IA ═════════════════════════

class TestGetRecommendationsMocking:
    def test_sin_api_key_ai_devuelve_cadena_vacia(self, report_limpio):
        """GROQ_API_KEY no configurada → get_ai_recommendation retorna '' sin red."""
        # patch.dict asegura que GROQ_API_KEY no esté presente sin importar el entorno
        env_sin_key = {k: v for k, v in os.environ.items() if k != "GROQ_API_KEY"}
        with patch.dict(os.environ, env_sin_key, clear=True):
            result = get_recommendations(report_limpio)
            assert result["ai"] == ""

    def test_mockea_llamada_a_groq_y_propaga_resultado(self, report_limpio):
        """Mock de get_ai_recommendation: se llama una vez y su valor llega al dict."""
        with patch("model.recommender.get_ai_recommendation",
                   return_value="recomendacion simulada") as mock_fn:
            result = get_recommendations(report_limpio)
            mock_fn.assert_called_once_with(report_limpio)
            assert result["ai"] == "recomendacion simulada"

    def test_local_siempre_presente_independiente_de_ia(self, report_limpio):
        with patch("model.recommender.get_ai_recommendation", return_value=""):
            result = get_recommendations(report_limpio)
            assert "local" in result
            assert isinstance(result["local"], list)
            assert len(result["local"]) >= 1

    def test_retorna_exactamente_las_claves_correctas(self, report_limpio):
        with patch("model.recommender.get_ai_recommendation", return_value=""):
            result = get_recommendations(report_limpio)
            assert set(result.keys()) == {"local", "ai"}

    def test_local_con_datos_reales_cuando_hay_nulos(self, report_con_nulos):
        with patch("model.recommender.get_ai_recommendation", return_value="mock"):
            result = get_recommendations(report_con_nulos)
            assert any("nulo" in r.lower() for r in result["local"])
