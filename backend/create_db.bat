@echo off
set PGPASSWORD=8640
set PSQL=C:\Progra~1\PostgreSQL\18\bin\psql.exe
set CREATEDB=C:\Progra~1\PostgreSQL\18\bin\createdb.exe
set CREATEUSER=C:\Progra~1\PostgreSQL\18\bin\createuser.exe

echo === Creating HR Payroll PostgreSQL database ===

echo [1] Drop existing database if exists...
%PSQL% -U postgres -h 127.0.0.1 -p 5432 -c "DROP DATABASE IF EXISTS hr_payroll_db;"

echo [2] Drop existing user if exists...
%PSQL% -U postgres -h 127.0.0.1 -p 5432 -c "DROP ROLE IF EXISTS hr_payroll_user;"

echo [3] Create user hr_payroll_user with password 8640...
%PSQL% -U postgres -h 127.0.0.1 -p 5432 -c "CREATE ROLE hr_payroll_user WITH LOGIN PASSWORD '8640';"

echo [4] Create database hr_payroll_db...
%PSQL% -U postgres -h 127.0.0.1 -p 5432 -c "CREATE DATABASE hr_payroll_db OWNER hr_payroll_user ENCODING 'UTF8';"

echo [5] Grant privileges...
%PSQL% -U postgres -h 127.0.0.1 -p 5432 -c "GRANT ALL PRIVILEGES ON DATABASE hr_payroll_db TO hr_payroll_user;"

echo [6] Verify connection as hr_payroll_user...
set PGPASSWORD=8640
%PSQL% -U hr_payroll_user -h 127.0.0.1 -p 5432 -d hr_payroll_db -c "SELECT current_database(), current_user, version();"

echo.
echo === Database created successfully! ===
echo    Database: hr_payroll_db
echo    User:     hr_payroll_user
echo    Password: 8640
echo    Host:     127.0.0.1:5432
