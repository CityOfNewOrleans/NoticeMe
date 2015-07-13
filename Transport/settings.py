""" NoticeMe Transport Settings file. """

#Connection string to the production database (extract from)
constr = 'sqlite:///C:\\Users\\jbraasch\\Desktop\\NoticeMe_new\\site\\noticeme.sqlite' #Dev
#constr = 'mssql+pyodbc://<username>:<password>@<server>/NoticeMe?driver=SQL Server Native Client 10.0' #Staging
#constr = 'mssql+pyodbc://<username>:<password>@<server>/NoticeMe' #Production

#Spatial References.
# Some input polys have two wkids: 102100 and 3857.  Both refer to the same
# projection (WGS 1984 Web Mercator Auxiliary Sphere), so we need to make sure
# one (we're using 3857, the new number as of Arc10.1) of the two is in the
# spatialRef as saved by the web map.  We also need to project to LA State Plane
# South (ft.) for the spatial joins that are done by the backend.
inwkid = 3857 #WGS 1984 Web Mercator Auxiliary Sphere
outwkid = 3452 #NAD 1983 StatePlane Louisiana South FIPS 1702 Feet

#Location and name of the output GDB (extract to)
outloc = 'C:\\Scripts\\NoticeMe\\Transport'
outgdb = 'NoticeMe_AOIs.gdb'
outfc = 'AOIs'

#Output fields in the GDB
outfields = ['name', 'emailaddr', 'early', 'autoadd', 'citywide', 'freq', 
             'bza_docketed', 'bza_staffreport', 'bza_hearingresults',
             'cpc_docketed', 'cpc_staffreport', 'cpc_hearingresults',
             'zon_checks']

#Name of the field in the input that contains the geometry.
geomfield = 'geom'
