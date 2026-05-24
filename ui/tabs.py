import html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from model.recommender import get_recommendations, get_local_recommendations
from ui.utils import (
    get_df, cached_analyze, health_score, simplify_dtype, empty_state,
    df_as_str, cached_describe, cached_numeric_stats, cached_correlation,
    cached_histogram, cached_violin, cached_category_chart,
    COLOR_DANGER, COLOR_WARN, COLOR_SUCCESS, COLOR_PRIMARY,
)


def render_tabs() -> None:
    # ── Cabecera ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="app-header">
        <h1>✨ DataCleaner</h1>
        <p>Limpia, transforma y exporta tus datos de forma visual e intuitiva · Streamlit + Plotly</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Feedback toast ────────────────────────────────────────────────────────
    if st.session_state.feedback:
        msg, kind = st.session_state.feedback
        icons = {"success": "✅", "warning": "⚠️", "error": "❌", "info": "ℹ️"}
        st.toast(msg, icon=icons.get(kind, "ℹ️"))
        st.session_state.feedback = None

    # ── Métricas rápidas ──────────────────────────────────────────────────────
    df     = get_df()
    report = cached_analyze(df)
    score  = health_score(report)

    m1, m2, m3 = st.columns(3)
    m4, m5     = st.columns(2)
    with m1: st.metric("📋 Filas",    f"{report.total_rows:,}")
    with m2: st.metric("📊 Columnas", report.total_cols)
    with m3:
        icon = "🟢" if score >= 70 else ("🟡" if score >= 40 else "🔴")
        st.metric(f"{icon} Salud", f"{score}/100")
    with m4: st.metric("⚠️ Nulos", f"{report.total_nulls:,}",
                       delta=f"-{report.total_nulls:,}" if report.total_nulls else None,
                       delta_color="inverse")
    with m5: st.metric("🔁 Duplicados", f"{report.duplicate_rows:,}",
                       delta=f"-{report.duplicate_rows:,}" if report.duplicate_rows else None,
                       delta_color="inverse")

    st.markdown("")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_datos, tab_diag, tab_stats, tab_corr, tab_hist = st.tabs([
        "📊   Vista de Datos",
        "🔍   Diagnóstico & IA",
        "📈   Estadísticas",
        "🔗   Correlaciones",
        "📋   Historial de Cambios",
    ])

    # ══ TAB 1: Vista de Datos ═════════════════════════════════════════════════
    with tab_datos:
        search = st.text_input(
            "Buscar en datos", placeholder="🔎  Filtra filas que contengan cualquier texto...",
            label_visibility="hidden", key="search_data",
        )
        display_df = df
        if search.strip():
            mask = df_as_str(df).apply(
                lambda c: c.str.contains(search, case=False, na=False, regex=False)
            ).any(axis=1)
            display_df = df[mask]
            st.caption(f"Mostrando **{len(display_df):,}** de **{len(df):,}** filas")

        dynamic_height = min(600, max(200, len(display_df) * 35 + 38))
        st.dataframe(display_df, use_container_width=True, height=dynamic_height)
        st.caption("💡 Las operaciones de limpieza están en el **panel izquierdo**. "
                   "La tabla se actualiza automáticamente después de cada operación.")

    # ══ TAB 2: Diagnóstico & IA ═══════════════════════════════════════════════
    with tab_diag:
        col_gauge, col_issues = st.columns([1, 1], gap="large")

        with col_gauge:
            gauge_color = COLOR_SUCCESS if score >= 70 else (COLOR_WARN if score >= 40 else COLOR_DANGER)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                number={"suffix": "/100", "font": {"size": 28, "color": gauge_color}},
                title={"text": "Salud del Dataset", "font": {"size": 14, "color": "#374151"}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#CCC"},
                    "bar": {"color": gauge_color, "thickness": 0.3},
                    "bgcolor": "white",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0,  40], "color": "#FFF0F0"},
                        {"range": [40, 70], "color": "#FFFBF0"},
                        {"range": [70,100], "color": "#F0FFF4"},
                    ],
                    "threshold": {
                        "line": {"color": gauge_color, "width": 3},
                        "thickness": 0.8, "value": score,
                    },
                },
            ))
            fig_gauge.update_layout(height=230, margin=dict(t=30, b=0, l=20, r=20),
                                    paper_bgcolor="white")
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_issues:
            st.markdown("#### Resumen de Problemas")
            n_issues = 0
            if report.total_nulls > 0:
                st.warning(f"⚠️ **{report.total_nulls:,} valores nulos** en el dataset")
                n_issues += 1
            if report.duplicate_rows > 0:
                st.warning(f"⚠️ **{report.duplicate_rows:,} filas duplicadas** detectadas")
                n_issues += 1
            critical = [c for c in report.columns if c.null_pct > 50]
            if critical:
                names = ", ".join(f"`{c.name}`" for c in critical)
                st.error(f"🚨 Columnas críticas (>50% nulos): {names}")
                n_issues += 1
            if n_issues == 0:
                st.success("✅ ¡El dataset no tiene problemas detectados! Listo para exportar.")

            type_counts: dict[str, int] = {}
            for c in report.columns:
                t = simplify_dtype(c.dtype)
                type_counts[t] = type_counts.get(t, 0) + 1

            fig_pie = px.pie(
                values=list(type_counts.values()),
                names=list(type_counts.keys()),
                title="Distribución de tipos de datos",
                color_discrete_sequence=["#6C63FF", "#4ECDC4", "#FF6B6B", "#FFD93D", "#A8E6CF"],
                hole=0.45,
            )
            fig_pie.update_layout(height=220, margin=dict(t=35, b=5, l=0, r=0),
                                  showlegend=False, paper_bgcolor="white")
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")

        col_with_nulls = [c for c in report.columns if c.null_count > 0]
        if col_with_nulls:
            st.markdown("#### Valores Nulos por Columna")
            null_df = pd.DataFrame({
                "Columna": [c.name for c in col_with_nulls],
                "% Nulos": [c.null_pct for c in col_with_nulls],
                "# Nulos": [c.null_count for c in col_with_nulls],
            }).sort_values("% Nulos", ascending=True)

            fig_bar = px.bar(
                null_df, x="% Nulos", y="Columna", orientation="h",
                text="# Nulos", color="% Nulos",
                color_continuous_scale=["#D4EDDA", "#FFF3CD", "#F8D7DA"],
                range_color=[0, 100],
            )
            fig_bar.update_traces(textposition="outside", marker_line_width=0)
            fig_bar.update_layout(
                height=max(180, len(col_with_nulls) * 38 + 60),
                margin=dict(t=10, b=10, l=10, r=40),
                coloraxis_showscale=False,
                xaxis=dict(range=[0, 115], title="% de valores nulos"),
                paper_bgcolor="white", plot_bgcolor="white",
            )
            fig_bar.update_xaxes(showgrid=True, gridcolor="#E5E7EB",
                                 tickfont=dict(color="#374151"), title_font=dict(color="#374151"))
            fig_bar.update_yaxes(tickfont=dict(color="#374151"))
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.success("✅ Ninguna columna tiene valores nulos")

        st.markdown("---")

        st.markdown("#### Detalle por Columna")
        st.markdown('<ul role="list" style="list-style:none;padding:0;margin:0">', unsafe_allow_html=True)
        for col_rep in report.columns:
            css_class   = "danger" if col_rep.null_pct > 50 else ("warning" if col_rep.null_pct > 0 else "good")
            bar_color   = COLOR_DANGER if col_rep.null_pct > 50 else (COLOR_WARN if col_rep.null_pct > 0 else COLOR_SUCCESS)
            dtype_label = simplify_dtype(col_rep.dtype)
            sample_str  = html.escape(", ".join(str(v)[:25] for v in col_rep.sample_values)) \
                          if col_rep.sample_values else "—"
            col_name    = html.escape(col_rep.name)

            st.markdown(f"""
            <li role="listitem" class="col-card {css_class}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <b style="color:#111827;font-size:0.95rem">{col_name}</b>
                        &nbsp;<span class="type-badge">{dtype_label}</span>
                        &nbsp;<span style="color:#6B7280;font-size:0.78rem">{col_rep.unique_count} únicos</span>
                    </div>
                    <div style="text-align:right;font-size:0.82rem;color:#374151">
                        {col_rep.null_count} nulos
                        <b style="color:{bar_color}"> ({col_rep.null_pct}%)</b>
                    </div>
                </div>
                <div style="margin-top:8px;background:#E5E7EB;border-radius:4px;height:6px;overflow:hidden">
                    <div style="width:{col_rep.null_pct}%;background:{bar_color};height:6px;border-radius:4px"></div>
                </div>
                <div style="margin-top:5px;color:#6B7280;font-size:0.78rem">
                    Muestra: <span style="color:#1F2937">{sample_str}</span>
                </div>
            </li>
            """, unsafe_allow_html=True)
        st.markdown('</ul>', unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("#### 💡 Recomendaciones de Limpieza")
        local_recs = get_local_recommendations(report)
        st.markdown("**Análisis automático:**")
        for rec in local_recs:
            st.markdown(f'<div class="rec-local">• {html.escape(rec)}</div>', unsafe_allow_html=True)

        st.markdown("")
        st.markdown("**Recomendaciones con Inteligencia Artificial (Groq · Llama 3):**")

        ai_result = st.session_state.ai_result
        col_btn, col_info = st.columns([1, 2])
        with col_btn:
            ai_clicked = st.button("🤖 Pedir recomendaciones IA", use_container_width=True)
        with col_info:
            st.caption("Usa la API gratuita de Groq. Requiere la variable de entorno `GROQ_API_KEY`.")

        if ai_clicked:
            with st.spinner("Consultando IA..."):
                recs = get_recommendations(report)
                st.session_state.ai_result   = recs["ai"]
                st.session_state.ai_for_file = st.session_state.filename
            st.rerun()

        if ai_result:
            if ai_result.startswith("["):
                st.warning(ai_result)
            else:
                st.markdown(f'<div class="rec-ai">{html.escape(ai_result)}</div>', unsafe_allow_html=True)
                if st.session_state.ai_for_file:
                    st.caption(f"Análisis para: {st.session_state.ai_for_file}")

    # ══ TAB 3: Estadísticas ═══════════════════════════════════════════════════
    with tab_stats:
        numeric_cols     = df.select_dtypes(include="number").columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        # Resumen general
        st.markdown("#### 📋 Resumen General")
        desc_df = cached_describe(df)
        if desc_df is not None:
            def _col_gradient(s: pd.Series) -> list[str]:
                lo, hi = s.min(), s.max()
                out = []
                for v in s:
                    if pd.isna(v) or hi == lo:
                        out.append("")
                        continue
                    t  = (v - lo) / (hi - lo)
                    r  = int(239 - t * 209)
                    g  = int(246 - t * 182)
                    b  = int(255 - t * 80)
                    tc = "#111827" if t < 0.55 else "white"
                    out.append(f"background-color: rgb({r},{g},{b}); color: {tc}")
                return out
            st.dataframe(
                desc_df.style.apply(_col_gradient, axis=0).format("{:.2f}"),
                use_container_width=True,
            )
            st.caption("Estadísticas descriptivas de todas las columnas numéricas, redondeadas a 2 decimales.")
        else:
            st.info("No hay columnas numéricas para mostrar el resumen.")

        st.markdown("---")

        # Distribuciones
        st.markdown("#### 📊 Distribuciones")
        if not numeric_cols:
            st.info("No hay columnas numéricas en el dataset.")
        else:
            _col_sel, _col_bins = st.columns([2, 1])
            with _col_sel:
                hist_col = st.selectbox("Columna numérica", numeric_cols, key="hist_col")
            with _col_bins:
                hist_bins = st.slider("Barras", min_value=5, max_value=100, value=30, key="hist_bins")
            st.plotly_chart(cached_histogram(df, hist_col, hist_bins), use_container_width=True)

        st.markdown("---")

        # Box plot & violín
        st.markdown("#### 📦 Box Plot & Violín")
        if not numeric_cols:
            st.info("No hay columnas numéricas en el dataset.")
        else:
            box_col = st.selectbox("Columna numérica", numeric_cols, key="box_col")
            st.plotly_chart(cached_violin(df, box_col), use_container_width=True)
            st.caption("Los puntos fuera de los bigotes son outliers. "
                       "La línea central es la mediana; el rombo es la media.")

        st.markdown("---")

        # Frecuencias categóricas
        st.markdown("#### 🏷️ Frecuencias Categóricas")
        if not categorical_cols:
            st.info("No hay columnas categóricas (texto u objeto) en el dataset.")
        else:
            cat_col = st.selectbox("Columna categórica", categorical_cols, key="cat_col")
            st.plotly_chart(cached_category_chart(df, cat_col), use_container_width=True)

        st.markdown("---")

        # Comparación de medias
        st.markdown("#### 📈 Comparación de Medias")
        if not numeric_cols:
            st.info("No hay columnas numéricas en el dataset.")
        else:
            rows_m  = cached_numeric_stats(df)
            comp_df = pd.DataFrame(rows_m)

            _y_max     = comp_df["Media"].max()
            _y_min     = min(0, comp_df["Media"].min())
            _threshold = _y_max * 0.08
            comp_df["_label"] = comp_df["Media"].apply(
                lambda v: f"{v:,.3f}" if v >= _threshold else ""
            )

            fig_medias = px.bar(
                comp_df, x="Columna", y="Media",
                color="Distribución",
                color_discrete_map={
                    "↑ Sesgada +": COLOR_SUCCESS,
                    "↓ Sesgada −": COLOR_DANGER,
                    "≈ Simétrica":  "#6B7280",
                },
                text="_label",
                title="Media por columna numérica",
            )
            fig_medias.update_traces(
                texttemplate="%{text}",
                textposition="inside",
                insidetextanchor="end",
                textfont=dict(color="white", size=11),
            )
            fig_medias.update_layout(
                height=420,
                margin=dict(t=50, b=20, l=20, r=20),
                paper_bgcolor="white", plot_bgcolor="white",
                xaxis=dict(tickfont=dict(color="#374151"), title=None, showgrid=False),
                yaxis=dict(tickfont=dict(color="#374151"), title="Media",
                           range=[_y_min, _y_max * 1.05],
                           showgrid=True, gridcolor="#E5E7EB"),
                legend=dict(title="Distribución", orientation="h", yanchor="bottom", y=1.02, x=0),
            )
            st.plotly_chart(fig_medias, use_container_width=True)

            st.markdown("#### Detalle por columna")
            st.dataframe(
                comp_df.style.map(
                    lambda v: "color: #10B981; font-weight:600" if v == "↑ Sesgada +"
                    else ("color: #EF4444; font-weight:600" if v == "↓ Sesgada −" else "color: #6B7280"),
                    subset=["Distribución"],
                ).format({"Media": "{:,.4f}", "Mediana": "{:,.4f}", "Desv. Est.": "{:,.4f}"}),
                use_container_width=True,
                hide_index=True,
            )

    # ══ TAB 4: Correlaciones ══════════════════════════════════════════════════
    with tab_corr:
        numeric_cols_c = df.select_dtypes(include="number").columns.tolist()

        if len(numeric_cols_c) < 2:
            st.info("Necesitas al menos 2 columnas numéricas para calcular correlaciones.")
        else:
            selected_corr = st.multiselect(
                "Selecciona las columnas a analizar",
                options=numeric_cols_c,
                default=numeric_cols_c[:min(8, len(numeric_cols_c))],
                key="corr_cols",
                help="Selecciona 2 o más columnas numéricas",
            )

            if len(selected_corr) < 2:
                st.warning("Selecciona al menos 2 columnas para ver la matriz de correlación.")
            else:
                corr_matrix  = cached_correlation(df, tuple(selected_corr))
                _corr_vals   = corr_matrix.values
                _corr_labels = corr_matrix.columns.tolist()
                _annotations = []
                for _i, _row in enumerate(_corr_vals):
                    for _j, _val in enumerate(_row):
                        _fc = "white" if abs(_val) > 0.45 else "#374151"
                        _annotations.append(dict(
                            x=_corr_labels[_j], y=_corr_labels[_i],
                            text=f"{_val:.3f}",
                            showarrow=False,
                            font=dict(color=_fc, size=12),
                            xref="x", yref="y",
                        ))

                fig_corr = go.Figure(data=go.Heatmap(
                    z=_corr_vals,
                    x=_corr_labels,
                    y=_corr_labels,
                    colorscale=[
                        [0.0,  "#B91C1C"],
                        [0.25, "#FCA5A5"],
                        [0.5,  "#F1F5F9"],
                        [0.75, "#93C5FD"],
                        [1.0,  "#1E40AF"],
                    ],
                    zmin=-1, zmax=1,
                    xgap=3, ygap=3,
                    colorbar=dict(
                        title=dict(text="r", side="right"),
                        tickvals=[-1, -0.7, -0.4, 0, 0.4, 0.7, 1],
                        ticktext=["-1", "-0.7", "-0.4", "0", "0.4", "0.7", "1"],
                        len=0.85, thickness=14, outlinewidth=0,
                    ),
                ))
                fig_corr.update_layout(
                    title=dict(text=f"Correlación de Pearson — {len(selected_corr)} columnas",
                               font=dict(size=15, color="#1F2937")),
                    annotations=_annotations,
                    height=max(380, len(selected_corr) * 60 + 80),
                    margin=dict(t=55, b=20, l=20, r=100),
                    paper_bgcolor="white", plot_bgcolor="white",
                    xaxis=dict(tickfont=dict(color="#374151"), side="bottom"),
                    yaxis=dict(tickfont=dict(color="#374151"), autorange="reversed"),
                )
                st.plotly_chart(fig_corr, use_container_width=True)

                st.markdown("#### Referencia de interpretación")
                col_r1, col_r2, col_r3 = st.columns(3)
                with col_r1:
                    st.markdown("""
                    **Correlación positiva** 🔵
                    - `r ≥ 0.9` — Muy fuerte
                    - `r ≥ 0.7` — Fuerte
                    - `r ≥ 0.4` — Moderada
                    """)
                with col_r2:
                    st.markdown("""
                    **Sin correlación** ⚪
                    - `|r| < 0.4` — Débil / nula
                    - `r = 0` — Sin relación lineal
                    """)
                with col_r3:
                    st.markdown("""
                    **Correlación negativa** 🔴
                    - `r ≤ -0.4` — Moderada
                    - `r ≤ -0.7` — Fuerte
                    - `r ≤ -0.9` — Muy fuerte
                    """)

    # ══ TAB 5: Historial ══════════════════════════════════════════════════════
    with tab_hist:
        change_log = st.session_state.model.change_log

        if change_log:
            st.markdown(f"#### {len(change_log)} operación(es) realizadas")
            st.caption("Las más recientes aparecen primero. Deshaz la última con **↩ Deshacer** en el panel izquierdo.")

            st.markdown('<ol role="list" style="list-style:none;padding:0;margin:0">', unsafe_allow_html=True)
            for idx, entry in enumerate(reversed(change_log)):
                num = len(change_log) - idx
                st.markdown(f"""
                <li role="listitem" class="log-entry">
                    <span style="color:#6C63FF;font-weight:700">#{num}</span>
                    &nbsp; {html.escape(entry)}
                </li>
                """, unsafe_allow_html=True)
            st.markdown('</ol>', unsafe_allow_html=True)

            st.markdown("")
            log_text = "\n".join(f"{i+1:02d}. {e}" for i, e in enumerate(change_log))
            st.download_button("📥 Descargar Log Completo (.txt)",
                               data=log_text.encode("utf-8"),
                               file_name="log_cambios.txt", mime="text/plain")
        else:
            st.markdown(empty_state("📋",
                "Aún no se han realizado operaciones.",
                "Cada limpieza que apliques quedará registrada aquí."),
                unsafe_allow_html=True)
