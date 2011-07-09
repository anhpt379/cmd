REPOSITORY = '/home/Workspace/fmd/src/repository'

FILES = [
  '/home/Workspace/fmd/src/tests/1.conf',
  '/home/Workspace/fmd/src/tests/2.conf',
]

REFRESH_TIME = 300  # 5 mins (for change going to stable)
DEBUG = True
SEND_EMAIL_NOTIFICATION = False
if SEND_EMAIL_NOTIFICATION:
  USERNAME = ''
  PASSWORD = ''
  SMTP_SERVER = ''
  RECIPIENTS = ['AloneRoad@Gmail.com']