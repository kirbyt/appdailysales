#!/usr/bin/python
#
# appdailysales.py
#
# iTune Connect Daily Sales Reports Downloader
# Copyright 2008 Kirby Turner
#
# Version 1.8
#
# Latest version and additional information available at:
#   http://appdailysales.googlecode.com/
#
#
# This script will download yesterday's daily sales report from
# the iTunes Connect web site.  The downloaded file is stored
# in the same directory containing the script file.  Note: if
# the download file already exists then it will be overwritten.
#
# The iTunes Connect web site has dynamic urls and form field
# names.  In other words, these values change from session to
# session.  So to get to the download file we must navigate  
# the site and webscrape the pages.  Joy, joy.
#
#
# Contributors:
#   Leon Ho
#   Rogue Amoeba Software, LLC
#   Keith Simmons
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


# -- Change the following to match your credentials --
# -- or use the command line options.               --
appleId = 'Your Apple Id'
password = 'Your Password'
outputDirectory = ''
unzipFile = False
verbose = False
daysToDownload = 1
dateToDownload = None
# ----------------------------------------------------


import urllib
import urllib2
import cookielib
import datetime
import re
import getopt
import sys
import os
import gzip
import StringIO
import traceback

try:
    import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# The class ReportOptions defines a structure for passing
# report options to the download routine. The expected
# data attributes are:
#   appleId
#   password
#   outputDirectory
#   unzipFile
#   verbose
#   daysToDownload
# Note that the class attributes will default to the global
# variable value equivalent.
class ReportOptions:
    def __getattr__(self, attrname):
        if attrname == 'appleId':
            return appleId
        elif attrname == 'password':
            return password
        elif attrname == 'outputDirectory':
            return outputDirectory
        elif attrname == 'unzipFile':
            return unzipFile
        elif attrname == 'verbose':
            return verbose
        elif attrname == 'daysToDownload':
            return daysToDownload
        elif attrname == 'dateToDownload':
            return dateToDownload
        else:
            raise AttributeError, attrname


def usage():
    print '''usage: %s [options]
Options and arguments:
-h     : print this help message and exit (also --help)
-a uid : your apple id (also --appleId)
-p pwd : your password (also --password)
-o dir : directory where download file is stored, default is the current working directory (also --outputDirectory)
-v     : verbose output, default is off (also --verbose)
-u     : unzip download file, default is off (also --unzip)
-d num : number of days to download, default is 1 (also --days)
-D mm/dd/yyyy : report date to download, -d option is ignored when -D is used (also --date)''' % sys.argv[0]


def processCmdArgs():
    global appleId
    global password
    global outputDirectory
    global unzipFile
    global verbose
    global daysToDownload
    global dateToDownload

    # Check for command line options. The command line options
    # override the globals set above if present.
    try: 
        opts, args = getopt.getopt(sys.argv[1:], 'ha:p:o:uvd:D:', ['help', 'appleId=', 'password=', 'outputDirectory=', 'unzip', 'verbose', 'days=', 'date='])
    except getopt.GetoptError, err:
        #print help information and exit
        print str(err)  # will print something like "option -x not recongized"
        usage()
        return 2

    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            return 2
        elif o in ('-a', '--appleId'):
            appleId = a
        elif o in ('-p', '--password'):
            password = a
        elif o in ('-o', '--outputDirectory'):
            outputDirectory = a
        elif o in ('-u', '--unzip'):
            unzipFile = True
        elif o in ('-v', '--verbose'):
            verbose = True
        elif o in ('-d', '--days'):
            daysToDownload = a
        elif o in ('-D', '--date'):
            dateToDownload = a
        else:
            assert False, 'unhandled option'


# There is an issue with Python 2.5 where it assumes the 'version'
# cookie value is always interger.  However, itunesconnect.apple.com
# returns this value as a string, i.e., "1" instead of 1.  Because
# of this we need a workaround that "fixes" the version field.
#
# More information at: http://bugs.python.org/issue3924
class MyCookieJar(cookielib.CookieJar):
    def _cookie_from_cookie_tuple(self, tup, request):
        name, value, standard, rest = tup
        version = standard.get('version', None)
        if version is not None:
            version = version.replace('"', '')
            standard["version"] = version
        return cookielib.CookieJar._cookie_from_cookie_tuple(self, tup, request)


def showCookies(cj):
    for index, cookie in enumerate(cj):
        print index, ' : ', cookie
    


