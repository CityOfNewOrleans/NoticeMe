import argparse
import datetime
import sys

import configreader
import fetcher
from localstore import LocalStore

def get_args():
    """
    Parses command-line arguments and returns them.

    returns the argparse namespace with the arguments.
    """
    parser = argparse.ArgumentParser(description='Fetch LAMA data for NoticeMe.')
    parser.add_argument('settings', metavar='<settings>',
                        help='file containing program settings')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--daily', action='store_true',
                       help='fetch the previous 24 hours of data')
    group.add_argument('-w', '--weekly', action='store_true',
                       help='fetch the previous seven days of data')
    return parser.parse_args()


if __name__ == '__main__':
    #Parse the command line arguments, and load the config file.
    args = get_args()
    config = configreader.Configurator(args.settings)
    cfg, notices = config.read_settings('spatial')
    #cfg, notices = configreader.read_settings(args.settings)

    today = datetime.date.today()
    if args.weekly:
        searchdate = today + datetime.timedelta(days=-7)
        dbname = 'w_' + cfg['localdb']
    else:
        searchdate = today
        dbname = cfg['localdb']
        #test date please ignore.
        #searchdate = datetime.date(2014, 11, 8)

    print 'Fetching from {0} to now...'.format(searchdate.isoformat())

    lamagetter = fetcher.Fetcher(cfg['connection'])
    localdb = LocalStore(dbname)
    for notice in notices:
        try:
            rows = lamagetter.fetch(notice['sql'].format(searchdate))
        except fetcher.FetcherError as e:
            print ' - Error accessing DB: {0}'.format(e.message)
            sys.exit(1)
        localdb.save_data(notice['table'], rows, notice['uidfield'])
        print ' - {0} rows saved to table {1}'.format(len(rows), notice['table'])
    localdb.close_db()

    print 'NoticeLAMA Complete!'