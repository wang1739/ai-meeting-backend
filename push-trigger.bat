@echo off
chcp 65001 >nul
cd /d d:\Trae\ai-meeting-backend
echo Pushing empty commit to trigger Railway redeploy...
git push origin main
if %errorlevel%==0 (
    echo SUCCESS: Code pushed. Railway will auto-deploy.
) else (
    echo FAILED: Push failed. Please check network connection.
)
pause