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


import os
import sys
import datetime
import zipfile
import xml.dom.minidom
import xml.dom.minicompat

class jmemorize_files:
    """
    This plugin provides access on flashcard-files used and created by
    jMemorize Version 1.3.0.
    """
    filename = ""
    words2add = []
    def __init__(self):
        pass

    def getSupportedExtensions(self):
        """
        Returns supported file extensions with description.
        """
        return [("JMemorize Flashcard-Files (zipped)", "jml")
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
        
    def addWord(self, foreside, backside):
        """
        Adds words to the list of words to add.
        """
        self.words2add.append((foreside, backside))
    
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
        except BadZipFile:
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
            return -4
        finally:
            dom.unlink()

        return words
    
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
        # TODO: manage time stamp
        aktuell = datetime.datetime.now()
        time = aktuell.time().strftime("%H:%M:%S")
        date = aktuell.date().strftime("%d-%b-%Y")
        timestamp = date + " " + time
        defaultCategory = "Alle"
        cards2add = []
        # convert word-pairs to jmemorize xml-flashcards 
        for word2add in self.words2add:
            xml_data4card = """<Card AmountLearnedBack="0" AmountLearnedFront="0" Backside="%s" DateCreated="%s" DateModified="%s" DateTouched="%s" Frontside="%s" TestsHit="0" TestsTotal="0"><Side/><Side/></Card>""" % (word2add[0], timestamp, timestamp, timestamp, word2add[1])
            cards2add.append(xml.dom.minidom.parseString(xml_data4card))
        
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
            dom = xml.dom.minidom.parseString(lesson_xml)
            lesson_nd  = dom.getElementsByTagName(xmlpath[0])[0]
            categories = lesson_nd.getElementsByTagName(xmlpath[1])
            for category in categories:
                attrib = category.attributes["name"].firstChild
                if attrib.wholeText == defaultCategory:
                    deck = category.getElementsByTagName(xmlpath[2])[0]
                    olddeck = deck
                    for card2add in cards2add:
                        deck.appendChild(card2add.firstChild)
                        #print "adding card: %s" % (card2add.firstChild.toxml())
                    dom.replaceChild(deck, olddeck)
                    break
            new_jml = zipfile.ZipFile(os.curdir+os.sep+self.seperateFilenameAndPath()["filename"], mode="w", compression=zipfile.ZIP_DEFLATED)
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
        
        jmf = jmemorize_files()
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
