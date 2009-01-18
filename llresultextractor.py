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

import htmllib

class ResultExtractor (htmllib.HTMLParser):
    """Extracts the results gotten from dict.leo.org/ende."""
    def __init__(self, formatter):
        htmllib.HTMLParser.__init__(self, formatter)
        self.results = []
        self.inside_td = False
        self.toLang1 = True
        self.unmittelb_Treffer = False
        self.notNext = False

    def start_td(self, attrs):
        """If a opening td-tag is recognized, this method will be called."""    
        self.inside_td = True

    def end_td(self):
        """If a closing td-tag is recognized, this method will be called."""
        self.inside_td = False

    def handle_data(self, text):
        """Extracts data betrween td-tags."""
        text = text.strip()
        if "Verben und Verbzusammensetzungen" in text:
            self.unmittelb_Treffer = False

        if self.inside_td and self.unmittelb_Treffer:
            #print text
            if text == '\xa0' or text == 'i' or text == '':
                return
            if self.toLang1:
                if text[0] == "[":
                    # Eckige Klammer in Element 0
                    self.results[len(self.results)-2][1] = self.results[len(self.results)-2][1] + ' ' + text
                    print "DEBUG: %s\tPosition:%d" % (text, text.find("["))
                elif "Pl.:" in text:
                    self.notNext = True
                    
                    pass
                else:
                    self.results.append([text])
                    self.toLang1 = False

            elif not self.toLang1:
                if text[0] == "[":
                    # Eckige Klammer in Element 1
                    self.results[len(self.results)-1][0] = self.results[len(self.results)-1][0] + ' ' + text
                    pass
                else:
                    self.results[len(self.results)-1].append(text)
                    self.toLang1 = True
        else:
            if "Unmittelbare Treffer" in text:
                self.unmittelb_Treffer = True

    def getResults(self):
        """Returns the parsed results as a list."""
        return self.results

                
        
        
if __name__ == "__main__":
    import formatter
    import sys
    if len(sys.argv) <  2:
        print "ResultExtractor: Please specify a html-file to parse.\n"
        sys.exit()
    
    inst = ResultExtractor(formatter.AbstractFormatter(formatter.NullWriter()))
    file = open(sys.argv[1], "r")
    inst.feed(file.read())
    file.close()
    inst.close()
    print inst.getResults()
    
    pass
