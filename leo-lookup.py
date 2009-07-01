#!/usr/bin/python
# -*- coding: utf-8 -*-

# leo-lookup - Utility to look up translations for a word using dict.leo.org
# Copyright (C) 2009 Markus Zeindl <mrszndl@googlemail.com>
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. 
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details. 
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# import general packages
import os
import sys

# import gui packages
import gtk
import gobject
#import gdk

# import other needed or useful packages
import urllib2
import urllib
import logging
import formatter
import datetime
import getopt

# import own modules
import llresultextractor2
import plugins

__path__ = "."

LOGFILENAME = "leo-lookup.log"
HOMEDIR = "/home/bitmaster/source/python/gtk/leo-lookup/"
IMGDIR = HOMEDIR+"images/"
PLUGINDIR = "plugins/"

class leolookup:
    """Represents the programme, with the window."""
    __version__ = "0.2"
    
    url = "http://dict.leo.org/"
    supportedLangs = { "German":"de", "English" : "en", "Spanish" : "es", 
                       "Italian" : "it", "French" : "fr", "Chinese" : "ch" }

    menubardesc = """
<ui>
  <menubar name="Mainmenu">
    <menu action="File">
      <menuitem name="Quit" action="Quit" />
    </menu>
    <menu action="Extensions">
      <separator/>
      <menuitem name="Preferences" action="ext_prefs" />
    </menu>
    <menu action="Help">
      <menuitem name="about" action="aboutdlg" />
    </menu>
  </menubar>
</ui>
"""
    def __init__(self):
        logger = logging.getLogger('INIT')
        self.uimanager = gtk.UIManager()
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        gtk.window_set_default_icon_from_file(IMGDIR+"icon.png")
        self.window.set_size_request(490,420)
        self.window.set_title("leo-lookup Version " + self.__version__)
        self.window.connect("destroy", self.destroyWin)

        self.box = gtk.VBox(False, 5)
        
        self.menubar_acts = [
                             ('File', None, "_File"),
                             ('Quit', gtk.STOCK_QUIT, "_Quit", None, 
                              "Close Program", self.destroyWin),
                             
                             ('Extensions', None, "_Extensions"),
                             ('ext_prefs', None, "_Preferences", None,
                              "Set prefereences for extensions", None),

                             ('Help', None, "_Help"),
                             ('aboutdlg', None, "_About", None,
                              "View informations about leo-lookup.", None)

                             ]
                             
        self.actgroup = gtk.ActionGroup("LEO_LOOKUP")
        self.actgroup.add_actions(self.menubar_acts)

        accelgroup = self.uimanager.get_accel_group()
        self.window.add_accel_group(accelgroup)
        self.uimanager.add_ui_from_string(self.menubardesc)
        self.uimanager.insert_action_group(self.actgroup, 0)
        self.menubar = self.uimanager.get_widget("/Mainmenu")
        self.box.pack_start(self.menubar, False)
      
        self.word2lookup = gtk.Entry()
        self.word2lookup.set_text("Enter word to lookup here ...")
        self.box.pack_start(self.word2lookup, False, False, 0)

        self.box2 = gtk.HBox(False, 6)
        

        self.fromLangLabel = gtk.Label("From ")
        self.box2.pack_start(self.fromLangLabel, False, False, 0)

        # Create combo box for the language to translate from
        self.lstst_fromLang = gtk.ListStore(gtk.gdk.Pixbuf, str)
        self.fromLang = gtk.ComboBox(self.lstst_fromLang)
        cellpb = gtk.CellRendererPixbuf()
        cellt  = gtk.CellRendererText()
        self.fromLang.pack_start(cellpb, True)
        self.fromLang.pack_start(cellt, True)
        self.fromLang.add_attribute(cellpb, 'pixbuf', 0)
        self.fromLang.add_attribute(cellt, 'text', 1)

        # add languages to combobox
        for lang in self.supportedLangs:
            self.lstst_fromLang.append([gtk.gdk.pixbuf_new_from_file(
                    IMGDIR+lang+".png"),
                    lang])
        self.fromLang.set_active(0)
        self.box2.pack_start(self.fromLang, False, False, 0)

        self.swapToFrom = gtk.Button("<>")
        self.swapToFrom.connect("clicked", self.swapToFromClicked)
        self.box2.pack_start(self.swapToFrom, False, False, 0)


        self.toLangLabel = gtk.Label("to ")
        self.box2.pack_start(self.toLangLabel, False, False, 0)

        # Create combo box for the language to translate to
        self.lstst_toLang = gtk.ListStore(gtk.gdk.Pixbuf, str)
        self.toLang = gtk.ComboBox(self.lstst_toLang)
        self.toLang.pack_start(cellpb, True)
        self.toLang.pack_start(cellt, True)
        self.toLang.add_attribute(cellpb, 'pixbuf', 0)
        self.toLang.add_attribute(cellt, 'text', 1)
        for lang in self.supportedLangs:
            self.lstst_toLang.append([gtk.gdk.pixbuf_new_from_file(
                    IMGDIR+lang+".png"),
                    lang])
        self.toLang.set_active(1)
        
        self.box2.pack_start(self.toLang, False, False, 0)

        # Create indicator of successes
        self.results = gtk.Label("")
        self.box2.pack_end(self.results, False, False, 0)

        self.box.pack_start(self.box2, False, False,0)

        self.lookup = gtk.Button("Look up!")
        self.lookup.connect("clicked", self.onTransClick)
        self.box.pack_start(self.lookup, False, False, 0)
        
        self.scrollcont = gtk.ScrolledWindow()
        self.scrollcont.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        
        self.meanings = gtk.ListStore(str,str)
        self.listOfMeanings = gtk.TreeView(self.meanings)
        self.listOfMeaningsCol = gtk.TreeViewColumn("Foreign Lang.")
        self.listOfMeanings.append_column(self.listOfMeaningsCol)
        cell = gtk.CellRendererText()
        self.listOfMeaningsCol.pack_start(cell, True)
        self.listOfMeaningsCol.add_attribute(cell, 'text', 0)
        
        self.listOfMeaningsCol2 = gtk.TreeViewColumn("Familiar Lang.")
        self.listOfMeanings.append_column(self.listOfMeaningsCol2)
        cell2 = gtk.CellRendererText()
        self.listOfMeaningsCol2.pack_start(cell2, True)
        self.listOfMeaningsCol2.add_attribute(cell2, 'text', 1)

        self.lom_treesel = self.listOfMeanings.get_selection()
        self.lom_treesel.set_mode(gtk.SELECTION_MULTIPLE)

        self.scrollcont.add(self.listOfMeanings)
        self.box.pack_start(self.scrollcont, True, True, 0)

        self.box.show_all()

        self.window.add(self.box)
        logger.info("window constructed, let's make it visible ...")
        self.window.show_all()

        logger.info("initializing plugin architecture ...")
        pm = plugins.plugin_manager(self.uimanager,
                                    self.lom_treesel,
                                    PLUGINDIR)
        pm.load_plugins()
        gtk.main()
        
    
    def swapToFromClicked(self, *args):
        """
        Will be executed if the user clicks on the swap button between the to combo boxes. Makes the target language the source language and vice versa.
        """
        temp = self.fromLang.get_active()
        self.fromLang.set_active(self.toLang.get_active())
        self.toLang.set_active(temp)

    def onTransClick(self, *args):
        """
        Will be executed if the user clicks on the "Translate"-button
        """

        # initialize the logger
        logger = logging.getLogger('onTransClick')
        logger.setLevel(logging.DEBUG)

        # check and define the search direction
        lang1iter = self.fromLang.get_active_iter()
        lang2iter = self.toLang.get_active_iter()

        lang1 = self.lstst_fromLang[self.lstst_fromLang.get_path(lang1iter)][1]
        lang2 = self.lstst_toLang[self.lstst_toLang.get_path(lang2iter)][1]
        logger.debug("from language: %s" % (lang1))
        logger.debug("to language: %s" % (lang2))

        # the user has chosen two equal languages, which is nonsense
        # (e. g. translation from German to German)
        if lang1 == lang2:
            messagedlg = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, 
                                           gtk.BUTTONS_OK, "Translation in the same language makes no sense!")
            messagedlg.set_title("Error!")
            messagedlg.run()
            messagedlg.destroy()
            return

        # determine where the foreign language is specified
        if  lang2 == "German":
            # (lang1 == foreign language)
            searchLoc = -1
            pagename = self.supportedLangs[lang1] + "de"
            self.foreignlang = lang1

        elif lang1 == "German":
            # (lang2 == foreign language)
            searchLoc = 1
            pagename = self.supportedLangs[lang2] + "de"
            self.foreignlang = lang2

        else:
            logger.debug("Couldn't determine search direction, taking automatic mode.")
            searchLoc = 0


        # Make boxes for header widgets (column one and two)
