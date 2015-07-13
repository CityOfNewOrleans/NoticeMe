from configobj import ConfigObj

"""
Import a configuration file for use in the NoticeMe applications.
"""

class ConfigError(Exception):
    def __init__(self, msg):
        self.message = msg
    def __repr__(self):
        return self.message

class Configurator(object):
    """
    Class to handle various special cases of config file reading.
    """
    #Section names
    GENERAL = 'General' 
    NOTICES = 'Notices'

    def __init__(self, fname):
        """
        Load the config file, and setup the class for reading the config

        fname is the name of the configuration file.
        """
        self.fname = fname
        self.config = ConfigObj(fname)

    def read_general_settings(self):
        """
        Read the general settings section from the config file.

        returns the general section as a dict.
        """
        if self.GENERAL not in self.config.keys():
            msg = 'General settings section "{0}" not found in {1}'
            raise ConfigError(msg.format(self.GENERAL, self.fname))

        generalcfg = self.config[self.GENERAL]
        return generalcfg

    def read_notice_settings(self, kind='spatial'):
        """
        Read the notices section from the config file.

        kind determines what kind of notices are returned:
          Spatially-dependent notices ('spatial') (default)
          Spatially-indpendent notices ('nonspatial')
          All notices ('all')

        returns a list of dicts of the notice settings of specified kind.
        """
        if self.NOTICES not in self.config.keys():
            msg = 'Notice settings section "{0}" not found in {1}'
            raise ConfigError(msg.format(self.NOTICES, self.fname))

        if kind.lower() not in ['spatial', 'nonspatial', 'all']:
            msg = 'Notice kind must be spatial, nonspatial, or all'
            raise ConfigError(msg.format(kind))

        noticecfg = []
        if kind.lower() == 'all':
            noticecfg = [self.config[self.NOTICES][x] for x in self.config[self.NOTICES].keys()]
        elif kind.lower() == 'spatial':
            noticecfg = [self.config[self.NOTICES][x] for x in self.config[self.NOTICES].keys()
                         if self.config[self.NOTICES][x]['spatial'].lower() == 'true']
        elif kind.lower() == 'nonspatial':
            noticecfg = [self.config[self.NOTICES][x] for x in self.config[self.NOTICES].keys()
                         if self.config[self.NOTICES][x]['spatial'].lower() == 'false']

        return noticecfg

    def read_settings(self, kind='spatial'):
        """
        Read and return settings - mostly compatible with the old way

        kind determines what kind of notices are returned:
          Spatially-dependent notices ('spatial') (default)
          Spatially-indpendent notices ('nonspatial')
          All notices ('all')

        returns a dict of General settings, and a list of dicts of the 
         subsections of section
        """
        generalcfg = self.read_general_settings()
        noticecfg = self.read_notice_settings(kind)
        return generalcfg, noticecfg


def read_settings(fname, general='General', section='Notices'):
    """
    Legacy method to read a config file, parse, and return the info needed.

    fname is the filename of the configuration file
    general is the name of the general config section in the file
    section is the specific section in the file to return

    returns a dict of General settings, and a list of dicts of the 
     subsections of section
    """
    required = [general, section]
    config = ConfigObj(fname)
    sections = config.keys()

    if len(sections) > 0:
        for sect in required:
            if sect not in sections:
                msg = 'Required section {0} not in {1}'.format(sect, fname)
                raise ConfigError(msg)
    else:
        msg = 'Config file {0} is empty'.format(fname)
        raise ConfigError(msg)

    generalcfg = config[general]
    sectioncfg = [config[section][x] for x in config[section].keys()]
    return config[general], sectioncfg


if __name__ == '__main__':
    cfg = Configurator('noticeme.cfg')
    gencfg, notices = cfg.read_settings('spatial')
    print 'General Section Options:'
    print '\n'.join([' - {0}'.format(x) for x in gencfg.keys()])
    print 'Notice Sections Options:'
    print '\n'.join([' - {0}'.format(x) for x in notices[0].keys()])
