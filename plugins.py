#!/usr/bin/python
#
# This file is part of leo-lookup.
# leo-lookup is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# leo-lookup is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with leo-lookup.  If not, see <http://www.gnu.org/licenses/>.
# 

# TODO:
#  __init__: check for __init__.py

import os
import sys
import logging

class plugin_manager(object):
    """
    Manages plugin handling.
    """
    def __init__(self, UIMANAGER, TREESELECTION, PLUGINDIR=""):
        logger = logging.getLogger('plugins.py:INIT')
        logger.info("Setting '%s' as plugin path" % (PLUGINDIR))
        self.treeselection = TREESELECTION
        self.plugindir = PLUGINDIR
        self.all_plugins = []
        self.loaded = []
        self.uimanager = UIMANAGER



        logger.info("Plugin engine initialized.")
#        self.load_plugins(PLUGINDIR)
        
        pass

    def load_plugins(self):
        """
        Loads plugins from a given pathname.
        """
        logger = logging.getLogger('plugins.py:load_plugins')
        path = self.plugindir
        if len(path) == 0:
            logger.warning("Invalid plugin-path. Skipping plugins ...")
            return
                     
        logger.info("Loading plugins:")
        for file in os.listdir(path):
            if file.endswith(".py"):
                logstr = "- %s :  " % (file)
                self.all_plugins.append(file)
                try:
                    pl = __import__(path+file[:len(file)-3])
                    pl.__init__(self.uimanager, self.treeselection)
                    self.loaded.append(pl)
                    logstr = logstr + "ok"
                except ImportError:
                    logstr = logstr + "failed"
                logger.info(logstr)

                
        logger.info('Following plugins have been found:\n %s' % (self.all_plugins))
        logger.info('Following plugins have been loaded:\n %s' % 
                    (self.loaded))

        pass
