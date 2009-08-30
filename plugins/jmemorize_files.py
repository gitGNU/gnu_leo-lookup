# /usr/bin/python
# -*- encoding: utf-8 -*- 
#
# This file is part of leo-lookup.
#
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
# Copyright (C) 2009 Markus Zeindl <mrszndl@googlemail.com>

# TODO: Line 587

import os
import sys
import datetime
import zipfile
import xml.dom.minidom
import xml.dom.minicompat
import logging

import gtk
import gobject

def __init__(uiman, treeselection):
    """
    Initialize the module.
    """
    jmf = jmemorize_files(uiman, treeselection)


class jmemorize_files:
    """
    This plugin provides access on flashcard-files used and created by
    jMemorize Version 1.3.0.
    """
    filename = ""
    words2add = []
    category = ""

    # Define structure of menu entries, added by this plugin
    new_mnuitems = """
<ui>
  <menubar name="Mainmenu">
    <menu action="Extensions">
      <menu action="jMemorize">
	<menuitem name="open" action="openfile"/>
	<menuitem name="close" action="closefile"/>
	<menuitem name="add" action="addWord"/>
      </menu>
    </menu>
  </menubar>
</ui>
"""


    def __init__(self, uimanager, treeselection):
        self.treeselection = treeselection
        logger = logging.getLogger("jmemorize_files.py:INIT")
        self.menubar_acts = [
            ('Extensions', None, "_Extensions"),
            
            ('jMemorize', None, "_jMemorize"),

            ('openfile', None, "Open flashcard-file ...", None,
             "Opens a flashcard file for adding words", self.openFileDlg),

            ('closefile', None, "Close flashcard-file ...", None,
             "Closes an open flashcard file.", self.closeFileDlg),

            ('addWord', None, "Add selection to flashcard-file ...", None,
             "Adds selection as a word under a specified category.", self.addWordDlg)
            ]

        self.actgroup = gtk.ActionGroup("LL_JMEMORIZE")
        self.actgroup.add_actions(self.menubar_acts)
        uimanager.insert_action_group(self.actgroup, 1)
        uimanager.add_ui_from_string(self.new_mnuitems)
        uimanager.ensure_update()
        logger.info("jMemorize support is initialized.")

    def getSupportedExtensions(self):
        """
        Returns supported file extensions including description.
        """
        return [
                ("JMemorize Flashcard-Files (zipped)", "jml"),
                ("JMemorize Flashcard-Files",          "xml")
               ]

    def setTargetFile(self, file):
        if self.checkFile(file) == 0:
            self.filename = file
            return True
        else:
            return False

    def checkFile(self, file):
        # First, check if file exists
        # Second, try to unzip file
        # Third, search after signature
        
        # check if file exists
        try:
            os.stat(file)
        except OSError:
            return -1
        
        # check if file is a zip file and get list of contained files
        try:
            zf = zipfile.ZipFile(file, mode="r")
            nl = zf.namelist()
            zf.close()
        except BadZipFile:
            return -2

        # check if structure is ok
        if not len(nl) == 1 or not nl[0] == "lesson.xml":
            return -3
        
            
        # if all tests succeeded, return zero
        return 0
        
    def addWord(self, foreside, backside, category=""):
        """
        Adds a word to the list of words to add.
        """
        self.words2add.append((backside, foreside, category))
    
    def listWords(self):
        """
        Return a list of words, which are already stored in the
        given file. TODO: Consider using ElementTree API, seems to be simpler
        and more effective.
        """
        xmlpath = ["Lesson", "Category", "Deck", "Card" ]
        words = []
        dom = xml.dom.minidom.Document()
        lesson_xml = ""
        try:
            # open jml (zip) file
            zf = zipfile.ZipFile(self.filename, mode="r")
            # extract "lesson.xml", containing interesting infos
            lesson_xml = zf.read(zf.namelist()[0])
            zf.close()
        except zipfile.BadZipFile:
            return -2
        
        try:
            dom = xml.dom.minidom.parseString(lesson_xml)
            
            nd = dom.getElementsByTagName(xmlpath[0])[0]
            categories = nd.getElementsByTagName(xmlpath[1])
            for category in categories:
                deck = category.getElementsByTagName(xmlpath[2])[0]
                cards = deck.getElementsByTagName(xmlpath[3])
                for card in cards:
                    attrib_t =  card.attributes["Backside"].firstChild
                    bs = attrib_t.wholeText
                    attrib_t.unlink()
                    attrib_t = card.attributes["Frontside"].firstChild
                    fs = attrib_t.wholeText
                    attrib_t.unlink()
                    words.append((fs,bs))
        except Exception:
            print words
            dom.unlink()
            return -4
        finally:
            dom.unlink()

        return words

    def getCategories(self):
        """
        Return a list of existing categories, which are already stored in the
        given file. TODO: Consider using ElementTree API, seems to be simpler
        and more effective.
        """
        xmlpath = ["Lesson", "Category" ]
        category_names = []
        dom = xml.dom.minidom.Document()
        lesson_xml = ""
        try:
            # open jml (zip) file
            zf = zipfile.ZipFile(self.filename, mode="r")
            # extract "lesson.xml", containing interesting data
            lesson_xml = zf.read(zf.namelist()[0])
            zf.close()
        except BadZipFile:
            return -2
        
        try:
            dom = xml.dom.minidom.parseString(lesson_xml)
            
            nd = dom.getElementsByTagName(xmlpath[0])[0]
            categories = nd.getElementsByTagName(xmlpath[1])
            for category in categories:
                attrib = category.attributes["name"].firstChild
                category_names.append(attrib.wholeText)
                attrib.unlink()
        except Exception:
            print category_names
            return -4
        finally:
            dom.unlink()

        return category_names
    
    def flush(self):
        """
        Writes words to target file and clears buffer variables.
        At first, it will extract the lesson.xml from the given jml-file.
        Secondly, it adds the words to the buffered lesson.xml-data and 
        writes this to a new lesson.xml-file.
        After that, the given filename will be removed and the lesson.xml-file
        will be compressed and renamed to the given filename.
        Note: The cards will be added to the category "Alle"
        """
        # construct needed data
        # TODO: manage time stamp,
        #       custom category support

        logger = logging.getLogger("jmemorize_files.py:flush")

        aktuell = datetime.datetime.now()
        time = aktuell.time().strftime("%H:%M:%S")
        date = aktuell.date().strftime("%d-%b-%Y")
        timestamp = date + " " + time
        
        # set target category
