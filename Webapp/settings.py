"""NoticeMe Web App Settings"""

#Flask's debug behavior.
debug = True

#Connection string for connecting to a DB.  SQLite should only be used for dev.
constr = 'sqlite:///C:\\Scripts\\NoticeMe\\Webapp\\noticeme.sqlite' #Dev
#constr = 'mssql+pyodbc://<username>:<password>@<server>/NoticeMe?driver=SQL Server Native Client 10.0' #Staging
#constr = 'mssql+pyodbc://<username>:<password>@<server>/NoticeMe' #Production

#Hostname.  Required to be correct for Persona.
hostname = 'http://localhost:5000/' #Dev (while running from command line)
#hostname = 'http://cno-scripts01/' #Staging
#hostname = 'http://noticeme.nola.gov'  #Production