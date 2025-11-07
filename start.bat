@echo off
echo Starting the application...

REM Start the web application in a new command window
start "Web Application" cmd /k "cd /d %~dp0 && python app.py"

REM Start the Telegram bot in a new command window
start "Telegram Bot" cmd /k "cd /d %~dp0 && python telegram_bot.py"

echo Both applications have been started. Check the command windows that opened.
pause
