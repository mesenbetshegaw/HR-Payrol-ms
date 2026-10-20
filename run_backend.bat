@echo off
echo ============================================
echo  HR Payroll System - Backend Server
echo  http://127.0.0.1:8000
echo  API Docs: http://127.0.0.1:8000/api/docs/
echo  Admin:    http://127.0.0.1:8000/admin/
echo ============================================
cd /d "c:\Users\mmese\Documents\messi folder\software folder\Graduation_Project\backend"
.\venv\Scripts\python.exe manage.py runserver 8000
pause
