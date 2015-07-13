import argparse
import datetime
import time
import sys

import configreader
import mailer
from localstore import LocalStore

def get_args():
    """
    Parses command-line arguments and returns them.

    returns the argparse namespace with the arguments.
    """
    parser = argparse.ArgumentParser(description='Send Emails for NoticeMe.')
    parser.add_argument('settings', metavar='<settings>',
                        help='file containing program settings')
    group0 = parser.add_mutually_exclusive_group(required=False)
    group0.add_argument('-k', '--keep', action='store_true',
                        help='do not delete database after mailing')
    group0.add_argument('-r', '--rename', action='store_true',
                        help='rename and keep database after mailing')
    group1 = parser.add_mutually_exclusive_group(required=True)
    group1.add_argument('-d', '--daily', action='store_true',
                       help='send mail based on the previous 24 hours of data')
    group1.add_argument('-w', '--weekly', action='store_true',
                       help='send mail based on the previous seven days of data')
    group2 = parser.add_mutually_exclusive_group(required=True)
    group2.add_argument('-a', '--all', action='store_true',
                        help='send emails to all registered recipients')
    group2.add_argument('-n', '--nola', action='store_true',
                        help='only send emails to xxx@nola.gov addresses')
    group2.add_argument('-c', '--citizens', action='store_true',
                        help='send emails to recipients without a xxx@nola.gov address')
    parser.add_argument('-s', '--save', action='store_true',
                        help='save emails to disk instead of sending them')

    return parser.parse_args()


if __name__ == '__main__':
    #Parse the command line arguments, and load the config file.
    args = get_args()
    config = configreader.Configurator(args.settings)
    cfg, notices = config.read_settings('all')

    #If we're running a weekly batch, name things appropriately.
    if args.weekly:
        dbname = 'w_' + cfg['localdb']
        emailtemplate = cfg['weeklytemplate']
    else:
        dbname = cfg['localdb']
        emailtemplate = cfg['dailytemplate']

    #Get the addresses we need for this sendoff.
    if args.all:
        early = None
    elif args.nola:
        early = True
    elif args.citizens:
        early = False
    else:
        early = None

    if args.weekly:
        print 'Processing weekly notices...'
    else:
        print 'Processing daily notices...'

    #Setup the info needed by the MailGenerator
    localdb = LocalStore(dbname)
    displaynames = {x['table']: x['displayname'] for x in notices}
    templates = {x['table']: x['template'] for x in notices}

    secretary = mailer.MailGenerator(localdb, cfg['mailtable'],
                                     cfg['namefield'], cfg['addrfield'],
                                     cfg['uidfield'], cfg['sourcefield'],
                                     displaynames, templates)

    #Get the email addresses to which we must send notices, and proceed if
    # there are any to send.
    try:
        numemails = secretary.get_emailaddrs(early)
    except mailer.MailError as e:
        print ' - Cannot retrieve emails: {0}'.format(e.message)
        sys.exit(1)
    if numemails > 0:
        print ' - {0} emails to process and send.'.format(numemails)
        if early is not None:
            if early:
                print ' - Sending early notices.'
            else:
                print ' - Sending late notices.'
        #Process the data and generate emails.
        try:
            emails = secretary.generate_emails(cfg['citywidearea'], emailtemplate, cfg['templatepath'])
        except mailer.MailError as e:
            print ' - Error generating emails: {0}'.format(e.message)
            sys.exit(1)
        #Now, send the emails.
        try:
            postman = mailer.MailSender(cfg['mailserver'], cfg['fromaddress'])
            #For testing, save them to disk before sending.
            if args.save:
                sentemails, totaltime = postman.save_emails(emails)
            else:
                sentemails, totaltime = postman.send_emails(emails)
        except Exception as e:
            print ' - Error sending emails: {0}'.format(e.message)
            sys.exit(1)

        print ' - {0} emails sent in {1:0.2f} seconds.'.format(sentemails, totaltime)
        if sentemails != len(emails):
            currdate = datetime.date.today().strftime('%Y%m%d')
            errfile = 'email_errors_{0}.txt'.format(currdate)
            print ' - errors encountered sending some emails.'
            with open(errfile, 'w') as f:
                f.writelines([x+'\n' for x in postman.mailerrors])
            print ' - error details saved to {0}'.format(errfile)
    else:
        print ' - No notices to send.'

    #Now, delete the sqlite database, unless the --keep option has been passed.
    localdb.close_db()
    del localdb
    if args.keep:
        #Do nothing to the DB; we'll need it for a later mailing.
        print 'Keeping scratch db for later use...'
    elif args.rename:
        #Rename and keep the DB, we want it for checking and testing later.
        print 'Keeping scratch db for posterity...'
        currdate = datetime.date.today().strftime('%Y%m%d')
        try:
            mailer.keep_db(dbname, currdate)
        except mailer.MailError as e:
            print ' - Error renaming scratch DB: {0}'.format(e.message)
            sys.exit(1)
    else:
        print 'Deleting scratch db...'
        try:
            mailer.del_db(dbname)
        except mailer.MailError as e:
            print ' - Error deleting scratch DB: {0}'.format(e.message)
            sys.exit(1)

    print 'NoticeMail Complete!'
