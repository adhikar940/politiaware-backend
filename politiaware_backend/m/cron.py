import os
from django.core.files.storage import FileSystemStorage
from datetime import datetime
from django.core.management import call_command

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
    print(f"Checked directory: {path}")

def maintain_backup_limit(path, limit=6):
    files = sorted([os.path.join(path, f) for f in os.listdir(path)], key=os.path.getctime)
    if len(files) > limit:
        os.remove(files[0])
    print(f"Maintained backup limit: {path}, current files: {len(files)}")

def create_backup(path):
    # Example backup file creation logic
    filename = os.path.join(path, f"backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql")
    with open(filename, 'w') as f:
        f.write('')  # Replace with actual backup data
    print(f"Created backup: {filename}")    
def min_job():
    call_command('dbbackup')
def daily_job():
    backup_path = 'backup/daily/'
    ensure_directory_exists(backup_path)
    maintain_backup_limit(backup_path)
    #create_backup(backup_path)
    DBBACKUP_STORAGE_OPTIONS = {'location': backup_path}
    call_command('dbbackup')
   
   
def weekly_job():
    backup_path = 'backup/weekly/'
    ensure_directory_exists(backup_path)
    maintain_backup_limit(backup_path)
    create_backup(backup_path)
    DBBACKUP_STORAGE_OPTIONS = {'location': backup_path}
    storage = FileSystemStorage(location=DBBACKUP_STORAGE_OPTIONS['location'])
    
def monthly_job():
    backup_path = 'backup/monthly/'
    ensure_directory_exists(backup_path)
    maintain_backup_limit(backup_path)
    create_backup(backup_path)
    DBBACKUP_STORAGE_OPTIONS = {'location': backup_path}
    storage = FileSystemStorage(location=DBBACKUP_STORAGE_OPTIONS['location'])
   

def yearly_job():
    backup_path = 'backup/yearly/'
    ensure_directory_exists(backup_path)
    maintain_backup_limit(backup_path)
    create_backup(backup_path)
    DBBACKUP_STORAGE_OPTIONS = {'location': backup_path}
    storage = FileSystemStorage(location=DBBACKUP_STORAGE_OPTIONS['location'])
    