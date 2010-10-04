#!/usr/bin/python
#
# appdailysales.py
#
# iTune Connect Daily Sales Reports Downloader
# Copyright 2008-2010 Kirby Turner
#
# Version 2.5
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
#   Andrew de los Reyes
#   Maarten Billemont
#   Daniel Dickison
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
outputFormat = None
debug = False
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
import getpass


class ITCException(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value);


# The class ReportOptions defines a structure for passing
# report options to the download routine. The expected
# data attributes are:
#   appleId
#   password
#   outputDirectory
#   unzipFile
#   verbose
#   daysToDownload
#   dateToDownload
#   outputFormat
#   debug
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
        elif attrname == 'outputFormat':
            return outputFormat
        elif attrname == 'debug':
            return debug
        else:
            raise AttributeError, attrname


def usage():
    print '''usage: %s [options]
Options and arguments:
-h     : print this help message and exit (also --help)
-a uid : your apple id (also --appleId)
-p pwd : your password (also --password)
-P     : read the password from stdin (also --passwordStdin)
-o dir : directory where download file is stored, default is the current working directory (also --outputDirectory)
-v     : verbose output, default is off (also --verbose)
-u     : unzip download file, default is off (also --unzip)
-d num : number of days to download, default is 1 (also --days)
-D mm/dd/yyyy : report date to download, -d option is ignored when -D is used (also --date)
-f format : output file name format (see strftime; also --format)
--debug : debug output, default is off''' % sys.argv[0]


def processCmdArgs():
    global appleId
    global password
    global outputDirectory
    global unzipFile
    global verbose
    global daysToDownload
    global dateToDownload
    global outputFormat
    global debug

    # Check for command line options. The command line options
    # override the globals set above if present.
    try: 
        opts, args = getopt.getopt(sys.argv[1:], 'ha:p:Po:uvd:D:f:', ['help', 'appleId=', 'password=', 'passwordStdin', 'outputDirectory=', 'unzip', 'verbose', 'days=', 'date=', 'format=', 'debug'])
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
        elif o in ('-P', '--passwordStdin'):
            password = getpass.getpass()
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
        elif o in ('-f', '--format'):
            outputFormat = a
        elif o in ('--debug'):
            debug = True
            verbose = True # Turn on verbose if debug option is on.
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
    

def readHtml(opener, url, data=None, options=None):
    request = urllib2.Request(url, data)
    urlHandle = opener.open(request)
    html = urlHandle.read()
    if options and options.debug:
        f = open(os.path.join(options.outputDirectory, 'temp.html'), 'w')
        try:
            f.write(html)
        finally:
            f.close()
    return html


