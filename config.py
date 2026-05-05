import os

DATABASE = os.environ.get(
    'RUNNING_DB',
    '/Users/scottroberts/Dropbox/Databases/RunningLog/races.sqlite'
)

GARMIN_EMAIL = os.environ.get('GARMIN_EMAIL')
GARMIN_PASSWORD = os.environ.get('GARMIN_PASSWORD')