#        head_col1 = gtk.HBox(False,2)
#        head_col2 = gtk.HBox(False,2)

        # construct box for foreign language column header

#        flag = gtk.Image()
#        flag.set_from_file(IMGDIR+self.foreignlang+".png")
#        lbl = gtk.Label(self.foreignlang)
#        head_col1.pack_start(flag, False, False, 0)
#        head_col1.pack_start(lbl, False, False, 0)
#        head_col1.show()

        # construct box for German language column header 
#        flag2 = gtk.Image()
#        flag2.set_from_file(IMGDIR+"German.png")          
#        lbl2 = gtk.Label("German")
#        head_col2.pack_start(flag2, False, False, 0)
#        head_col2.pack_start(lbl2, False, False, 0)
#        head_col2.show()

        # set headers of the columns
        self.listOfMeaningsCol.set_title(self.foreignlang)
        self.listOfMeaningsCol2.set_title("German")
#        self.listOfMeaningsCol.set_widget(lbl)
#        self.listOfMeaningsCol2.set_widget(lbl2)
        
        # define arguments to be committed to the webserver, like
        # the word, we are looking up.
        args = {"relink" :"off", 
                "search" : self.word2lookup.get_text(), 
                "searchLoc" : searchLoc}

        data = urllib.urlencode(args)
        # do communication with the webserver
        request = urllib2.Request(self.url+pagename, data)
        logger.info("Requesting from URL: %s" % (request.get_full_url() + '?'
                                                  + request.get_data()))
        response = urllib2.urlopen(request)

        # read the answer and save it in a local variable
        html = response.read()
        # get interesting things of the webpage
        # IoUT = Index of Unmittelbare Treffer
        # eoIT = end of Interesting Things
        # soIT = start of ------"-------
        # ipof = interesting piece of file
        if " " in self.word2lookup.get_text().strip():
            IoUT = html.find("bereinstimmung")
        else:
            IoUT = html.find("Unmittelbare Treffer")
        eoIT = html.find("</table>", IoUT)
        soIT = html.rfind("<table", 1, eoIT)
        ipof = html[soIT:eoIT+8] # +8 adds the closing table-tag
        logger.debug(ipof)
        logger.debug("IoUT: %s\teoIT: %s\tsoIT: %s\t" % (IoUT, eoIT, soIT))

        # make instance of result extractor class and submit data
        myhtmlparser = llresultextractor2.ResultExtractor()
        myhtmlparser.feed(ipof)
        myhtmlparser.close()

        # extract results from webpage
        results = myhtmlparser.getResults()
        self.meanings.clear()
        logger.debug(results)

        # the last element of the gotten data stores the amount of results.
        # put it in an extra variable and remove it from the list.
        successes = results.pop()
        logger.debug("successes: %s" % (successes))

        # checks if we have got results
        if successes == 0:
            self.results.set_text("No results ")
        else:
            self.results.set_text("%s results " % (successes))

        # adds result-pairs (other lang, german) and manage letters like
        # äüö
        for pair in results:
            self.meanings.append([pair[0].decode("iso-8859-15"),pair[1].decode("iso-8859-15")])
            logger.debug(pair)
        self.listOfMeanings.columns_autosize()
            
     
    def getTagsWoAttr(self, html):
        cnt = html.count("=")
        pos_attr = 0
        print "%s attributes were found." % (cnt)
        for z in range(0, cnt):
            pos_attr_alt = pos_attr
            pos_attr = html.find("=")
            end_attr = html.find(" ", pos_attr)
            beg_attr = html[pos_attr_alt:end_attr].rfind(" ")
            html = html.replace(html[beg_attr:end_attr], "")
        return html

    def destroyWin(self, *args):
        """Will be executed if the user wants to close the window."""
        logger = logging.getLogger('DESTROY')
        logger.info("Terminate leo-lookup...\n")
        gtk.main_quit()
        sys.exit(0)

    def make_menu_item(self, name, callback, data=None):
        """Creates and returns a menu item"""
        item = gtk.MenuItem(name)
        item.connect("activate", callback, data)
        item.show()
        return item
    
    def get_active_text(self,combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0]


