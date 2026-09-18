from politiaware_backend.conf.conf_loader import config

'''
### sqlite database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase',
    }
}'''

db_conf = config["database"]
DATABASES = {
    'default': {
        'ENGINE':'django.contrib.gis.db.backends.postgis',
        'NAME': db_conf['name'],
        'USER': db_conf['user'],
        'PASSWORD': db_conf['password'],
        'HOST': db_conf['host'],
        'PORT': db_conf['port'],
        'OPTIONS': {
            'options': f"-c search_path={db_conf.get('schema', 'public')}"
        },
    }
}

# ┌───────────── minute (0–59)
# │ ┌───────────── hour (0–23)
# │ │ ┌───────────── day of the month (1–31)
# │ │ │ ┌───────────── month (1–12)
# │ │ │ │ ┌───────────── day of the week (0–6) (Sunday to Saturday;
# │ │ │ │ │                                   7 is also Sunday on some systems)
# │ │ │ │ │
# │ │ │ │ │
# * * * * * <command to execute>
'''
*/5 * * * *: Every 5 minutes
0 */2 * * *: Every 2 hours
0 0 */3 * *: Every 3 days
0 0 1 */6 *: Every 6 months
'''
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': 'backup/'}
#('*/1 * * * *', 'm.cron.min_job', '>> /tmp/scheduled_job.log'),      # test every min.
CRONJOBS = [   
    ('0 0 * * *', 'm.cron.daily_job'),      # Daily at midnight
    ('0 0 * * 0', 'm.cron.weekly_job'),     # Weekly at midnight on Sunday
    ('0 0 1 * *', 'm.cron.monthly_job'),    # Monthly at midnight on the 1st
    ('0 0 1 1 *', 'm.cron.yearly_job'),     # Yearly at midnight on January 1st

]

'''EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('adhikar_EMAIL_HOST')
EMAIL_PORT = os.environ.get('adhikar_EMAIL_PORT')
EMAIL_USE_TLS = os.environ.get('adhikar_EMAIL_USE_TLS')
EMAIL_HOST_USER = os.environ.get('adhikar_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('adhikar_EMAIL_HOST_PASSWORD')'''
INTERNAL_IPS = [
    "127.0.0.1",
]