def downloadFile(options):
    if options.verbose == True:
        print '-- begin script --'

    if (options.outputDirectory != '' and not os.path.exists(options.outputDirectory)):
        os.makedirs(options.outputDirectory)

    urlITCBase = 'https://itunesconnect.apple.com%s'

    cj = MyCookieJar();
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    if options.verbose == True:
        print 'Signing into iTunes Connect web site.'

    # Go to the iTunes Connect website and retrieve the
    # form action for logging into the site.
    urlWebsite = urlITCBase % '/WebObjects/iTunesConnect.woa'
    html = readHtml(opener, urlWebsite, options=options)
    match = re.search('" action="(.*)"', html)
    urlActionLogin = urlITCBase % match.group(1)


    # Login to iTunes Connect web site and go to the sales 
    # report page, get the form action url and form fields.  
    # Note the sales report page will actually load a blank 
    # page that redirects to the static URL. Best guess here 
    # is that the server is setting some session variables 
    # or something.
    webFormLoginData = urllib.urlencode({'theAccountName':options.appleId, 'theAccountPW':options.password, '1.Continue':'0'})
    html = readHtml(opener, urlActionLogin, webFormLoginData, options=options)
    if (html.find('Your Apple ID or password was entered incorrectly.') != -1):
        raise ITCException, 'User or password incorrect.'

    # Find the Sales and Trends URL.
    if options.verbose == True:
        print 'Accessing Sales and Trends reporting web site.'
    
    try:
        match = re.findall('/WebObjects/iTunesConnect.woa/wo/(.*?).0.9.7.2.9.1.0.0.3', html)
        backtrackedId = match[0]
    except:
        if options.verbose == True:
            print 'Unable to find the Sales and Trends URL.'
            raise
        else:
            raise ITCException, 'Unable to find the Sales and Trends URL.'
    
    # Click through to the Sales and Trends.
    salesAndTrendsPath = '/WebObjects/iTunesConnect.woa/wo/%s.0.9.7.2.9.1.0.0.3'
    urlSalesAndTrends = urlITCBase % salesAndTrendsPath % backtrackedId
    if options.debug == True:
        print 'Sales and Trends URL: ', urlSalesAndTrends

    html = readHtml(opener, urlSalesAndTrends, options=options)

    # We're at the vendor default page. Might need additional work if your account
    # has more than one vendor.
    try:
        match = re.findall('"javax.faces.ViewState" value="(.*?)"', html)
        viewState = match[0]
        match = re.findall('script id="defaultVendorPage:(.*?)"', html)
        defaultVendorPage = match[0]
        ajaxName = re.sub('_2', '_0', defaultVendorPage)
        if options.debug == True:
            print 'viewState: ', viewState
            print 'defaultVendorPage: ', defaultVendorPage
            print 'ajaxName: ', ajaxName
    except:
        errMessage = 'Unable to find default vendor page.'
        if options.verbose == True:
            print errMessage
            raise
        else:
            raise ITCException, errMessage

    urlDefaultVendorPage = 'https://reportingitc.apple.com/vendor_default.faces'
    webFormSalesReportData = urllib.urlencode({'AJAXREQUEST':ajaxName, 'javax.faces.ViewState':viewState, 'defaultVendorPage':defaultVendorPage, 'defaultVendorPage:'+defaultVendorPage:'defaultVendorPage:'+defaultVendorPage})
    html = readHtml(opener, urlDefaultVendorPage, webFormSalesReportData, options=options)

    # Check for notification messages.
    urlDashboard = 'https://reportingitc.apple.com/subdashboard.faces'
    html = readHtml(opener, urlDashboard, options=options)
    try:
        # Note the (?s) is an inline re.DOTALL, makes . match new lines.
        match = re.findall('(?s)<div class="notification">(.*?)</span>', html)
        notificationDiv = match[0]
        match = re.findall('(?s)<td>(.*?)</td>', notificationDiv)
        notificationMessage = match[0]
        if options.verbose == True:
            print notificationMessage
    except:
        pass # Do nothing. We're just checking for notifications.


    # Access the sales report page.
    if options.verbose == True:
        print 'Accessing sales report web page.'
    urlSalesReport = 'https://reportingitc.apple.com/sales.faces'
    html = readHtml(opener, urlSalesReport, options=options)


    # Get the form field names needed to download the report.
    try:
        match = re.findall('"javax.faces.ViewState" value="(.*?)"', html)
        viewState = match[0]
        match = re.findall('theForm:j_id_jsp_[0-9]*_6', html)
        dailyName = match[0]
        ajaxName = re.sub('._6', '_2', dailyName)
        dateName = re.sub('._6', '_8', dailyName)
        selectName = re.sub('._6', '_32', dailyName)
        if options.debug == True:
            print 'viewState: ', viewState
            print 'dailyName: ', dailyName
            print 'ajaxName: ', ajaxName
            print 'dateName: ', dateName
            print 'selectName:', selectName
    except:
        errMessage = 'Unable to load the sales report web page at this time. A number of reasons can cause this including delayed reporting, unsigned contracts, and change to the web site breaking this script. Try again later or sign into iTunes Connect and verify access.'
        if options.verbose == True:
            print errMessage
            raise
        else:
            raise ITCException, errMessage


    # Get the list of available dates.
    try:
        # Note the (?s) is an inline re.DOTALL, makes . match new lines.
        match = re.findall('(?s)<div class="pickList">(.*?)</div>', html)
        dateListAvailableDays = re.findall('<option value="(.*?)"', match[0])
        dateListAvailableWeeks = re.findall('<option value="(.*?)"', match[1])
        if options.debug == True:
            print 'dateListAvailableDays: ', dateListAvailableDays
            print 'dateListAvailableWeeks: ', dateListAvailableWeeks
    except:
        errMessage = 'Unable to retrieve the list of available dates.'
        if options.verbose == True:
            print errMessage
            raise
        else:
            raise ITCException, errMessage


    # Click through from the dashboard to the sales page.
    webFormSalesReportData = urllib.urlencode({'AJAXREQUEST':ajaxName, 'theForm':'theForm', 'theForm:xyz':'notnormal', 'theForm:vendorType':'Y', 'theForm:datePickerSourceSelectElementSales':dateListAvailableDays[0], 'theForm:weekPickerSourceSelectElement':dateListAvailableWeeks[0], 'javax.faces.ViewState':viewState, dailyName:dailyName})
    html = readHtml(opener, urlSalesReport, webFormSalesReportData, options=options)
    match = re.findall('"javax.faces.ViewState" value="(.*?)"', html)
    viewState = match[0]


    # Set the list of report dates.
    # A better approach is to grab the list of available dates
    # from the web site instead of generating the dates. Will
    # consider doing this in the future.
    reportDates = []
    if options.dateToDownload == None:
        for i in range(int(options.daysToDownload)):
            today = datetime.date.today() - datetime.timedelta(i + 1)
            reportDates.append( today )
    else:
        reportDates = [datetime.datetime.strptime(options.dateToDownload, '%m/%d/%Y').date()]

    if options.debug == True:
        print 'reportDates: ', reportDates


    ####
    if options.verbose == True:
        print 'Downloading daily sales reports.'
    unavailableCount = 0
    filenames = []
    for downloadReportDate in reportDates:
        # Set the date within the web page.
        dateString = downloadReportDate.strftime('%m/%d/%Y')
        
        if dateString in dateListAvailableDays:
            if options.verbose == True:
                print 'Downloading report for: ', dateString
            webFormSalesReportData = urllib.urlencode({'AJAXREQUEST':ajaxName, 'theForm':'theForm', 'theForm:xyz':'notnormal', 'theForm:vendorType':'Y', 'theForm:datePickerSourceSelectElementSales':dateString, 'theForm:datePickerSourceSelectElementSales':dateString, 'theForm:weekPickerSourceSelectElement':dateListAvailableWeeks[0], 'javax.faces.ViewState':viewState, selectName:selectName})
            html = readHtml(opener, urlSalesReport, webFormSalesReportData)
            match = re.findall('"javax.faces.ViewState" value="(.*?)"', html)
            viewState = match[0]

            # And finally...we're ready to download yesterday's sales report.
            webFormSalesReportData = urllib.urlencode({'theForm':'theForm', 'theForm:xyz':'notnormal', 'theForm:vendorType':'Y', 'theForm:datePickerSourceSelectElementSales':dateString, 'theForm:weekPickerSourceSelectElement':dateListAvailableWeeks[0], 'javax.faces.ViewState':viewState, 'theForm:downloadLabel2':'theForm:downloadLabel2'})
            request = urllib2.Request(urlSalesReport, webFormSalesReportData)
            urlHandle = opener.open(request)
            try:
                if options.debug == True:
                    print urlHandle.info()
                if (options.outputFormat):
                    filename = downloadReportDate.strftime(options.outputFormat)
                else:
                    filename = urlHandle.info().getheader('content-disposition').split('=')[1]

                filebuffer = urlHandle.read()
                urlHandle.close()

                if options.unzipFile == True:
                    if options.verbose == True:
                        print 'Unzipping archive file: ', filename
                    #Use GzipFile to de-gzip the data
                    ioBuffer = StringIO.StringIO( filebuffer )
                    gzipIO = gzip.GzipFile( 'rb', fileobj=ioBuffer )
                    filebuffer = gzipIO.read()

                filename = os.path.join(options.outputDirectory, filename)
                if options.unzipFile == True and filename[-3:] == '.gz': #Chop off .gz extension if not needed
                    filename = os.path.splitext( filename )[0]

                if options.verbose == True:
                    print 'Saving download file:', filename

                downloadFile = open(filename, 'w')
                downloadFile.write(filebuffer)
                downloadFile.close()

                filenames.append( filename )
            except AttributeError:
                print '%s report is not available - try again later.' % dateString
                unavailableCount += 1
        else:
            print '%s report is not available - try again later.' % dateString
            unavailableCount += 1
    # End for downloadReportDate in reportDates:
    ####

    if unavailableCount > 0:
        raise ITCException, '%i report(s) not available - try again later' % unavailableCount

    if options.debug == True:
        os.remove(os.path.join(options.outputDirectory, "temp.html"))
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
    options.outputFormat = outputFormat
    options.debug = debug
    
    # Download the file.
    try:
        downloadFile(options)
    except ITCException, e:
        print e.value
        return 1


if __name__ == '__main__':
  sys.exit(main())
