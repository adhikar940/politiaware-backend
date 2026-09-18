# Taking backup from specifc app - myapp
python manage.py dumpdata myapp > myapp_data.json

# Restoring data to specific app 
python manage.py loaddata myapp_data.json