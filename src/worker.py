#! coding: utf-8
# pylint: disable-msg=W0311

from time import sleep, time
from dmp import diff_match_patch
from os import stat, path, system as run_command
from settings import *

def email_it_via_gmail(headers, text=None, html=None, password=None):
    """Send an email -- with text and HTML parts.
    
    @param headers {dict} A mapping with, at least: "To", "Subject" and
        "From", header values. "To", "Cc" and "Bcc" values must be *lists*,
        if given.
    @param text {str} The text email content.
    @param html {str} The HTML email content.
    @param password {str} Is the 'From' gmail user's password. If not given
        it will be prompted for via `getpass.getpass()`.
    
    Derived from http://code.activestate.com/recipes/473810/ and
    http://stackoverflow.com/questions/778202/smtplib-and-gmail-python-script-problems
    """
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText
    import re
    import smtplib
    import getpass
    
    if text is None and html is None:
        raise ValueError("neither `text` nor `html` content was given for "
            "sending the email")
    if not ("To" in headers and "From" in headers and "Subject" in headers):
        raise ValueError("`headers` dict must include at least all of "
            "'To', 'From' and 'Subject' keys")

    # Create the root message and fill in the from, to, and subject headers
    msg_root = MIMEMultipart('related')
    for name, value in headers.items():
        msg_root[name] = isinstance(value, list) and ', '.join(value) or value
    msg_root.preamble = 'This is a multi-part message in MIME format.'

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want
    # to display.
    msg_alternative = MIMEMultipart('alternative')
    msg_root.attach(msg_alternative)

    # Attach HTML and text alternatives.
    if text:
        msg_text = MIMEText(text.encode('utf-8'), _charset='utf-8')
        msg_alternative.attach(msg_text)
    if html:
        msg_text = MIMEText(html.encode('utf-8'), 'html', _charset='utf-8')
        msg_alternative.attach(msg_text)

    to_addrs = headers["To"] \
        + headers.get("Cc", []) \
        + headers.get("Bcc", [])
    from_addr = msg_root["From"]
    
    # Get username and password.
    from_addr_pats = [
        re.compile(".*\((.+@.+)\)"),  # Joe (joe@example.com)
        re.compile(".*<(.+@.+)>"),  # Joe <joe@example.com>
    ]
    for pat in from_addr_pats:
        m = pat.match(from_addr)
        if m:
            username = m.group(1)
            break
    else:
        username = from_addr
    if not password:
        password = getpass.getpass("%s's password: " % username)
    
    smtp = smtplib.SMTP('smtp.gmail.com', 587) # port 465 or 587
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(username, password)
    smtp.sendmail(from_addr, to_addrs, msg_root.as_string())
    smtp.close()

  
def set_style(text, type):
  style = 'font-family: monospace; font-size: 12px;'
  if type == 'remove':
    style += 'background-color: #FDD; text-decoration: line-through; color: #333; opacity: 0.25;'
  elif type == 'insert':
    style += 'background-color: #DFD; color: #333;'
  else:
    style += 'color: #333;'
  return '<span style="%s">%s</span>' % (style, text)
    

dmp = diff_match_patch()
def diff(file1, file2):
  lines = open(file1).read().split('\n')
  old = ''.join(['<pre>%s</pre>' % line for line in lines])
  lines = open(file2).read().split('\n')
  new = ''.join(['<pre>%s</pre>' % line for line in lines])
  diffs = dmp.diff_main(old, new, checklines=False)

  html = []
  for diff in diffs:
    state, text = diff
    if state == -1:
      html.append(set_style(text, 'remove'))
    elif state == 1:
      html.append(set_style(text, 'insert'))
    else:
      html.append(set_style(text, 'normal'))
      
  content = ''.join(html)
  return content
  


def run():
  DATABASE = {}
  
  # Backup original file to compared later
  for file in FILES:
    filename = file.replace('/', '.').lstrip('.')
    tmp_file = path.join(REPOSITORY, filename)
    run_command('cp %s %s' % (file, tmp_file))
    
  while True:
    for file in FILES:
      filename = file.replace('/', '.').lstrip('.')
      mtime = stat(file).st_mtime
      
      tmp_file = path.join(REPOSITORY, filename)
      revision_name = '%s.%s' % (tmp_file, int(time()))
      
      if DATABASE.has_key(filename) and DATABASE.get(filename) != mtime:  # file changed
          print 'file %s changed' % file
          
          html = diff(tmp_file, file)
          open('%s.html' % revision_name, 'w').write(html)  # save html file to disk
          
          run_command("diff -u %s %s > %s.patch" % (tmp_file, file, revision_name))   # save patch file
          text = open('%s.patch' % revision_name).read()
          
          run_command("cp %s %s" % (file, tmp_file))
          
          if SEND_EMAIL_NOTIFICATION:
            # Now, send changes to admins
            headers = {'From': 'AloneRoad@Gmail.com',
                       'To': RECIPIENTS,
                       'Subject': 'File %s changed' % file}
            email_it_via_gmail(headers, text, html)
              
      DATABASE[filename] = mtime
    sleep(1)
  
  
if __name__ == '__main__':
  import daemon
  with daemon.DaemonContext():
    run()
