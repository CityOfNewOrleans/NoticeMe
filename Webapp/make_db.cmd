@echo off
echo Initializing DB...
C:\Python27\python -c "import database; database.init_db()"
echo Complete.