def getUIManager():
    """
    Returns the used UIManager for the mainwindow. This is needed by
    installed plugins, to integrate themselves into mainmenu.
    """
    return self.uimanager

def help_msg():
    """
    Prints a general help message, explaining the commandline-interface
    of leo-lookup. Only used if user starts leo-lookup with the commandline
    switch '-h'.
    """
    print """Usage: leo-lookup.py [OPTION]
Search for translations of words using the online dictionary LEO.

Available options:
 -d, --debug=LEVEL     Specifies verbosity regarding debug messages.
                       LEVEL can be 'debug', 'info', 'warning', 'error', 
                       'critical' (default: 'warning').
 -l, --logfile=FILE    Set the output file for logging messages 
                       (default: 'leo-lookup.log').
 -h, --help            Show this help message.

Report bugs to <leo-lookup-feedback@nongnu.org> or go to
'http://savannah.nongnu.org/bugs/?func=additem&group=leo-lookup'.
"""

def check_cwd(mainmod):
    """
    check if current working directory is leo-lookup's home directory
    extract the path and filename of "leo-lookup.py", which has been 
    launched
    """
    # mainmod represents the path and name of this file.
    mainmod_path  = mainmod[:mainmod.rfind(os.sep)]
    mainmod_fn    = mainmod[mainmod.rfind(os.sep)+1:]
    
    try:
        # try to locate leo-lookup.py in the current working directory
        # if this test fails, we can change to leo-lookup's home directory
        os.stat(mainmod_fn)
    except OSError:
        os.chdir(mainmod_path)

