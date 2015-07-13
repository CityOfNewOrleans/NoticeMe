import collections
import os

import arcpy

"""
Module to encapsulate the methods and classes necessary to do spatial processing
 for NoticeMe.
"""

LASTATEPLANE = "PROJCS['NAD_1983_StatePlane_Louisiana_South_FIPS_1702_Feet',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',3280833.333333333],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-91.33333333333333],PARAMETER['Standard_Parallel_1',29.3],PARAMETER['Standard_Parallel_2',30.7],PARAMETER['Latitude_Of_Origin',28.5],UNIT['Foot_US',0.3048006096012192]];-124791100 -91255500 3048.00609601219;-100000 10000;-100000 10000;3.28083333333333E-03;0.001;0.001;IsHighPrecision"

class ArcError(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return self.message

def make_gdb(location, gdbname):
    """
    Create a file geodatabase for processing spatial joins.

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
            raise ArcError(e.message)
        if res.status != 4: #4 indicates success.
            raise ArcError(res.getMessage(0))

    return gdb


def keep_gdb(gdbpath, procdate):
    """
    Renames a GDB so it can be kept without interfering in future processing.

    gdbpath is the full path of the file geodatabase.
    procdate is a string that is added to the gdb name (process date).

    no return.
    """
    if arcpy.Exists(gdbpath):
        gdbloc, gdbname = os.path.split(gdbpath)
        newname = gdbname.split('.')[0] + '_' + procdate + '.gdb'
        newpath = os.path.join(gdbloc, newname)
        arcpy.Rename_management(gdbpath, newpath)
    else:
        msg = 'Cannot find GDB {0}'.format(gdbpath)
        raise ArcError(msg)


def del_gdb(gdbpath):
    """
    Deletes a GDB from disk.

    gdbpath is the full path of the file geodatabase.

    no return.
    """
    if arcpy.Exists(gdbpath):
        arcpy.Delete_management(gdbpath)
    else:
        msg = 'Cannot find GDB {0}'.format(gdbpath)
        raise ArcError(msg)


def make_points(gdb, fcname, spatialref, rows, xname='X', yname='Y'):
    """
    Make a point featureclass in the specified geodatabase, overwriting if necessary.

    gdb is the name and location of the gdb.
    fcname is the name of the featureclass to create.
    spatialref is the spatial reference to use.
    rows is a list of OrderedDicts of the data to put into the feature class.
     must contain x and y fields ('X' and 'Y' by default) for the geometry, and
     can contain any number of other fields, however, they will all be text,
     254 char.
    xname is the name of field containing the X-position.
    yname is the name of field containing the Y-position.

    returns the path to the created feature class.
    """
    arcpy.env.overwriteOutput = True
    geom = 'POINT'
    template = ''
    hasm = 'DISABLED'
    hasz = 'DISABLED'
    try:
        res = arcpy.CreateFeatureclass_management(gdb, fcname, geom, template,
                                                  hasm, hasz, spatialref)
    except Exception as e:
        raise ArcError(e.message)

    if res.status != 4:
        msg = 'Error Creating Feature Class {0}\n'.format(fcname)
        msg += res.getMessage(0)
        raise ArcError(msg)

    fc = ''
    if len(rows) > 0:
        fc = os.path.join(gdb, fcname)
        fldtyp = 'TEXT'
        fldlen = '254'
        fields = rows[0].keys()
        if xname not in fields or yname not in fields:
            raise ArcError('Cannot find geometry in the provided rows.')
        addfields = [x for x in fields if x not in [xname, yname]]
        for fld in addfields:
            res = arcpy.AddField_management(fc, fld, fldtyp, "", "", fldlen,
                                            "", "NULLABLE", "NON_REQUIRED", "")
            if res.status != 4:
                raise ArcError('Error adding field {0} to {1}'.format(fld, fcname))

        #Now, add the actual data.
        cur = arcpy.da.InsertCursor(fc, ['SHAPE@XY']+addfields)
        for row in rows:
            pnt = (row[xname], row[yname])
            cur.insertRow([pnt]+[row[x] for x in addfields])
        del cur
    return fc


def build_fieldmap(tables, outfields, uidname=None):
    """
    Invokes the Black Majick incantations necessary to summon an ESRI fieldmap.

    Fieldmaps often look like strings, but apparently, they are so carefully
     crafted that you must build them using the ESRI FieldMappings class.  Woe
     be unto thee if you attempt otherwise.

    tables is a list of table names that hold the data that will be merged or
     joined into the final output.
    outfields is a list of field names (in the tables) that will exist in the
     final field map.
    uidname is the name of a unique identifier field that will be used to hold
     a list of uids in the final spatial-joined featureclass.  This defaults
     to None to be a more general field map building routine.

    returns the summoned fieldmap.
    """
    #Start with the fields as they currently exist in the input featureclasses.
    originalmaps = arcpy.FieldMappings()
    for table in tables:
        originalmaps.addTable(table)
    #Build the output fieldmap from the original field definitions.
    outmap = arcpy.FieldMappings()
    for field in outfields:
        fieldidx = originalmaps.findFieldMapIndex(field)
        if fieldidx >= 0:
            outmap.addFieldMap(originalmaps.getFieldMap(fieldidx))
        else:
            errmsg = 'Error adding the field {0} to the output field map.'
            raise ArcError(errmsg.format(field))

    #If a uid fieldname has been passed, modify the UID field to implement
    # the merge rules, etc. necessary for the spatial join.  This part is
    # specific to what we need for NoticeMe.
    if uidname is not None:
        uididx = outmap.findFieldMapIndex(uidname)
        if uididx >= 0:
            uidmap = outmap.getFieldMap(uididx)
            uidfield = uidmap.outputField
            #This is a really long field, because the join throws an error if it
            # can't fit the output into the results field.  I wish there were a
            # way to get final field length before I actually execute the join,
            # but there's no way to really do that.
            uidfield.length = 300000
            uidfield.name = uidname
            uidmap.outputField = uidfield
            uidmap.mergeRule = 'join'
            uidmap.joinDelimiter = '|'
            outmap.replaceFieldMap(uididx, uidmap)
        else:
            errmsg = 'UID Field {0} not found in input tables.'
            raise ArcError(errmsg.format(uidname))

    return outmap


def select_and_join(aoisource, pointsfc, gdb, selectsql, outfields, uidname):
    """
    For a given notice type, select the appropriate AOIs and execute the spatial join.

    aoisource is the location of the AOI polygons.
    pointsfc is the name of points featureclass we want to join to the AOIs.
     This should be the same as the table that we made when we fetched the data,
     and is the name of the featureclass we created using make_points().
     This is not a fully qualified path, just the name of the featureclass.
    gdb is the full path to the temp geodatabase to use for processing.
    selectsql is the SQL query used to filter the AOEs into selected.
    outfields are the fields we actually want in the joined output.
    uidname is the name of the unique id field.

    returns the full path name of the joined output featureclass.
    """
    arcpy.env.overwriteOutput = True
    #First, select the appropriate aoe polygons
    selected = os.path.join(gdb, 'selected')
    arcpy.Select_analysis(aoisource, selected, selectsql)
    #Now, build the spatial-joined output fieldmap.
    noticetable = os.path.join(gdb, pointsfc)
    #Check to make sure there are any points.  If uidname is not in the fields,
    # then no points were created and we need to skip this featureclass.
    fcfields = arcpy.ListFields(noticetable)
    fcfieldnames = [x.name for x in fcfields]
    if uidname in fcfieldnames:
        outmap = build_fieldmap([selected, noticetable], outfields, uidname)
        #Now, execute the spatial join.
        joinout = os.path.join(gdb, pointsfc+'_joined')
        joinop = 'JOIN_ONE_TO_ONE'
        jointype = 'KEEP_COMMON'
        joinmatch = 'INTERSECT'
        res = arcpy.SpatialJoin_analysis(selected, noticetable, joinout, joinop,
                                         jointype, outmap, joinmatch, "", "")
        if res.status != 4:
            msg = 'Error Executing Join:\n'
            msg += res.getMessage(0)
            raise ArcError(msg)
    else:
        joinout = None

    return joinout


def extract_results(fclass, fcfields, exportfields):
    """
    Extracts data from the attribute table of a featureclass.

    fclass is the featureclass from which we should extract the data (full path,
     as returned by select_and_join()).
    fcfields is a list of field names (as they are in the featureclass) to extract.
    exportfields is a list of field names as they should be saved.
     fcfields and exportfields should have entries corresponding to one another
     in the same place in the list.  i.e.:
     fcfields = ['NAME', 'emailaddr', 'UID']
     exportfields = ['name', 'emailaddr', 'uids']

    returns a list of OrderedDicts containing the requested data.
    """
    outdata = []
    if len(fcfields) != len(exportfields):
        msg = 'Featureclass field names ({0}) do not match export field names ({1}).'
        raise ArcError(msg.format(fcfields, exportfields))
    cur = arcpy.da.SearchCursor(fclass, fcfields)
    for row in cur:
        outdata.append(collections.OrderedDict(zip(exportfields, row)))
    return outdata
