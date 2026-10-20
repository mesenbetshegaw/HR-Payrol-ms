@echo off
echo ============================================
echo  HR Payroll System - Starting All Servers
echo ============================================
echo.
echo Starting Backend on http://127.0.0.1:8000 ...
start "Backend - Django" cmd /k "cd /d "c:\Users\mmese\Documents\messi folder\software folder\Graduation_Project\backend" && .\venv\Scripts\python.exe manage.py runserver 8000"

timeout /t 3 /nobreak > nul

echo Starting Frontend on http://localhost:5173 ...
start "Frontend - Vite" cmd /k "cd /d "c:\Users\mmese\Documents\messi folder\software folder\Graduation_Project\frontend" && npm run dev"

echo.
echo ============================================
echo  Backend:  http://127.0.0.1:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://127.0.0.1:8000/api/docs/
echo  Admin:    http://127.0.0.1:8000/admin/
echo ============================================
echo.
echo Both servers are starting in separate windows.
echo Login credentials:
echo   messi@hrpayroll.et       / 8640        (Admin)
echo   admin@hrpayroll.et       / Admin@1234  (Admin)
echo   subadmin@hrpayroll.et    / SubAdmin@1234 (Sub Admin)
echo   manager@hrpayroll.et     / Manager@1234  (Manager)
echo   employee@hrpayroll.et    / Employee@1234 (Employee)
pause
