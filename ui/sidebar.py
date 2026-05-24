import html
import streamlit as st
from io import BytesIO

from ui.utils import (
    get_df, has_data, set_ok, set_warn, set_err,
    empty_state, load_uploaded_file,
)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## ✨ DataCleaner")
        st.caption("v2.0")
        st.markdown("---")

        # ── Carga de archivo ──────────────────────────────────────────────
        st.markdown("### 📂 Cargar Archivo")
        uploaded = st.file_uploader(
            "CSV o Excel",
            type=["csv", "xlsx", "xls"],
            label_visibility="hidden",
        )

        if uploaded:
            file_id = f"{uploaded.name}_{uploaded.size}"
            if st.session_state.loaded_file_id != file_id:
                try:
                    df_loaded, fname = load_uploaded_file(uploaded)
                    st.session_state.model.load(df_loaded)
                    st.session_state.filename       = fname
                    st.session_state.loaded_file_id = file_id
                    st.session_state.ai_result      = None
                    set_ok(f"✅ **{fname}** cargado — {len(df_loaded):,} filas × {len(df_loaded.columns)} columnas")
                    st.rerun()
                except Exception as exc:
                    set_err(f"❌ Error al cargar: {exc}")

        if not has_data():
            st.markdown(empty_state("☝", "Carga un archivo para comenzar"),
                        unsafe_allow_html=True)
            st.stop()

        # ── Info del archivo ──────────────────────────────────────────────
        df_current = get_df()
        st.markdown(f"""
        <div style="background:#252639;padding:10px 14px;border-radius:8px;
                    font-size:0.82rem;border:1px solid #3A3C54;">
            <b style="color:#A8AACC">📄 {html.escape(st.session_state.filename)}</b><br>
            <span style="color:#6C63FF;font-weight:600">{len(df_current):,}</span>
            <span style="color:#9EA3C0"> filas &nbsp;·&nbsp; </span>
            <span style="color:#6C63FF;font-weight:600">{len(df_current.columns)}</span>
            <span style="color:#9EA3C0"> columnas</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")

        # ── Deshacer ──────────────────────────────────────────────────────
        if st.button("↩  Deshacer última operación",
                     disabled=not st.session_state.model.can_undo(),
                     use_container_width=True):
            op = st.session_state.model.undo()
            set_ok(f"↩ Deshecho: **{op}**")
            st.rerun()

        st.markdown("---")
        st.markdown("### 🛠 Operaciones")

        cols = list(get_df().columns)

        # 1 ── Tratar Nulos ────────────────────────────────────────────────
        with st.expander("🔸 Tratar Nulos"):
            col_options = ["— todas las columnas —"] + cols
            null_col = st.selectbox("Columna", col_options, key="null_col")
            action   = st.radio("Acción", ["Eliminar filas con nulos", "Rellenar nulos"],
                                key="null_act", horizontal=False)

            if action == "Rellenar nulos":
                strat = st.selectbox("Estrategia", ["media", "mediana", "moda", "personalizado"],
                                     key="null_strat")
                custom_val = st.text_input("Valor personalizado", key="null_custom") \
                             if strat == "personalizado" else ""
                if st.button("Rellenar", key="btn_fill", use_container_width=True):
                    target = None if null_col.startswith("—") else null_col
                    if not target:
                        set_warn("Selecciona una columna específica para rellenar")
                    else:
                        with st.spinner("Procesando..."):
                            n = st.session_state.model.fill_nulls(target, strat, custom_value=custom_val or None)
                        set_ok(f"✅ {n} valores rellenos en **{target}**")
                    st.rerun()
            else:
                st.caption("⚠️ Se eliminarán las filas que tengan nulos.")
                confirm_null = st.checkbox("Confirmar eliminación", key="confirm_null_drop")
                if st.button("Eliminar filas con nulos", key="btn_drop_null",
                             use_container_width=True, disabled=not confirm_null):
                    target = None if null_col.startswith("—") else null_col
                    with st.spinner("Procesando..."):
                        n = st.session_state.model.drop_nulls(target)
                    set_ok(f"✅ {n} filas eliminadas")
                    st.rerun()

        # 2 ── Duplicados ──────────────────────────────────────────────────
        with st.expander("🔁 Eliminar Duplicados"):
            st.caption("Elimina filas completamente idénticas en todo el dataset.")
            confirm_dup = st.checkbox("Confirmar eliminación", key="confirm_dup")
            if st.button("Eliminar Duplicados", key="btn_dup",
                         use_container_width=True, disabled=not confirm_dup):
                with st.spinner("Procesando..."):
                    n = st.session_state.model.drop_duplicates()
                set_ok(f"✅ {n} filas duplicadas eliminadas")
                st.rerun()

        # 3 ── Normalizar texto ────────────────────────────────────────────
        with st.expander("🔤 Normalizar Texto"):
            norm_col   = st.selectbox("Columna de texto", cols, key="norm_col")
            norm_lower = st.checkbox("Convertir a minúsculas",          value=True, key="norm_lower")
            norm_strip = st.checkbox("Eliminar espacios inicio/fin",    value=True, key="norm_strip")
            norm_extra = st.checkbox("Eliminar espacios extra internos", value=True, key="norm_extra")
            if st.button("Normalizar", key="btn_norm", use_container_width=True):
                with st.spinner("Normalizando..."):
                    n = st.session_state.model.normalize_text(norm_col, norm_lower, norm_strip, norm_extra)
                set_ok(f"✅ {n} celdas normalizadas en **{norm_col}**")
                st.rerun()

        # 4 ── Convertir tipo ──────────────────────────────────────────────
        with st.expander("🔄 Convertir Tipo de Dato"):
            type_col    = st.selectbox("Columna", cols, key="type_col")
            type_target = st.selectbox("Convertir a", ["int", "float", "str", "datetime"], key="type_target")
            if st.button("Convertir", key="btn_type", use_container_width=True):
                with st.spinner("Convirtiendo..."):
                    ok, msg = st.session_state.model.convert_type(type_col, type_target)
                (set_ok if ok else set_err)(("✅ " if ok else "❌ ") + msg)
                st.rerun()

        # 5 ── Renombrar columna ───────────────────────────────────────────
        with st.expander("✏️ Renombrar Columna"):
            rename_old = st.selectbox("Columna a renombrar", cols, key="rename_old")
            rename_new = st.text_input("Nuevo nombre", placeholder="nombre_nuevo", key="rename_new")
            if st.button("Renombrar", key="btn_rename", use_container_width=True):
                if rename_new.strip():
                    with st.spinner("Renombrando..."):
                        ok, msg = st.session_state.model.rename_column(rename_old, rename_new.strip())
                    (set_ok if ok else set_err)(("✅ " if ok else "❌ ") + msg)
                    st.rerun()
                else:
                    set_warn("⚠️ Escribe un nombre válido")

        # 6 ── Filtrar / eliminar filas ────────────────────────────────────
        with st.expander("🔍 Filtrar / Eliminar Filas"):
            filter_col = st.selectbox("Columna", cols, key="filter_col")
            filter_op  = st.selectbox("Operador",
                                      ["==", "!=", ">", "<", ">=", "<=", "contains", "startswith"],
                                      key="filter_op")
            filter_val = st.text_input("Valor", key="filter_val")
            st.caption("⚠️ Se eliminarán las filas que **cumplan** la condición.")
            confirm_filter = st.checkbox("Confirmar eliminación", key="confirm_filter")
            if st.button("Eliminar filas filtradas", key="btn_filter",
                         use_container_width=True, disabled=not confirm_filter):
                if filter_val.strip():
                    try:
                        with st.spinner("Procesando..."):
                            n = st.session_state.model.filter_rows(filter_col, filter_op, filter_val.strip())
                        set_ok(f"✅ {n} filas eliminadas")
                    except ValueError as e:
                        set_err(f"❌ {e}")
                    st.rerun()
                else:
                    set_warn("Escribe un valor para filtrar")

        # 7 ── Eliminar columna ────────────────────────────────────────────
        with st.expander("🗑️ Eliminar Columna"):
            del_col = st.selectbox("Columna", cols, key="del_col")
            st.warning(f"Se eliminará permanentemente **{del_col}**. Puedes deshacer después.")
            confirm_del = st.checkbox(f"Confirmo que quiero eliminar '{del_col}'", key="confirm_del_col")
            if st.button(f"⚠️ Eliminar '{del_col}'", key="btn_del_col",
                         use_container_width=True, type="primary", disabled=not confirm_del):
                with st.spinner("Eliminando columna..."):
                    st.session_state.model.drop_column(del_col)
                set_ok(f"✅ Columna **{del_col}** eliminada")
                st.rerun()

        # 8 ── Eliminar outliers (IQR) ─────────────────────────────────────
        with st.expander("📉 Eliminar Valores Atípicos (IQR)"):
            numeric_cols = list(get_df().select_dtypes(include="number").columns)
            if not numeric_cols:
                st.caption("No hay columnas numéricas en el dataset.")
            else:
                iqr_col    = st.selectbox("Columna numérica", numeric_cols, key="iqr_col")
                iqr_factor = st.number_input("Factor IQR", min_value=0.1, max_value=10.0,
                                             value=1.5, step=0.1, key="iqr_factor")
                st.caption("Elimina filas fuera de Q1 − factor×IQR  y  Q3 + factor×IQR. "
                           "1.5 = estándar · 3.0 = solo extremos.")
                if st.button("Eliminar outliers", key="btn_iqr", use_container_width=True):
                    try:
                        with st.spinner("Procesando..."):
                            n = st.session_state.model.remove_outliers_iqr(iqr_col, factor=iqr_factor)
                        set_ok(f"✅ {n} filas con valores atípicos eliminadas en **{iqr_col}**")
                    except ValueError as e:
                        set_warn(f"⚠️ {e}")
                    st.rerun()

        st.markdown("---")

        # ── Exportar ──────────────────────────────────────────────────────
        st.markdown("### 💾 Exportar")
        export_name = st.text_input("Nombre del archivo", value="datos_limpios", key="export_name")
        df_export   = get_df()

        buf_csv = BytesIO()
        df_export.to_csv(buf_csv, index=False, encoding="utf-8-sig")
        buf_csv.seek(0)
        st.download_button("⬇ Descargar CSV", data=buf_csv,
                           file_name=f"{export_name}.csv", mime="text/csv",
                           use_container_width=True)

        buf_xlsx = BytesIO()
        df_export.to_excel(buf_xlsx, index=False, engine="openpyxl")
        buf_xlsx.seek(0)
        st.download_button("⬇ Descargar Excel", data=buf_xlsx,
                           file_name=f"{export_name}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

        if st.session_state.model.change_log:
            log_text = "\n".join(f"{i+1:02d}. {e}"
                                 for i, e in enumerate(st.session_state.model.change_log))
            st.download_button("📋 Descargar Log de Cambios", data=log_text.encode("utf-8"),
                               file_name="log_cambios.txt", mime="text/plain",
                               use_container_width=True)
