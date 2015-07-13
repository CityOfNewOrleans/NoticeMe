import argparse
import datetime
import os
import sys

import configreader
import spatial
from localstore import LocalStore

def get_args():
    """
    Parses command-line arguments and returns them.

    returns the argparse namespace with the arguments.
    """
    parser = argparse.ArgumentParser(description='Process data for NoticeMe.')
    parser.add_argument('settings', metavar='<settings>', 
                        help='file containing program settings')
    parser.add_argument('-r', '--rename', action='store_true',
                        help='rename and keep geodatabase after processing')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--daily', action='store_true',
                       help='process the previous 24 hours of data')
    group.add_argument('-w', '--weekly', action='store_true',
                       help='process the previous seven days of data')
    return parser.parse_args()


if __name__ == '__main__':
    #Parse the command line arguments, and load the config file.
    args = get_args()
    config = configreader.Configurator(args.settings)
    cfg, notices = config.read_settings('spatial')
    #cfg, notices = configreader.read_settings(args.settings)

    if args.weekly:
        dbname = 'w_' + cfg['localdb']
        gdbname = 'w_' + cfg['gdb']
        frequency = 'w' #'WEEKLY'
    else:
        dbname = cfg['localdb']
        gdbname = cfg['gdb']
        frequency = 'd' #'DAILY'

    print 'Running spatial processes...'
    localdb = LocalStore(dbname)
    try:
        gdb = spatial.make_gdb(os.getcwd(), gdbname)
    except spatial.ArcError as e:
        print ' - Error creating spatial DB: {0}'.format(e.message)
        sys.exit(1)

    totaljoined = 0
    for notice in notices:
        outfields = [notice['namefield'], notice['addrfield'], 
                     notice['freqfield'], notice['uidfield']]
        data = localdb.get_points(notice['table'], notice['xfield'], 
                                  notice['yfield'], notice['uidfield'])

        try:
            points = spatial.make_points(gdb, notice['table'], spatial.LASTATEPLANE, 
                                         data, notice['xfield'], notice['yfield'])
        except spatial.ArcError as e:
            print ' - Error creating points from notices: {0}'.format(e.message)
            sys.exit(1)

        aoifilter = notice['aoifilter'].format(frequency)
        try:
            joined = spatial.select_and_join(cfg['aoisource'], notice['table'], 
                                             gdb, aoifilter, outfields, notice['uidfield'])
        except spatial.ArcError as e:
            print ' - Error completing spatial join: {0}'.format(e.message)
            sys.exit(1)

        if joined is not None:
            fcfields = [notice['namefield'], notice['addrfield'], notice['uidfield']]
            exportfields = [cfg['namefield'], cfg['addrfield'], cfg['uidfield']]
            joinedrows = spatial.extract_results(joined, fcfields, exportfields)
            if len(joinedrows) > 0:
                localdb.save_points(cfg['mailtable'], joinedrows, 
                                    notice['table'], cfg['sourcefield'])
            totaljoined += len(joinedrows)
            print ' - {0} rows saved for notice {1}'.format(len(joinedrows), notice['table'])
        else:
            print ' - {0} rows saved for notice {1}'.format(0, notice['table'])
    localdb.close_db()

    #Now, delete the temp GDB, unless the --keep option has been passed.
    if args.rename:
        print 'Keeping scratch GDB for posterity...'
        currdate = datetime.date.today().strftime('%Y%m%d')
        try:
            spatial.keep_gdb(gdb, currdate)
        except spatial.ArcError as e:
            print ' - Error renaming spatial DB: {0}'.format(e.message)
            sys.exit(1)
    else:
        print 'Deleting scratch GDB...'
        try:
            spatial.del_gdb(gdb)
        except spatial.ArcError as e:
            print ' - Error deleting spatial DB: {0}'.format(e.message)
            sys.exit(1)

    print 'NoticeProcess Complete!'
    if totaljoined == 0:
        sys.exit(2)
    else:
        sys.exit(0)