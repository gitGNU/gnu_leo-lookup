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

class ResultExtractor():
    """Extracts the results gotten from dict.leo.org./ende"""
    def __init__(self):
        self.results = []
        self.closed = False
        pass

    def feed(self, data):
        if not self.closed:
            self.input = data
    
    def close(self):
        """Process the given data and get results."""
        self.closed = True
        ignoreCount = 9
    
        # index of cell in the current row, only element nr. 1 and nr. 3 are useful 
        cellind = 0
        pos1 = 0
        pos2 = 0
        result = ""
        pair = []
        
        # Skip useless header
        while(True):
            pos1 = self.input.find("<td", pos2)
            pos2 = self.input.find("</td>", pos1)
            if pos1 == -1 or pos2 == -1:
                break;
            if ignoreCount > 0:
                ignoreCount = ignoreCount - 1
            else:
                break;

        while(True):
            pos1 = self.input.find("<td", pos2)
            pos2 = self.input.find("</td>", pos1)
            if pos1 == -1 or pos2 == -1:
                break;
            if cellind == 4:
                cellind = 0
            else:
                cellind = cellind + 1
            result = self.input[pos1:pos2]            
            if "Verben und Verbzusammensetzungen" in result:
                break;
            if cellind == 1 or cellind == 3: 

                print "[DEBUG]idx = %d result = %s" % (cellind,result)
                pair.append(self.removeTags(result))
                if len(pair) == 2:
                    print "[DEBUG]: pair = %s" % (pair)
                    self.results.append(pair)
                    pair = []
                isUseful = False
    def removeTags(self, data):
        """Removes html-tags from the given string and returns it."""
        # <td width="43%"><b>bla</b></td>
        pos1 = 0
        pos2 = 0
        while(True):
            pos1 = data.find("<")
            pos2 = data.find(">", pos1)
            if pos1 == -1 or pos2 == -1:
                break;
            data = data.replace(data[pos1:pos2+1],"",1)
            print "[DEBUG]: data = %s" % (data)
        return data
    
    def getResults(self):
        return self.results
        pass
         
if __name__ == "__main__":
    import formatter
    import sys
    if len(sys.argv) <  2:
        print "ResultExtractor2: Please specify a html-file to parse.\n"
        sys.exit()
    
    inst = ResultExtractor()
    file = open(sys.argv[1], "r")
    inst.feed(file.read())
    file.close()
    inst.close()
    print inst.getResults()
    
    pass
 
