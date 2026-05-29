@echo off
echo ==========================================
echo Starting ASAAP Full Stack Ecosystem
echo ==========================================

:: Switch to script directory
cd /d "%~dp0"

:: Set Java 17 Path
set JAVA_HOME=%CD%\jdk\jdk17.0.19_10
set PATH=%JAVA_HOME%\bin;%PATH%

echo.
echo Java Home: %JAVA_HOME%
echo.

echo [1/4] Starting Auth Service (Port 8081)...
start "ASAAP Auth Service" cmd /k "set JAVA_HOME=%JAVA_HOME%&& set PATH=%JAVA_HOME%\bin;%PATH%&& cd /d %~dp0backend\auth-service && .\mvnw.cmd spring-boot:run"

echo [2/4] Starting Alert Service (Port 8082)...
start "ASAAP Alert Service" cmd /k "set JAVA_HOME=%JAVA_HOME%&& set PATH=%JAVA_HOME%\bin;%PATH%&& cd /d %~dp0backend\alert-service && .\mvnw.cmd spring-boot:run"

echo [3/4] Starting Python AI Model Server (Port 8000)...
start "ASAAP AI Model" cmd /k "cd /d %~dp0 && python model_server.py"

echo [4/4] Starting React Frontend (Port 5173)...
start "ASAAP Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ==========================================
echo All services are launching in separate windows!
echo ==========================================
echo.
echo  Auth Service   :  http://localhost:8081
echo  Alert Service  :  http://localhost:8082
echo  AI Model API   :  http://localhost:8000
echo  React Frontend :  http://localhost:5173
echo.
echo You can safely close this window.
