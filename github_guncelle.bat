@echo off
chcp 65001 >nul
echo ============================================
echo   GitHub Guncelleme (mevcut repo korunur)
echo ============================================
echo.

cd /d "%~dp0"

:: .git klasoru yoksa depoyu ilk kez bu makinede baglar
if not exist ".git" (
    echo [Bilgi] Yerel git deposu bulunamadi, olusturuluyor ve baglaniyor...
    git init
    git remote add origin https://github.com/enesboz-9/model_e-itimi.git
    git fetch origin
    git checkout -B main origin/main
) else (
    echo [Bilgi] Mevcut yerel git deposu kullaniliyor.
)

:: Buyuk / gereksiz dosyalari yoksay (repoya gitmesin)
(
echo arabam.com-otomobil-veri-seti.json
echo arabam.com-otomobil-veri-seti-csv.csv
echo arabam_temiz.csv
echo Engine_Data.xlsx
echo __pycache__/
echo *.pyc
) > .gitignore

:: Uzak depodaki en guncel halini once cek (cakismalari onlemek icin)
echo.
echo [1/4] Uzak depodan guncel degisiklikler cekiliyor...
git pull origin main --no-rebase --allow-unrelated-histories

:: Degisiklikleri ekle
echo.
echo [2/4] Degisiklikler ekleniyor...
git add -A

:: Commit (degisiklik yoksa hata vermeden devam eder)
echo.
echo [3/4] Commit olusturuluyor...
git commit -m "Motor modeli bilgilendirme ozelligi eklendi (motor veri seti + KNN eslestirme)"

:: Push
echo.
echo [4/4] GitHub'a gonderiliyor...
git branch -M main
git push -u origin main

echo.
echo ============================================
echo   Tamamlandi! GitHub'i kontrol et:
echo   https://github.com/enesboz-9/model_e-itimi
echo ============================================
pause
