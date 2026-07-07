@echo off
if "%~1"=="" (
    cmd /k "%~f0" __run__
    exit /b
)

echo ============================================
echo   GitHub Guncelleme (mevcut repo korunur)
echo ============================================
echo.

cd /d "%~dp0"
echo Calisma klasoru: %cd%
echo.

where git >nul 2>&1
if errorlevel 1 goto NOGIT

echo arabam.com-otomobil-veri-seti.json> .gitignore
echo arabam.com-otomobil-veri-seti-csv.csv>> .gitignore
echo arabam_temiz.csv>> .gitignore
echo Engine_Data.xlsx>> .gitignore
echo __pycache__/>> .gitignore
echo *.pyc>> .gitignore

if exist ".git" goto HASGIT

echo [Bilgi] Yerel git deposu bulunamadi, olusturuluyor...
git init
git remote add origin https://github.com/enesboz-9/model_e-itimi.git
goto SETBRANCH

:HASGIT
echo [Bilgi] Mevcut yerel git deposu kullaniliyor.
git remote get-url origin >nul 2>&1
if errorlevel 1 git remote add origin https://github.com/enesboz-9/model_e-itimi.git

:SETBRANCH
git branch -M main

echo.
echo [1/4] Yerel degisiklikler ekleniyor ve commit olusturuluyor...
git add -A
git commit -m "Motor modeli bilgilendirme ozelligi eklendi (motor veri seti + KNN eslestirme)"

echo.
echo [2/4] Uzak depo (GitHub) bilgisi indiriliyor...
git fetch origin

echo.
echo [3/4] Uzak depoyla gecmis birlestiriliyor (cakismalarda yerel dosyalar korunur)...
git merge origin/main --allow-unrelated-histories -X ours -m "Yerel guncellemeler ile birlestirildi"

echo.
echo [4/4] GitHub'a gonderiliyor...
git push -u origin main

echo.
echo ============================================
echo   Tamamlandi! GitHub'i kontrol et:
echo   https://github.com/enesboz-9/model_e-itimi
echo ============================================
goto END

:NOGIT
echo.
echo [HATA] Git bulunamadi! Once https://git-scm.com adresinden Git kurmalisin.
echo Kurduktan sonra bu dosyayi tekrar calistir.
goto END

:END
echo.
echo (Bu pencere kapanmayacak, cikmak icin bir tusa bas ya da pencereyi kapat)
pause
