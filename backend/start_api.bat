@echo off
echo ==============================================
echo INICIANDO AMBIENTE VIRTUAL E API DO PROSPECTOR
echo ==============================================

set PYTHON_PATH="C:\Users\X1Carbon\AppData\Local\Programs\Python\Python311\python.exe"

IF NOT EXIST venv (
    echo [1] Criando ambiente virtual ^(venv^)...
    %PYTHON_PATH% -m venv venv
)

echo [2] Instalando dependencias do API...
call venv\Scripts\python.exe -m pip install -r requirements.txt --quiet

echo [3] Iniciando o Servidor Uvicorn/FastAPI...
call venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000

pause
