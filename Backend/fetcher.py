import collections

import pyodbc

class FetcherError(Exception):
    """
    Exception for use in Fetcher.
    """
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return self.message

class Fetcher(object):
    """
    Simple pyodbc-based SQL Server data grabber.

    Based off of fetchdata.py, except much simpler.
    """

    def __init__(self, constr):
        """
        Initializes the Fetcher Class.

        constr is the connection string to the db of interest.
        """
        self.constr = constr
        self.conerr = 'Fetcher: Cannot connect with the supplied Connection String.'
        self.sqlerr = 'Fetcher: Error executing the supplied SQL.'

    def fetch(self, fetchsql):
        """
        Fetches data from the connected database.

        fetchsql is the SQL to execute.

        returns a list of ordered dicts of the row results.
        """
        #Set up the db connection.
        try:
            con = pyodbc.connect(self.constr)
        except:
            raise self.FetcherError(self.conerr)
        cur = con.cursor()
        cur.execute('SET QUERY_GOVERNOR_COST_LIMIT 0')
        cur.execute('SET NOCOUNT ON')
        #Get the data of interest.
        try:
            res = cur.execute(fetchsql)
            dbrows = res.fetchall()
            fields = [col[0] for col in cur.description]
        except:
            raise FetcherError(self.sqlerr)
        con.close()
        #Return the data.
        rows = [collections.OrderedDict(zip(fields, row)) for row in dbrows]
        return rows
