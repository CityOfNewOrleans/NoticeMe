import csv
import json
import os
import sys

from collections import OrderedDict

import arcpy

from database import db_session
from models import User, Notice

import settings

class TransportError(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return self.message

def make_gdb(location, gdbname):
    """
    Create a file geodatabase.

    location is the path in which the gdb is to be created.
    gdbname is the name of the file geodatabase to create.

    returns the full path of the created gdb (including name).
    """
    #First, check to see if we've already created the gdb.
    gdb = os.path.join(location, gdbname)
    if not arcpy.Exists(gdb):
        #CURRENT means create a gdb at the current Arc version.
        try:
            res = arcpy.CreateFileGDB_management(location, gdbname, "CURRENT")
        except Exception as e:
            raise TransportError(e.message)
        if res.status != 4: #4 indicates success.
            raise TransportError(res.getMessage(0))

    return gdb

def make_fc(gdb, fcname, fields, wkid):
    """
    Create a new polygon featureclass to save areas of interest in.

    gdb is the path and name of the destination geodatabase.
    fcname is the name of the featureclass to create.
    fields is a list of field names to save (all are assumed text).
    wkid is the Well-Known ID of the Spatial Reference.

    returns the path to and name of the featureclass
    """
    arcpy.env.overwriteOutput = True
    geom = 'POLYGON'
    template = ''
    hasm = 'DISABLED'
    hasz = 'DISABLED'
    spatialref = arcpy.SpatialReference(wkid)

    try:
        res = arcpy.CreateFeatureclass_management(gdb, fcname, geom, template,
                                                  hasm, hasz, spatialref)
    except Exception as e:
        raise TransportError(e.message)
    if res.status != 4:
        msg = 'Error Creating Feature Class {0}\n'.format(fcname)
        msg += res.getMessage(0)
        raise TransportError(msg)

    #Now add the fields:
    fcname = os.path.join(gdb, fcname)
    for fld in fields:
        res = arcpy.arcpy.AddField_management(fcname, fld, 'TEXT', '', '', '254', '', 'NULLABLE', 'NON_REQUIRED', '')
        if res.status != 4:
            raise TransportError('Error adding field {0}.'.format(fld))

    return fcname

def poly_from_rings(ringpoints, inputwkid, outputwkid=None):
    """
    Creates an ESRI Polygon object from an array of points in rings.
    Useful for saving geometry from NoticeMe into a GDB.

    ringpoints is the list of lists of coordinate lists.
    inputwkid is the wkid of the input spatial reference.
    outputwkid is the wkid of the output SR (if projection is desired).

    returns an arcpy.Polygon.
    """
    spatialref = arcpy.SpatialReference(inputwkid)
    outref = arcpy.SpatialReference(outputwkid)

    rings = arcpy.Array()
    for ring in ringpoints:
        rings.add(arcpy.Array([arcpy.Point(*x) for x in ring]))
    feature = arcpy.Polygon(rings, spatialref)

    if outputwkid is not None and outputwkid != inputwkid:
        feature = feature.projectAs(outref)

    return feature

def load_notices():
    """
    Load all notice AOIs from the database.

    Uses SQLAlchemy to access the database, pull all the data in and format it
     into rows that we'll turn into polys in a featureclass.

    returns the organized data and any problem areas found during parsing.
    """
    #build the list of raw data by user
    usersdb = User.query.all()
    users = {}
    badareas = []
    fields = [settings.geomfield] + settings.outfields
    for user in usersdb:
        usernotices = Notice.query.filter(Notice.userid == user.userid).all()
        notices = []
        for ntc in usernotices:
            try:
                name = ntc.name
                notifications = json.loads(ntc.notices)
                rawgeom = json.loads(ntc.geom)['geometry']
                geom = rawgeom.get('rings', None)
                if geom is None:
                    badareas.append({'user': user.email, 'area': ntc.name, 'reason': 'geom'})
                    continue
                if settings.inwkid not in rawgeom['spatialReference'].values():
                    print 'Error loading data: Incorrect Spatial References Found.'
                    print 'NoticeID:', ntc.noticeid
                    sys.exit(1)
                notices.append({'name': name, 'notices': notifications, 'geom': geom})
            except Exception as e:
                badareas.append({'user': user.email, 'area': ntc.name, 'reason': 'unknown'})

        users[user.email] = {'freq': user.freq, 'autoadd': user.autoadd, 
                             'citywide': user.citywide, 'notices': notices}

    output = []
    noticemap = {'bza': ['bza_docketed', 'bza_staffreport', 'bza_hearingresults'],
                 'cpc': ['cpc_docketed', 'cpc_staffreport', 'cpc_hearingresults'],
                 'zon': ['zon_checks']}
    usernames = sorted(users.keys())
    for email in usernames:
        row = []
        freq = users[email]['freq']
        autoadd = users[email]['autoadd']
        citywide = users[email]['citywide']
        if '@nola.gov' in email:
            early = True
        else:
            early = False
        for ntc in users[email]['notices']:
            bza = [1 if ntc['notices']['bza'] else 0 for x in noticemap['bza']]
            cpc = [1 if ntc['notices']['cpc'] else 0 for x in noticemap['cpc']]
            zon = [1 if ntc['notices']['zon'] else 0 for x in noticemap['zon']]
            row = [ntc['geom'], ntc['name'], email, early, autoadd, citywide, freq]
            row += bza + cpc + zon
            output.append(OrderedDict(zip(fields, row)))

    return output, badareas

if __name__ == '__main__':
    print 'Transporting Data:'
    #First, Load the data from the database.
    print ' - Loading Data from Database...'
    notices, badareas = load_notices()

    #Now write the output to the GDB.
    #First, create the GDB.
    print ' - Creating Output GDB...'
    try:
        gdb = make_gdb(settings.outloc, settings.outgdb)
    except TransportError as e:
        msg = 'Error Creating Output GDB:\n' + e.message
        print msg
        sys.exit(1)

    #Now, create the featureclass that we're dumping the data into.
    print ' - Creating Output Feature Class...'
    #First, delete the old one
    oldfc = os.path.join(gdb, settings.outfc)
    if arcpy.Exists(oldfc):
        try:
            arcpy.Delete_management(oldfc)
        except Exception as e:
            print 'Error Deleting Old AOIs:\n{0}'.format(e.message)
    try:
        fc = make_fc(gdb, settings.outfc, settings.outfields, settings.outwkid)
    except TransportError as e:
        msg = 'Error Creating Output Feature Class:\n' + e.message
        print msg
        sys.exit(1)

    #Now, dump the data into the featureclass.
    print ' - Saving Data...'
    cur = arcpy.da.InsertCursor(fc, ['SHAPE@'] + settings.outfields)
    for ntc in notices:
        geom = poly_from_rings(ntc[settings.geomfield], settings.inwkid, settings.outwkid)
        outrow = [geom] + [ntc.get(x, 0) for x in settings.outfields]
        cur.insertRow(outrow)
    del cur

    if len(badareas) > 0:
        print 'Issues found in user areas:'
        for bad in badareas:
            print ' - user: {0} | area: {1} | reason: {2}'.format(bad['user'], bad['area'], bad['reason'])

    print 'Transport Complete.'