#        if 
        defaultCategory = "Alle"
        cards2add = []
        # convert word-pairs to jmemorize xml-flashcards 
        for word2add in self.words2add:
            logger.debug("attempt to add '%s'" % (str(word2add)))
            xml_data4card = """<Card AmountLearnedBack="0" AmountLearnedFront="0" Backside="%s" DateCreated="%s" DateModified="%s" DateTouched="%s" Frontside="%s" TestsHit="0" TestsTotal="0"><Side/><Side/></Card>""" % (word2add[0], timestamp, timestamp, timestamp, word2add[1])
            cards2add.append((xml.dom.minidom.parseString(xml_data4card),
                              word2add[2]))
        
        # do the first step: extract file lesson.xml
        try:
            zf = zipfile.ZipFile(self.filename, mode="r")
            lesson_xml = zf.read(zf.namelist()[0])
            zf.close()
        except BadZipFile:
            return -1
        
        # do the second step: change xml-data (add Card-tags)
        xmlpath = ["Lesson", "Category", "Deck" ]
        try:
            # parse xml-file
            dom = xml.dom.minidom.parseString(lesson_xml)
            lesson_nd  = dom.getElementsByTagName(xmlpath[0])[0]
            categories = lesson_nd.getElementsByTagName(xmlpath[1])
            for card2add in cards2add:
                for category in categories:
                    # look for category with the name of defaultCategory
                    attrib = category.attributes["name"].firstChild
                    if attrib.wholeText == card2add[1]:
                        deck = category.getElementsByTagName(xmlpath[2])[0]
                        olddeck = deck
                        # add words to deck
                        deck.appendChild(card2add[0].firstChild)
                        #print "adding card: %s" % (card2add.firstChild.toxml())
                        # replace old deck instance with the new.
                        dom.replaceChild(deck, olddeck)
                        break

            # delete old zip file
            os.remove(self.filename)

            # create Zip-File and write the xml-file
            new_jml = zipfile.ZipFile(self.filename, mode="w", compression=zipfile.ZIP_DEFLATED)
            new_jml.writestr("lesson.xml", dom.toxml().encode("UTF-8"))
            new_jml.close()
        except Exception:
            return -1

        
        return 0
    
    def closeFile(self):
        """
        It closes the target file and resets filename. Before it
        closes the file, self.flush() will be called, to write data 
        which has to be written to the file.
        """
        self.flush()
        self.filename = ""
        
        pass
    def seperateFilenameAndPath(self):
        """
        Splits a given path to a file (including filename) to
        filename and path. It returns a directory with keys "path" and 
        "filename"
        """
        index = self.filename.rfind(os.sep)
        return { "path": self.filename[:index+1], 
                 "filename": self.filename[index+1:] }

    def openFileDlg(self, *args):
        supportedFiles = self.getSupportedExtensions()
        opendlg = gtk.FileChooserDialog(title="Open Flashcard-File",
                                        action=gtk.FILE_CHOOSER_ACTION_OPEN,
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_OPEN, gtk.RESPONSE_OK))

        for type in supportedFiles:
            filefilter = gtk.FileFilter()
            filefilter.set_name(type[0])
            filefilter.add_pattern("*." + type[1])
            opendlg.add_filter(filefilter)

        filefilter = gtk.FileFilter()
        filefilter.set_name("All files")
        filefilter.add_pattern("*")
        opendlg.add_filter(filefilter)
        
        resp = opendlg.run()
        if resp == gtk.RESPONSE_OK:
            self.filename = opendlg.get_filename()
        opendlg.destroy()
        

    def closeFileDlg(self, *args):
        self.closeFile()
        pass
    
    def addWordDlg(self, *args):
        """
        Will be executed if the user clicks on the menu-element "Add selection" in Extensions.
        """
        
        # Initialize logging facility for this method
        logger = logging.getLogger("jmemorize_files.py:addWordDlg")

        # List for selected words 
        # (content: tuples with foreign and native side)
        selectedwords = []
        

        (model, pathlist) = self.treeselection.get_selected_rows()
        logger.debug("Printing selection:")
        for selentry in pathlist:
            iter = model.get_iter(selentry)
            f_word = model.get_value(iter, 0)
            n_word = model.get_value(iter, 1)
            logger.debug("Foreign: %s\tNative: %s" % (f_word, n_word))
            selectedwords.append((f_word, n_word))
                
       
        # Category?

        # get amount of words selected
        self.amountOfSelWords = len(selectedwords)
        if self.amountOfSelWords == 0:
            message = """You haven't selected anything.
Please select words you wish to add."""

            msgdlg = gtk.MessageDialog(buttons=gtk.BUTTONS_OK, 
                                       message_format=message)
                                       
            msgdlg.run()
            msgdlg.destroy()
            return
        
        # Create dialog
        aw_dialog = gtk.Dialog(title = "Add selection to flashcard-file...",
                               buttons = ("_Add %s words" % self.amountOfSelWords, 
                                          gtk.RESPONSE_OK,
                                        "Cancel", gtk.RESPONSE_CANCEL))
        logger.debug("Children of aw_dialog.action_area: %s" % (aw_dialog.action_area.get_children()))
        aw_dialog.set_size_request(780, 500)

        self.chkb_joinwords = gtk.CheckButton(label = "_Join expressions to one word")
        self.chkb_joinwords.connect("toggled", self.joinwords_cb, aw_dialog.action_area.get_children()[1])

        self.chkb_joinwords.show()
        aw_dialog.vbox.pack_start(self.chkb_joinwords, False, False, 0)
        
        # Create a horizontal widget container with two elements
        hbox = gtk.HBox(2)

        # Create widgets for foreign words
        # At first prepare the table for foreign words
        add_fw_lst_store = gtk.ListStore(gobject.TYPE_BOOLEAN, 
                                         gobject.TYPE_STRING)
        
        # Add foreign words and make them checked by default
        checked = True
        for sel_word in selectedwords:
                add_fw_lst_store.append((checked, sel_word[0]))
                checked = False
                
        
        # create list-widget
        self.add_fw_tree_view = gtk.TreeView(add_fw_lst_store)

        # Prepare first column, which controls, which words
        # should be joined
        cellrend_toggle_fw = gtk.CellRendererToggle()
        cellrend_toggle_fw.set_property("activatable", True)
        cellrend_toggle_fw.connect('toggled', 
                                     self.adddlg_toggled_callback,
                                     add_fw_lst_store,
                                     0)        

        add_fw_tvcol0 = gtk.TreeViewColumn('included?',
                                           cellrend_toggle_fw,
                                           active=0)
       
        # enable the user to sort using this column
        add_fw_tvcol0.set_sort_column_id(0)

        # Prepare second column, which displays words only
        cellrend_text = gtk.CellRendererText()
        add_fw_tvcol1 = gtk.TreeViewColumn('Word', 
                                           cellrend_text, 
                                           text=1 )

        # enable the user to sort using this column
        add_fw_tvcol1.set_sort_column_id(1)

        self.add_fw_tree_view.append_column(add_fw_tvcol0)
        self.add_fw_tree_view.append_column(add_fw_tvcol1)        

        self.add_fw_tree_view.set_size_request(235, 350)
        self.add_fw_tree_view.show()

        # Make the table scrollable
        scrollwind_fw = gtk.ScrolledWindow()
        scrollwind_fw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        scrollwind_fw.add(self.add_fw_tree_view)
        scrollwind_fw.show()

        frm_foreign_side = gtk.Frame(label="Foreign words")
        frm_foreign_side.add(scrollwind_fw)
        frm_foreign_side.show()


        # Pack tree view in hbox
        hbox.pack_start(frm_foreign_side, True, True, 5)


        # Create widgets for native words
        # At first prepare the data-table for native words
        add_nw_lst_store = gtk.ListStore(gobject.TYPE_BOOLEAN, 
                                         gobject.TYPE_STRING)
        
        # Add native words and make them checked by default
        for sel_word in selectedwords:
            add_nw_lst_store.append((True, sel_word[1]))
        
        # create list-widget
        self.add_nw_tree_view = gtk.TreeView(add_nw_lst_store)

        # Prepare first column, which controls, which words
        # should be joined
        cellrend_toggle_nw = gtk.CellRendererToggle()
        cellrend_toggle_nw.set_property("activatable", True)
        cellrend_toggle_nw.connect('toggled', 
                                self.adddlg_toggled_callback,
                                add_nw_lst_store,
                                0)        

        add_nw_tvcol0 = gtk.TreeViewColumn('included?',
                                           cellrend_toggle_nw,
                                           active=0)
       
        # enable the user to sort using this column
        add_nw_tvcol0.set_sort_column_id(0)

        # Prepare second column, which displays words only
