@echo off
cd /d d:\Trae\ai-meeting-backend
echo Pushing to GitHub...
git push origin main --force
echo.
if %errorlevel% equ 0 (
    echo SUCCESS: Code pushed. Railway will auto-deploy.
) else (
    echo FAILED: Please check your network or use GitHub web upload.
    echo Upload URL: https://github.com/wang1739/ai-meeting-backend
)
pause