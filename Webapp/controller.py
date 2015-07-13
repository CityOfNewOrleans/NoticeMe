from database import db_session
from models import User, Notice

class DataError(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return self.message

def get_userinfo(emailadd):
    """
    Gets a user's information for notice retrieval.

    emailadd is the email address of the user.

    Returns userid, frequency, autoadd, and citywide. userid is -1 if they don't exist.
    """
    userid = -1
    frequency = 'w' #Default email frequency is weekly.
    autoadd = 1 #Default is to add new notices.
    citywide = 1 #Default is to receive citywide notices.
    existingusers = User.query.filter(User.email == emailadd).all()
    if len(existingusers) == 1:
        userid = existingusers[0].userid
        frequency = existingusers[0].freq
        autoadd = existingusers[0].autoadd
        citywide = existingusers[0].citywide
    elif len(existingusers) > 1:
        #urg.  Something really awful is happening with the database.
        msg = 'Error retrieving user info.'
        raise DataError(msg)
    return userid, frequency, autoadd, citywide

def add_user(emailadd, frequency, autoadd, citywide):
    """
    Adds a user to the database.

    emailadd is the email address of the user.
    frequency is the email notice frequency.
    autoadd is a preference to automatically add new notices to user areas.
    citywide is a preference to receive notices with city-wide impact.

    Returns the userid of the newly added user, or -1 if they already existed.
    """
    userid = -1
    existingusers = User.query.filter(User.email == emailadd).all()
    if len(existingusers) == 0:
        newu = User(email=emailadd, freq=frequency, autoadd=autoadd, citywide=citywide)
        db_session.add(newu)
        db_session.commit()
        addedusers = User.query.filter(User.email == emailadd).all()
        if len(addedusers) == 1:
            userid = addedusers[0].userid
        else:
            #Something bad happened.  Raise an error.
            msg = 'Error adding user to the database.'
            raise DataError(msg)
    elif len(existingusers) > 1:
        #urg.  Something really awful is happening with the database.
        msg = 'Error adding user to the database.'
        raise DataError(msg)
    return userid

def get_user_data(emailadd):
    """
    Gets a user's information and areas for return to the webpage.

    emailadd is the email address of the signed in user.

    returns a user's information from the users and notices tables as a dict.
    """
    data = {}
    areas = []
    userid, frequency, autoadd, citywide = get_userinfo(emailadd)
    if userid == -1:
        #Add the user; this is their first login.
        userid = add_user(emailadd, frequency, autoadd)
    else:
        notices = Notice.query.filter(Notice.userid == userid).all()
        for ntc in notices:
            ntcdata = {'id': ntc.userid, 
                       'namehash': ntc.namehash,
                       'name': ntc.name,
                       'notices': ntc.notices,
                       'geom': ntc.geom}
            areas.append(ntcdata)

    data['email'] = emailadd
    data['id'] = userid
    data['freq'] = frequency
    data['autoadd'] = autoadd
    data['citywide'] = citywide
    data['areas'] = areas
    return data

def save_data(userid, namehash, name, notices, geom):
    """
    Inserts a notification area into the database.

    userid is the user id number of the row.
    namehash is the hash of the area name.
    name is the user-defined area name.
    notices is a json string of the notices object.
    geom is a json string of the geometry of the area.

    Returns True on success.
    """
    newnotice = Notice(userid=userid, 
                       namehash=namehash, 
                       name=name, 
                       notices=notices, 
                       geom=geom)
    try:
        db_session.add(newnotice)
        db_session.commit()
        success = True
    except Exception as e:
        msg = 'Error adding notification:\n' + e.message
        raise DataError(msg)
    return True

def update_data(oldhash, userid, namehash, name, notices, geom):
    """
    Updates a notification in the database.

    oldhash is the original namehash of the area.
    userid is the user id number of the row.
    namehash is the hash of the area name.
    name is the user-defined area name.
    notices is a json string of the notices object.
    geom is a json string of the geometry of the area.

    Returns True on success.
    """
    success = False
    existingareas = Notice.query.filter(Notice.userid == userid, Notice.namehash == oldhash).all()
    if len(existingareas) == 1:
        try:
            existingareas[0].namehash = namehash
            existingareas[0].name = name
            existingareas[0].notices = notices
            existingareas[0].geom = geom
            db_session.commit()
            success = True
        except Exception as e:
            msg = 'Error updating notification:\n' + e.message
            raise DataError(msg)
    elif len(existingareas) == 0:
        #We can't find the thing we're supposed to be updating.
        # Better to add it and have a mess than just lose it silently.
        success = save_data(userid, namehash, name, notices, geom)
    else:
        #yuck.  Bad database again.
        msg = 'Error updating notification: Bad data in database.'
        raise DataError(msg)
    return success

def delete_data(userid, namehash):
    """
    Deletes a notification from the database.

    userid is the user id number on the row.
    namehash is the hash of the area name.

    Returns True on success.
    """
    success = False
    existingareas = Notice.query.filter(Notice.userid == userid, Notice.namehash == namehash).all()
    try:
        for ext in existingareas:
            db_session.delete(ext)
        db_session.commit()
        success = True
    except Exception as e:
        msg = 'Error deleting notification:\n' + e.message
        raise DataError(msg)
    return success

def update_user(emailadd, frequency, autoadd, citywide):
    """
    Updates a user's preferences in the database.

    emailadd is the user's email address.
    frequency is the preferred email frquency.
    autoadd is a preference to automatically add new notices to user areas.

    Returns True on success.
    """
    success = False
    existingusers = User.query.filter(User.email == emailadd).all()
    if len(existingusers) == 1:
        try:
            existingusers[0].freq = frequency
            existingusers[0].autoadd = autoadd
            existingusers[0].citywide = citywide
            db_session.commit()
            success = True
        except Exception as e:
            msg = 'Error updating user info:\n' + e.message
            raise DataError(msg)
    elif len(existingusers) > 1:
        #hurk.  Bad database again.
        msg = 'Error updating user info: Bad data in database.'
        raise DataError(msg)
    return success

if __name__ == '__main__':
    emailadd = 'name@example.com'
    frequency = 'd'
    autoadd = 0
    area1 = ['a15eb01ce68198b01e535347ef46d51c', 'ADAMS COURT', '{""cpc"": true, ""zon"": true, ""bza"": true}', '{""geometry"": {""rings"": [[[-10013255.5680646, 3506522.89585563], [-10013283.258175, 3506914.94324318], [-10013068.4290009, 3506941.73509836], [-10013023.2184456, 3506616.24186801], [-10013255.5680646, 3506522.89585563]]], ""spatialReference"": {""wkid"": 102100, ""latestWkid"": 3857}}, ""attributes"": {""Organization_Name"": ""ADAMS COURT""}, ""symbol"": {""color"": [51, 102, 204, 102], ""style"": ""esriSFSSolid"", ""type"": ""esriSFS"", ""outline"": {""color"": [51, 102, 204, 255], ""width"": 2.25, ""style"": ""esriSLSSolid"", ""type"": ""esriSLS""}}}']
    area2 = ['3af6a990ddcad8091fb4fea953ec479b', 'Irish Channel Neighborhood Association', '{""cpc"": true, ""zon"": true, ""bza"": true}', '{""geometry"": {""rings"": [[[-10028639.7012976, 3493658.66555108], [-10028519.7857158, 3493711.2211381], [-10028465.0280131, 3493737.57310123], [-10028379.7820962, 3493781.85279324], [-10028357.1775308, 3493795.48691294], [-10028266.3528935, 3493855.07001173], [-10028177.6492096, 3493913.43970446], [-10028087.265206, 3493971.11953558], [-10027936.6618728, 3494069.11237152], [-10027841.6284989, 3494130.7670262], [-10027752.1192001, 3494188.52565129], [-10027662.599869, 3494247.13164396], [-10027572.3070735, 3494305.69330888], [-10027505.1319132, 3494348.79033413], [-10027405.740354, 3494422.97016949], [-10027303.5704312, 3494500.43943901], [-10026697.2947755, 3493693.19151393], [-10026809.3657463, 3493619.55022694], [-10027063.1084735, 3493509.53848122], [-10027472.8486203, 3493350.87361789], [-10027955.2341589, 3493174.48706374], [-10028058.6845828, 3493133.13157543], [-10028153.5587189, 3493104.82032099], [-10028256.7905701, 3493083.52271714], [-10028389.2126396, 3493063.35587632], [-10028639.7012976, 3493658.66555108]]], ""spatialReference"": {""wkid"": 102100, ""latestWkid"": 3857}}, ""attributes"": {""Organization_Name"": ""Irish Channel Neighborhood Association""}, ""symbol"": {""color"": [51, 102, 204, 102], ""style"": ""esriSFSSolid"", ""type"": ""esriSFS"", ""outline"": {""color"": [51, 102, 204, 255], ""width"": 2.25, ""style"": ""esriSLSSolid"", ""type"": ""esriSLS""}}}']
    testhash = '9ef0d87c220b3bb34a204cf22d9c3416'

    print 'Create a user:'
    userinfo = get_user_data(emailadd)
    print get_user_data(emailadd)

    userid = userinfo['id']
    
    print '\nChange email frequency:'
    if update_user(emailadd, frequency, autoadd):
        print get_user_data(emailadd)

    print '\nInsert two rows:'
    save1 = save_data(userid, area1[0], area1[1], area1[2], area1[3])
    save2 = save_data(userid, area2[0], area2[1], area2[2], area2[3])
    if (save1 and save2):
        print get_user_data(emailadd)

    print '\nChange one of them:'
    update1 = update_data(area1[0], userid, testhash, 'TEST TEST TEST', area1[2], area1[3])
    if update1:
        print get_user_data(emailadd)

    print '\nDelete one of them:'
    del1 = delete_data(userid, area2[0])
    if del1:
        print get_user_data(emailadd)

    print '\nLooking good!'