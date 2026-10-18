@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/2] Bagimliliklar kontrol ediliyor...
python -m pip install -r requirements.txt
if errorlevel 1 goto hata

echo [2/2] EXE derleniyor...
python -m PyInstaller --noconsole --onefile --clean ^
  --name "UYAP_Evrak_Asistani" ^
  --icon logo.ico ^
  --add-data "logo.ico;." --add-data "logo.png;." ^
  --version-file version_info.txt ^
  --collect-all tkinterdnd2 --collect-all sv_ttk --collect-all docx --collect-all docx2pdf ^
  --hidden-import win32com.client --hidden-import pythoncom ^
  app.py
if errorlevel 1 goto hata

echo.
echo TAMAMLANDI: %~dp0dist\UYAP_Evrak_Asistani.exe
pause
exit /b 0

:hata
echo.
echo HATA: Derleme basarisiz. Yukaridaki mesaji kopyalayip gonderin.
pause
exit /b 1