#        cellrend_text = gtk.CellRendererText()
        add_nw_tvcol1 = gtk.TreeViewColumn('Word', 
                                           cellrend_text, 
                                           text=1 )

        # enable the user to sort using this column
        add_nw_tvcol1.set_sort_column_id(1)

        self.add_nw_tree_view.append_column(add_nw_tvcol0)
        self.add_nw_tree_view.append_column(add_nw_tvcol1)        

        self.add_nw_tree_view.set_size_request(235, 350)
        self.add_nw_tree_view.show()

        # Make the table scrollable
        scrollwind_nw = gtk.ScrolledWindow()
        scrollwind_nw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        scrollwind_nw.add(self.add_nw_tree_view)
        scrollwind_nw.show()

        frm_native_side = gtk.Frame(label="Native words")
        frm_native_side.add(scrollwind_nw)
        frm_native_side.show()


        hbox.pack_start(frm_native_side, True, True, 5)
        hbox.show()


        aw_dialog.vbox.pack_start(hbox, True, True, 5)


        # Create and display widgets for choosing the target category
        cat_hbox = gtk.HBox(2)

        label_cat = gtk.Label("Category:")
        cat_hbox.pack_start(label_cat, False, False, 0)

        # since a list-store is needed for the combobox, create it and
        # fill it with needed data
        mdl_categories = gtk.ListStore(str)
        for category in self.getCategories():
            mdl_categories.append([category])
        
        cb_category = gtk.ComboBox(mdl_categories)
        cb_category.pack_start(cellrend_text, True)
        cb_category.add_attribute(cellrend_text, 'text', 0)
        cb_category.set_active(0)
        cat_hbox.pack_start(cb_category, False, False, 0)
        cat_hbox.show_all()
        aw_dialog.vbox.pack_start(cat_hbox, False, False, 0)
        
        # Create and display Checkbox "Check for duplicates"
        chkb_duplicates = gtk.CheckButton(label = "_Check for duplicates")
        chkb_duplicates.set_active(True)
        chkb_duplicates.show()
        aw_dialog.vbox.pack_start(chkb_duplicates, False, False, 0)
        
        
        # call callback to disable widgets for joining words
        self.chkb_joinwords.emit("toggled")

        # Show dialog
        resp = aw_dialog.run()

        if resp == gtk.RESPONSE_OK:
            # examine target category
            target_catiter = cb_category.get_active_iter()
            target_category = mdl_categories[mdl_categories.get_path(target_catiter)][0]

            # should selection be joined?
            if self.chkb_joinwords.get_active():
                # define word lists containing words to join
                foreign = []
                foreign_j = ""
                native = []
                native_j = ""

                # iterate over data model (list store oject) 
                # of foreign words, check demand and add it to foreign
                for lst_entry in add_fw_lst_store:
                    ent_values = list(lst_entry)
                    if ent_values[0]:
                        foreign.append(ent_values[1]+ ", ")
                logger.info("Foreign words to be joined: %s\n" % (str(foreign)))

                # do the same thing for native words too
                for lst_entry in add_nw_lst_store:
                    ent_values = list(lst_entry)
                    if ent_values[0]:
                        native.append(ent_values[1] + ", ")
                logger.info("Native words to be joined: %s\n" % (str(native)))
                # join the prepared words now and cut last comma out
                foreign_j = "".join(foreign)
                foreign_j = foreign_j[:len(foreign_j)-2]
                native_j = "".join(native)
                native_j = native_j[:len(native_j)-2]             
                logger.info("Wordentry to be added:\n%s\n%s" % (foreign_j,
                                                                native_j))

                # process "check for duplicates"
                # TODO: Implement "Check for duplicates feature" for
                #       adding more words
                if chkb_duplicates.get_active():              
                    if self.producesDuplicates((foreign_j, native_j)):
                        message = "If you proceed, you will produce duplicate words in flashcard file.\nDo you really want to continue?"

                        msgdlg = gtk.MessageDialog(parent = None, 
                                                   message_format = message,
                                                   buttons = gtk.BUTTONS_YES_NO,
                                                   type = gtk.MESSAGE_QUESTION)
                        ret_val = msgdlg.run()
                        if ret_val == gtk.RESPONSE_YES:
                            # finally add the joined words
                            self.addWord(foreign_j, native_j, target_category)
                else:
                    # if there are no duplicates proceed adding the word
                    self.addWord(foreign_j, native_j, target_category)

            else:
                for s_word in selectedwords:
                    if chkb_duplicates.get_active():              
                        if self.producesDuplicates((s_word[0], s_word[1])):
                            message = "If you proceed, you will produce duplicate words in flashcard file.\nDo you really want to continue?"
                            
                            msgdlg = gtk.MessageDialog(parent = None, 
                                                       message_format = message,
                                                       buttons = gtk.BUTTONS_YES_NO,
                                                       type = gtk.MESSAGE_QUESTION)
                            ret_val = msgdlg.run()
                            if ret_val == gtk.RESPONSE_YES:
                                # finally add the joined words
                                self.addWord(s_word[0], s_word[1], target_category)
                        else:
                            # if there are no duplicates proceed adding the word
                            self.addWord(s_word[0], s_word[1], target_category)

        aw_dialog.destroy()
        return
    

    def adddlg_toggled_callback(self,cell, path, model=None, col_num=0):
        logger = logging.getLogger("jmemorize_files.py:adddlg_toogled_callback") 
        iter = model.get_iter(path)
        logger.debug("---------------------------------")
        logger.debug("adddlg_toggled_callback data:")
        logger.debug("cell: %s\t%s\npath: %s\t%s\nmodel: %s\t%s\ncol_num: %s\t%s" % (cell, type(cell), path, type(path), model, type(model), col_num, type(col_num)))

        oldvalue = model.get(iter, col_num)[0]
        logger.debug("changing from %s to %s" % (oldvalue, not oldvalue))
        model.set_value(iter, col_num, not oldvalue)
        logger.info("word toggled")
        return

    def joinwords_cb(self, checkbutton, button):
        if self.chkb_joinwords.get_active():
            button.set_label("Add word")
            self.add_fw_tree_view.set_sensitive(True)
            self.add_nw_tree_view.set_sensitive(True)
        else:
            button.set_label("Add %s words" % (self.amountOfSelWords))
            self.add_nw_tree_view.set_sensitive(False)
            self.add_fw_tree_view.set_sensitive(False)


        return
    def producesDuplicates(self, word2add):
        """
        Checks if the attempt to add the given word would produce duplicate
        saved word in the target falshcard-file.
        """
        duplicate_words = []
        # get words already saved in flashcard file and
        # compare every value of them with the word, the user
        # wants to add
        exist_words = self.listWords()
        for exist_word in exist_words:
            if word2add[0] == exist_word[0] or word2add[1] == exist_word[1]:
               duplicate_words.append((exist_word[0], exist_word[1]))
        if len(duplicate_words) > 0:
            return True
        else:
            return False
    
        