def check_usrdatadir():
    """
    Checks if the directory ~/.config/leo-lookup exists and creates
    it if needed.
    """
    usrname = os.getlogin()
    usrdatadir = "/home/" + usrname + "/.config/leo-lookup"
    try:
        os.stat(usrdatadir)
    except OSError:
        os.mkdir(usrdatadir)

if __name__ == "__main__":
    LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}
    # set loglevel warning as standard 
    level_name = "warning"

# not needed, since the feature of saving/loading preferences isn't 
# implemented in leo-lookup, so far.
#    check_usrdatadir()
    check_cwd(sys.argv[0])

    # check if the user has specified a log-level
    if len(sys.argv) > 1:

        # parse commandline arguments
        shopts = "hd:l:"
        lngopts = [ "help", "debug=", "logfile=" ]
        pars_args = getopt.gnu_getopt(sys.argv[1:], shopts, lngopts)
        for pair in pars_args[0]:
            if pair[0].endswith("help") or pair[0].endswith("h"):
                help_msg()
                exit(0)
            elif pair[0].endswith("debug") or pair[0].endswith("d"):
                level_name = pair[1]
            elif pair[0].endswith("logfile") or pair[0].endswith("l"):
                LOGFILENAME=pair[1]

        # configure logging facility according to commandline args
        
        level = LEVELS.get(level_name, logging.NOTSET)
        logging.basicConfig(filename=LOGFILENAME,level=level)
    else:
        logging.basicConfig(filename=LOGFILENAME, level=logging.INFO)
    curDateTime = datetime.datetime.isoformat(datetime.datetime.now())
    logging.info("\nlogging facility started on %s\t" % (curDateTime))
    logging.info("------------------------------")
  
    # launch main app
    app =  leolookup()


