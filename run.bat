@echo off
echo ========================================
echo   DataCleaner
echo   Powered by Streamlit + Plotly
echo ========================================
echo.

:: Verificar que Python esta disponible
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado en el PATH.
    echo Instala Python 3.9+ desde https://python.org y marca "Add to PATH".
    pause
    exit /b 1
)

:: Instalar dependencias de produccion
pip install -r requirements.txt --quiet

:: Informar sobre IA si no hay .env
if not exist .env (
    echo.
    echo NOTA: No se encontro archivo .env.
    echo Para habilitar las recomendaciones IA, copia .env.example a .env
    echo y agrega tu GROQ_API_KEY. La app funciona sin ella.
    echo.
)

echo Iniciando la aplicacion...
echo Abre tu navegador en: http://localhost:8501
echo.
echo Para cerrar la app presiona Ctrl+C en esta ventana.
echo.

python -m streamlit run app.py --server.headless false
pause
