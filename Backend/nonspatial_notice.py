import argparse
import collections
import datetime

import configreader
import fetcher
import spatial
from localstore import LocalStore


def get_args():
    """
    Parses command-line arguments and returns them.

    returns the argparse namespace with the arguments.
    """
    parser = argparse.ArgumentParser(description='Fetch Non-spatial notices for NoticeMe.')
    parser.add_argument('settings', metavar='<settings>',
                        help='file containing program settings')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--daily', action='store_true',
                       help='fetch the previous 24 hours of data')
    group.add_argument('-w', '--weekly', action='store_true',
                       help='fetch the previous seven days of data')
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    config = configreader.Configurator(args.settings)
    cfg, notices = config.read_settings('nonspatial')

    today = datetime.date.today()
    print 'Processing Non-spatial Notices...'
    if args.weekly:
        searchdate = today + datetime.timedelta(days=-7)
        dbname = 'w_' + cfg['localdb']
    else:
        searchdate = today
        dbname = cfg['localdb']
    #test date please ignore.
    #searchdate = datetime.date(2014, 11, 8)

    print ' - fetching from {0} to now'.format(searchdate.isoformat())

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
        if len(rows) > 0:
            #Extract all the users from the AOI featureclass.
            allusers = set()
            usrflds = [cfg['addrfield'], notice['preffield']]
            rawaddrs = spatial.extract_results(cfg['aoisource'], usrflds, usrflds)
            for addr in rawaddrs:
                if addr[notice['preffield']] == '1':
                    allusers.add(addr[cfg['addrfield']])
            print ' - {0} users to be notified for {1}'.format(len(allusers), notice['table'])
        
            #This gets a little brute-forcey.  Probably should be rolled up in localstore.
            getuidssql = 'SELECT DISTINCT {0} FROM {1}'.format(notice['uidfield'], notice['table'])
            uidres = localdb.exec_sql(getuidssql)
            noticeuids = '|'.join([str(x[notice['uidfield']]) for x in uidres])
            rows = []
            fields = [cfg['namefield'], cfg['addrfield'], cfg['uidfield']]
            for addr in allusers:
                rows.append(collections.OrderedDict(zip(fields, [cfg['citywidearea'], addr, noticeuids])))
            localdb.save_points(cfg['mailtable'], rows, notice['table'], cfg['sourcefield'])

    localdb.close_db()
    print 'Non-spatial Notice Complete!'
