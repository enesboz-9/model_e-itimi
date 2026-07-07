@echo off
chcp 65001 >nul
echo Push islemi basliyor...
echo.

cd /d "%~dp0"

:: Eski git gecmisini temizle
rmdir /s /q .git 2>nul

:: Yeniden baslat
git init

:: Buyuk ve gereksiz dosyalari yoksay
(
echo arabam.com-otomobil-veri-seti.json
echo arabam.com-otomobil-veri-seti-csv.csv
echo arabam_temiz.csv
echo __pycache__/
echo *.pyc
) > .gitignore

:: Dosyalari ekle
git add .

:: Commit
git commit -m "araç fiyat tahmin modeli - ilk surum"

:: Main branch
git branch -M main

:: Remote
git remote add origin https://github.com/enesboz-9/model_e-itimi.git

:: Push
git push -u origin main --force

echo.
echo Tamamlandi! GitHub'i kontrol et.
pause
