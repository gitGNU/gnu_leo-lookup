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

import logging

class ResultExtractor():
    """Extracts the results gotten from dict.leo.org./ende"""
    def __init__(self):
        self.results = []
        self.closed = False
        self.successes = ""
        pass

    def feed(self, data):
        if not self.closed:
            self.input = data
    
    def close(self):
        """Process the given data and get results."""
        logger = logging.getLogger('llresultextractor2.close')
        self.closed = True
        ignoreCount = 4
    
        # index of cell in the current row, only element nr. 1 and nr. 3 are useful 
        cellind = 0
        pos1 = 0
        pos2 = 0
        result = ""
        pair = []
        successesFound = False
        end_trpos = 0
        logging.debug("Input data:\n%s" % (self.input))
        # Skip useless header
        while(True):
            pos1 = self.input.find("<td", pos2)
            pos2 = self.input.find("</td>", pos1)
            if pos1 == -1 or pos2 == -1:
                break;
            if ignoreCount > 0:
                ignoreCount = ignoreCount - 1
                result = self.input[pos1:pos2]
                if 'Treffer' in result and not successesFound:
                    result = self.removeTags(result)
                    self.successes = result.strip().split(" ")[0]
                    logger.debug("result = '%s'\tself.successes = '%s'" %(result, self.successes))
                    successesFound = True
            else:
                break;
        
        
        while(True):
            pos1 = self.input.find("<td", pos2)
            pos2 = self.input.find("</td>", pos1)
            end_trpos = self.input.find("</tr>", pos1)
            if pos1 == -1 or pos2 == -1:
                break;
            if cellind == 4:
                cellind = 0
            else:
                cellind = cellind + 1
            
            if end_trpos > pos2:
                result = self.input[pos1:pos2]            
            elif end_trpos < pos2:
                result = self.input[pos1:end_trpos]
                logger.debug("result = '%s'\t'end_trpos = '%d'" % (result, end_trpos))
                pos2 = end_trpos
                #end_trpos = self.input.find("</tr>", end_trpos+1)

            if 'class="center"' in result or 'mehr &gt;&gt;' in result:
                result = self.removeTags(result)
                logger.debug("result = %s" % (result))
                #break;
                cellind = -1
                continue;
            if cellind == 1 or cellind == 3: 

                logger.debug("idx = %d result = %s" % (cellind,result))
                result = self.removeTags(result)
                result = result.replace("&#160;", " ")
                pair.append(result)
                if len(pair) == 2:
                    logger.debug(" pair = %s" % (pair))
                    self.results.append(pair)
                    pair = []
                isUseful = False
    def removeTags(self, data):
        """Removes html-tags from the given string and returns it."""
        # <td width="43%"><b>bla</b></td>
        logger = logging.getLogger('llresultextractor2.removeTags')
        pos1 = 0
        pos2 = 0
        while(True):
            pos1 = data.find("<")
            pos2 = data.find(">", pos1)
            if pos1 == -1 or pos2 == -1:
                break;
            data = data.replace(data[pos1:pos2+1],"",1)
            logger.debug("data = %s" % (data))
        return data
    
    def getResults(self):
        logger = logging.getLogger('llresultextractor2.getResults')
        self.results.append(self.successes)
        return self.results
        pass

         
if __name__ == "__main__":
    import formatter
    import sys
    import logging
    if len(sys.argv) <  2:
        print "ResultExtractor2: Please specify a html-file to parse.\n"
        sys.exit()
    logging.basicConfig(level=logging.debug)
    
    inst = ResultExtractor()
    file = open(sys.argv[1], "r")
    inst.feed(file.read())
    file.close()
    inst.close()
    print inst.getResults()
    
    pass

    
 