def downloadFile(options):
    if options.verbose == True:
        print '-- begin script --'

    urlBase = 'https://itts.apple.com%s'

    cj = MyCookieJar();
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))


    # Go to the iTunes Connect website and retrieve the
    # form action for logging into the site.
    urlWebsite = urlBase % '/cgi-bin/WebObjects/Piano.woa'
    urlHandle = opener.open(urlWebsite)
    html = urlHandle.read()
    match = re.search('"appleConnectForm" action="(.*)"', html)
    urlActionLogin = urlBase % match.group(1)


    # Login to iTunes Connect web site and go to the sales 
    # report page, get the form action url and form fields.  
    # Note the sales report page will actually load a blank 
    # page that redirects to the static URL. Best guess here 
    # is that the server is setting some session variables 
    # or something.
    webFormLoginData = urllib.urlencode({'theAccountName':options.appleId, 'theAccountPW':options.password})
    urlHandle = opener.open(urlActionLogin, webFormLoginData)
    html = urlHandle.read()

    # Get the form field names needed to download the report.
    if BeautifulSoup:
        if options.verbose == True:
            print 'using BeautifulSoap for HTML parsing'
        soup = BeautifulSoup.BeautifulSoup( html )
        form = soup.find( 'form', attrs={'name': 'frmVendorPage' } )
        urlDownload = urlBase % form['action']
        
        fieldNameReportType = soup.find( 'select', attrs={'id': 'selReportType'} )['name']
        fieldNameReportPeriod = soup.find( 'select', attrs={'id': 'selDateType'} )['name']
        fieldNameDayOrWeekSelection = soup.find( 'input', attrs={'name': 'hiddenDayOrWeekSelection'} )['name'] #This is kinda redundant
        fieldNameSubmitTypeName = soup.find( 'input', attrs={'name': 'hiddenSubmitTypeName'} )['name'] #This is kinda redundant, too
    else:
        match = re.findall('action="(.*)"', html)
        urlDownload = urlBase % match[1]
        match = re.findall('name="(.*?)"', html)
        fieldNameReportType = match[3]
        fieldNameReportPeriod = match[4]
        fieldNameDayOrWeekSelection = match[7]
        fieldNameSubmitTypeName = match[8]


    # Ah...more fun.  We need to post the page with the form
    # fields collected so far.  This will give us the remaining
    # form fields needed to get the download file.
    webFormSalesReportData = urllib.urlencode({fieldNameReportType:'Summary', fieldNameReportPeriod:'Daily', fieldNameDayOrWeekSelection:'Daily', fieldNameSubmitTypeName:'ShowDropDown'})
    urlHandle = opener.open(urlDownload, webFormSalesReportData)
    html = urlHandle.read()

    if BeautifulSoup:
        soup = BeautifulSoup.BeautifulSoup( html )
        form = soup.find( 'form', attrs={'name': 'frmVendorPage' } )
        urlDownload = urlBase % form['action']
        select = soup.find( 'select', attrs={'id': 'dayorweekdropdown'} )
        fieldNameDayOrWeekDropdown = select['name']
    else:
        match = re.findall('action="(.*)"', html)
        urlDownload = urlBase % match[1]
        match = re.findall('name="(.*?)"', html)
        fieldNameDayOrWeekDropdown = match[5]

    # Set the list of report dates.
    reportDates = []
    if options.dateToDownload == None:
        for i in range(int(options.daysToDownload)):
            today = datetime.date.today() - datetime.timedelta(i + 1)
            date = '%02i/%02i/%i' % (today.month, today.day, today.year)
            reportDates.append( date )
    else:
        reportDates = [options.dateToDownload]
        
    if options.verbose == True:
        print 'reportDates: ', reportDates

    unavailableCount = 0
    filenames = []
    for downloadReportDate in reportDates:
        # And finally...we're ready to download yesterday's sales report.
        webFormSalesReportData = urllib.urlencode({fieldNameReportType:'Summary', fieldNameReportPeriod:'Daily', fieldNameDayOrWeekDropdown:downloadReportDate, fieldNameDayOrWeekSelection:'Daily', fieldNameSubmitTypeName:'Download'})
        urlHandle = opener.open(urlDownload, webFormSalesReportData)
        try:
            filename = urlHandle.info().getheader('content-disposition').split('=')[1]
            filebuffer = urlHandle.read()
            urlHandle.close()

            if options.unzipFile == True:
                if options.verbose == True:
                    print 'unzipping archive file: ', filename
                #Use GzipFile to de-gzip the data
                ioBuffer = StringIO.StringIO( filebuffer )
                gzipIO = gzip.GzipFile( 'rb', fileobj=ioBuffer )
                filebuffer = gzipIO.read()

            filename = os.path.join(options.outputDirectory, filename)
            if options.unzipFile == True and filename[-3:] == '.gz': #Chop off .gz extension if not needed
                filename = os.path.splitext( filename )[0]

            if options.verbose == True:
                print 'saving download file:', filename

            downloadFile = open(filename, 'w')
            downloadFile.write(filebuffer)
            downloadFile.close()

            filenames.append( filename )
        except AttributeError:
            print '%s report is not available - try again later.' % downloadReportDate
            unavailableCount += 1

    if unavailableCount > 0:
        raise Exception, '%i report(s) not available - try again later' % unavailableCount

    if options.verbose == True:
        print '-- end of script --'

    return filenames


def main():
    if processCmdArgs() > 0:    # Will exit if usgae requested or invalid argument found.
      return 2
      
    # Set report options.
    options = ReportOptions()
    options.appleId = appleId
    options.password = password
    options.outputDirectory = outputDirectory
    options.unzipFile = unzipFile
    options.verbose = verbose
    options.daysToDownload = daysToDownload
    options.dateToDownload = dateToDownload
    # Download the file.
    downloadFile(options)


if __name__ == '__main__':
  sys.exit(main())
