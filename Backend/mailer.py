import collections
import datetime
import os
import smtplib
import time
import uuid

import jinja2

from email.mime.text import MIMEText

"""
Functions and Classes to handle mail generation and sending for NoticeMe.
"""

# Docs link: http://onestopapp.nola.gov/Documents.aspx?ObjLabel=Project&ID=[dbo.PlanCase.PlanPrjID]

class MailError(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return self.message

class MailGenerator(object):
    """
    Helper class to handle generation of email messages for NoticeMe.
    """
    def __init__(self, localdb, mailtable, namefield, addrfield, uidfield,
                 sourcefield, displaynames, templates):
        """
        Initialize the class.

        localdb is a LocalStore object that is attached to the sqlite3 database.
        mailtable is the name of the LocalStore table containing the summary of
         emails to send.
        namefield is the field name in mailtable that contains the area name.
        addrfield is the field name in mailtable that contains the email address.
        uidfield is the field name in mailtable that contains the uids.
        sourcefield is the field name in mailtable that contains the source table.
        displaynames is a dict mapping source table name to a display name.
        templates is a dict mapping source table name to the template file name.

        no return.
        """
        self.db = localdb
        self.addrs = []
        self.mailtablefields = [namefield, addrfield, uidfield, sourcefield]
        self.mailtable = mailtable
        self.namefield = namefield
        self.addrfield = addrfield
        self.uidfield = uidfield
        self.sourcefield = sourcefield
        self.displaynames = displaynames
        self.templates = templates

    def get_emailaddrs(self, early):
        """
        Gets a list of email addresses to whom we wish send notices.

        early is a flag that indicates if we're sending the early batch of
         notices to nola.gov addresses (True), the late batch of notices to all
         addresses that are not nola.gov (False), or if we're making no
         distinction (None).

        Returns the length of the address list.
        Saves the email addresses to self.emailaddrs
        """
        try:
            self.addrs = self.db.get_addrs(self.addrfield, self.mailtable, early)
        except Exception as e:
            msg = 'Error accessing scratch DB - {0}'.format(e.message)
            raise MailError(msg)
        return len(self.addrs)

    def generate_emails(self, citywide, mailtemplate, templatepath):
        """
        Method to generate the emails, using the info passed to __init__.

        citywide is the area 'name' given to non-spatial notices
        mailtemplate is the filename of jinja2 template for the entire email
        templatepath is the location of the template file on disk

        Returns a list of dicts in the format:
         [{emailaddr: <email>, subject: <subj>, message: <msg>}, ...].
        """
        #First, get the data necessary for each email address.
        dataforemails = []
        for addr in self.addrs:
            try:
                emaildata = self._get_email_data(addr, citywide)
            except Exception as e:
                msg = 'Error retrieving data for address {0}: {1}'.format(addr, e.message)
                raise MailError(msg)
            dataforemails.append(self._replace_and_escape(emaildata))

        #Now, render the emails
        emails = []
        env = jinja2.Environment(autoescape=False, loader=jinja2.FileSystemLoader(templatepath))
        template = env.get_template(mailtemplate)
        procdate = datetime.date.today().strftime('%B %d, %Y')
        #Google Analytics value for tracking email opens.
        gadate = datetime.date.today().isoformat()
        subject = 'NoticeMe Updates for {0}'.format(procdate)
        for item in dataforemails:
            #Google Analytics value for tracking email opens.
            #UUID is used as CID so it is unique but untraceable.
            gacid = str(uuid.uuid1())
            try:
                outhtml = template.render(procdate=procdate,
                                          gadate=gadate,
                                          gacid=gacid,
                                          digest=item['digest'],
                                          details=item['details'])
            except Exception as e:
                msg = 'Error rendering email for address {0}: {1}'.format(item['emailaddr'], e.message)
                raise MailError(msg)
            emails.append({'emailaddr': item['emailaddr'], 'subject': subject,
                           'message': outhtml.encode('UTF-8', 'replace')})

        return emails

    def _get_email_data(self, addr, citywide):
        """
        Queries the LocalStore for a given email address, and gets all data.

        addr is the email address of interest
        citywide is the area 'name' given to non-spatial notices

        Returns a dict in the format:
         {'emailaddr': addr, 'digest': digest, 'details': details}
        """
        items = self.db.get_uids(addr, self.mailtable, self.mailtablefields)
        sources = sorted(items.keys())
        digest = []
        details = []
        #{'source1': {'poly1':[uids], 'poly2':[uids], ...}, 'source2':{} ...}
        for tbl in sources:
            areanames = sorted(items[tbl].keys())
            for area in areanames:
                rows = self.db.get_entries(tbl, items[tbl][area])
                digestitems = []
                for row in rows:
                    detail = {'template': self.templates[tbl],
                              'displayname': self.displaynames[tbl],
                              'data': row}
                    if detail not in details:
                        details.append(detail)
                    #Wrap this in a try...except, to check that we have Location
                    # and RefCode, or test before we process.
                    dgst = {'Location': row['Location'],
                            'displayname': self.displaynames[tbl],
                            'RefCode': row['RefCode']}
                    #Check if Location is empty, and replace with Name if so.
                    if len(dgst['Location']) == 0:
                        dgst['Location'] = row['Name']
                    digestitems.append(dgst)
                #Make sure all notices in a single area are grouped together.
                if area in [x['name'] for x in digest]:
                    idx = [x['name'] for x in digest].index(area)
                    digest[idx]['rows'] += digestitems
                else:
                    digest.append({'name': area, 'rows': digestitems})
        #Finally, reorder the digest so citywide 'areas' are always first
        names = [x['name'] for x in digest]
        if citywide in names:
            idx = names.index(citywide)
            digest = digest[idx:idx+1] + digest[:idx] + digest[idx+1:]

        return {'emailaddr': addr, 'digest': digest, 'details': details}

    def _html_escape(self, text):
        """
        Replaces html-illegal characters with equivalents.

        text is the string in which we need to escape illegal characters.

        returns the text with the illegal characters escaped.
        """

        html_escape_table = {
                             "&": "&amp;",
                             '"': "&quot;",
                             "'": "&#39;", #"&apos;" is not valid in HTML4
                             ">": "&gt;",
                             "<": "&lt;",
                            }
        return "".join(html_escape_table.get(c,c) for c in text)

    def _replace_and_escape(self, emaildata):
        """
        Replace linebreaks (\r\n) with <br/>, tabs (\t) with &emsp;, and escape invalid HTML.
        Recursive to power through the dicts and lists that are in emaildata.

        emaildata is the dict returned from _get_email_data().

        Returns the filtered and escaped emaildata
        """
        if type(emaildata) == collections.OrderedDict or type(emaildata) == dict:
            if type(emaildata) == collections.OrderedDict:
                newdata = collections.OrderedDict()
            else:
                newdata = {}
            for key in emaildata.keys():
                newdata[key] = self._replace_and_escape(emaildata[key])
        elif type(emaildata) == list or type(emaildata) == tuple:
            newdata = []
            for item in emaildata:
                newdata.append(self._replace_and_escape(item))
            if type(emaildata) == tuple:
                newdata = tuple(newdata)
        elif type(emaildata) == str or type(emaildata) == unicode:
            newdata = self._html_escape(emaildata)
            newdata = newdata.replace('\r\n', '<br/>')
            newdata = newdata.replace('\t', '&emsp;')
        else:
            newdata = emaildata
        return newdata


class MailSender(object):
    """
    Helper Class to send emails using an SMTP relay server.
    """
    def __init__(self, mailserver, fromaddress):
        """
        Init the helper class.

        mailserver is the ip address or name of the SMTP server.
        fromaddress is the email address of the sender.
        """
        self.mailserver = mailserver
        self.fromaddress = fromaddress
        self.mailerrors = []

    def send_emails(self, emails):
        """
        Method to actually send the emails.

        emails is a list of dicts containing all the emails to send.  Each dict
         is in the format:
          {'emailaddr': <addr>, 'subject': <subject>, 'message': <html msg>}

        returns the number of emails sent, and the total time taken.
        """
        start = time.time()
        sent = 0
        sender = smtplib.SMTP(self.mailserver)
        for mail in emails:
            #Format the MIMEText message.
            # We have to make sure we set up the message as HTML and UTF-8.
            toaddr = mail['emailaddr']
            msg = MIMEText(mail['message'], 'html', 'utf-8')
            msg['Subject'] = mail['subject']
            msg['From'] = self.fromaddress
            msg['To'] = toaddr
            try:
                sender.sendmail(self.fromaddress, toaddr, msg.as_string())
                sent += 1
            except Exception as e:
                self.mailerrors.append(e.message)

        sender.quit()
        elapsed = time.time() - start
        return sent, elapsed

    def save_emails(self, emails):
        """
        Method to actually send the emails.  Scratch that, save emails for testing.

        emails is a list of dicts containing all the emails to send.  Each dict
         is in the format:
          {'emailaddr': <addr>, 'subject': <subject>, 'message': <html msg>}

        returns the number of emails sent, err, saved, and the total time taken.
        """
        start = time.time()
        sent = 0
        currdate = datetime.date.today().strftime('%Y%m%d')
        for mail in emails:
            toaddr = '{0}_{1}.html'.format(mail['emailaddr'], currdate)
            msg = mail['message']
            try:
                with open(toaddr, 'wb') as f:
                    f.write(msg)
                sent += 1
            except Exception as e:
                self.mailerrors.append(e.message)

        elapsed = time.time() - start
        return sent, elapsed


def keep_db(dbname, procdate):
    """
    Renames a db so it can be kept without interfering in future processing.

    dbname is the name of the db.
    procdate is a string that is added to the db name (process date).

    no return.
    """
    if os.path.exists(dbname):
        loc, nam = os.path.split(dbname)
        newnam = nam.split('.')[0] + '_' + procdate + '.' + nam.split('.')[1]
        dbnew = os.path.join(loc, newnam)
        try:
            os.rename(dbname, dbnew)
        except OSError as e:
            msg = 'Error renaming DB:\n' + e.message
            raise MailError(msg)
    else:
        msg = 'Cannot find DB {0}'.format(dbname)
        raise MailError(msg)

def del_db(dbname):
    """
    Deletes a db from disk.

    dbname is the name of the db.

    no return.
    """
    if os.path.exists(dbname):
        try:
            os.unlink(dbname)
        except OSError as e:
            msg = 'Error Deleting DB:\n' + e.message
            raise MailError(msg)
    else:
        msg = 'Cannot find DB {0}'.format(dbname)
        raise MailError(msg)