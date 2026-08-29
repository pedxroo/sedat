@echo off
cd /d "%~dp0"
echo Iniciando servidor local do SEDAT-SUS Dashboard...
start "" http://localhost:8791/index.html
python -m http.server 8791
