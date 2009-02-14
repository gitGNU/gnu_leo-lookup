#!/usr/bin/python
# -*- coding: utf-8 -*-

# leo-lookup - Utility to look up translations for a word using leo
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

# import other needed or useful packages
import urllib2
import urllib
import logging
import formatter
import datetime

# import own modules
import llresultextractor2

LOGFILENAME = "leo-lookup.log"

class leolookup:
    """Represents the program, with the window."""
    version = "0.01"

    # searchLoc
    # -1        Englisch to German 
    #  0        Automatic
    #  1        German to Englisch
    url = "http://dict.leo.org/ende"
    supportedfromLangs = [ "German", "English" ]
    supportedtoLangs = [ "German", "English" ]

    def __init__(self):
        logger = logging.getLogger('INIT')
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_size_request(430,420)
        self.window.set_title("leo-lookup Version " + self.version)
        self.window.connect("destroy", self.destroyWin)

        self.box = gtk.VBox(False, 4)
        
        self.word2lookup = gtk.Entry()
        self.word2lookup.set_text("Enter word to lookup here ...")
        self.box.pack_start(self.word2lookup, False, False, 0)

        self.box2 = gtk.HBox(False, 6)
        

        # Create combo box for the language to translate from
        self.fromLangLabel = gtk.Label("From ")
        self.box2.pack_start(self.fromLangLabel, False, False, 0)
        self.fromLang = gtk.combo_box_new_text()
        for lang in self.supportedfromLangs:
            self.fromLang.append_text(lang)
        self.fromLang.set_active(0)
        self.box2.pack_start(self.fromLang, False, False, 0)

        self.swapToFrom = gtk.Button("<>")
        self.swapToFrom.connect("clicked", self.swapToFromClicked)
        self.box2.pack_start(self.swapToFrom, False, False, 0)

        # Create combo box for the language to translate to
        self.toLangLabel = gtk.Label("to ")
        self.box2.pack_start(self.toLangLabel, False, False, 0)
        self.toLang = gtk.combo_box_new_text()
        for lang in self.supportedtoLangs:
            self.toLang.append_text(lang)
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
        self.cell = gtk.CellRendererText()
        self.listOfMeaningsCol.pack_start(self.cell, True)
        self.listOfMeaningsCol.add_attribute(self.cell, 'text', 0)
        
        self.listOfMeaningsCol2 = gtk.TreeViewColumn("Familiar Lang.")
        self.listOfMeanings.append_column(self.listOfMeaningsCol2)
        cell2 = gtk.CellRendererText()
        self.listOfMeaningsCol2.pack_start(cell2, True)
        self.listOfMeaningsCol2.add_attribute(cell2, 'text', 1)


        self.scrollcont.add(self.listOfMeanings)
        self.box.pack_start(self.scrollcont, True, True, 0)

        self.window.add(self.box)
        logger.info("window constructed, let's make it visible ...")
        self.window.show_all()
        gtk.main()
        
    
    def swapToFromClicked(self, *args):
        """Will be executed if the user clicks on the swap button between the to combo boxes"""
        temp = self.fromLang.get_active()
        self.fromLang.set_active(self.toLang.get_active())
        self.toLang.set_active(temp)

    def onTransClick(self, *args):
        """Will be executed if the user clicks on the "Translate"-button"""

        # initialize the logger
        logger = logging.getLogger('onTransClick')
        logger.setLevel(logging.DEBUG)

        # check and define the search direction
        lang1 = self.fromLang.get_active_text()
        lang2 = self.toLang.get_active_text()
        if lang1 == "English" and lang2 == "German":
            searchLoc = -1
        elif lang1 == "German" and lang2 == "English":
            searchLoc = 1
        else:
            searchLoc = 0

        # define arguments to be committed to the webserver, like
        # the word, we are looking up.
        args = {"relink" :"off", 
                "search" : self.word2lookup.get_text(), 
                "searchLoc" : searchLoc}

        data = urllib.urlencode(args)
        # do communication with the webserver
        request = urllib2.Request(self.url, data)
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
        # print ipof
        # print "IoUT: %s\teoIT: %s\tsoIT: %s\t" % (IoUT, eoIT, soIT)
        # xml_data = "<?xml version=\"1.0\"?>" + self.getTagsWoAttr(ipof)
        # print xml_data
        # dom1 = parseString(xml_data)
        myhtmlparser = llresultextractor2.ResultExtractor()
        myhtmlparser.feed(ipof)
        myhtmlparser.close()
        results = myhtmlparser.getResults()
        self.meanings.clear()
        logger.debug(results)
        successes = results.pop()
        logger.debug("successes: %s" % (successes))
        if successes == 0:
            self.results.set_text("No results ")
        else:
            self.results.set_text("%s results " % (successes))

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




if __name__ == "__main__":
    LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

    if len(sys.argv) > 1:
        level_name = sys.argv[1]
        level = LEVELS.get(level_name, logging.NOTSET)
        logging.basicConfig(filename=LOGFILENAME,level=level)
    else:
        logging.basicConfig(filename=LOGFILENAME, level=logging.INFO)
    curDateTime = datetime.datetime.isoformat(datetime.datetime.now())
    logging.info("\nlogging facility started on %s\t" % (curDateTime))
    logging.info("------------------------------")

    app =  leolookup()