if __name__ == "__main__":
# $ jmemorize_files.py [cmd] [file.jml]
# cmd could be --add fs,bs 
#              --list-contents
    import getopt 
    if len(sys.argv) > 1:
        sOpts = [ "add=", "list-contents" ]
        w2a = ()
        operation = ""
        # parse commandline 
        (opts, args) = getopt.getopt(sys.argv[1:], "", sOpts)
        if opts[0][0][2:] == sOpts[0][:3]:
            # first commandline argument is add, now extract values
            print "Attempting to add %s" % (opts[0][1])
            v = opts[0][1].split(",")
            operation = "add"
            w2a = (v[0], v[1])
        elif opts[0][0][2:] == sOpts[1]:
            # first commandline argument is list-contents
            operation = "list"
        
        # check if args[0] contains really a file name
        if args[0].endswith(".jml"):
            fn = args[0]
        
        jmf = jmemorize_files(None, None)
        if jmf.setTargetFile(fn):
            print "- File %s seems to be ok." % (fn)

        if operation == "list":
            print "\nThe following words are stored:"
            for card in jmf.listWords():
                print "  Foreside: %s\tBackside: %s" % (card[0], card[1])
        elif operation == "add":
            jmf.addWord(w2a[0], w2a[1])
        jmf.closeFile()
    pass




if __name__ != "__main__":
    pass
