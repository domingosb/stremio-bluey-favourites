@echo off
rem Rebuilds the addon from favourites.txt and publishes it to GitHub.
cd /d "%~dp0"
git pull -q --rebase
python -I build.py || (pause & exit /b 1)
git add -A
git commit -q -m "Update favourites"
git push
echo.
echo Done. Stremio picks up the new list within a few minutes (restart it to force).
pause
