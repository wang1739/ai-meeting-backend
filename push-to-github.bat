@echo off
chcp 65001 >nul
cd /d "d:\Trae\ai-meeting-backend"
echo Pushing backend code to GitHub...
git push origin main
if %errorlevel%==0 (
    echo.
    echo [OK] Backend code pushed to https://github.com/wang1739/ai-meeting-backend
) else (
    echo.
    echo [FAIL] Push failed. Please check network or GitHub token.
)
pause
