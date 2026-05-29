@echo off
echo ==========================================
echo Starting ASAAP Backend Services
echo ==========================================

:: Set Java 17 Path
set JAVA_HOME=%CD%\jdk\jdk17.0.19_10
set PATH=%JAVA_HOME%\bin;%PATH%

echo [1/2] Starting Auth Service on Port 8081...
start "ASAAP Auth Service" cmd /c "cd backend\auth-service && .\mvnw.cmd spring-boot:run"

echo [2/2] Starting Alert Service on Port 8082...
start "ASAAP Alert Service" cmd /c "cd backend\alert-service && .\mvnw.cmd spring-boot:run"

echo.
echo Both microservices are spinning up in separate windows!
pause
