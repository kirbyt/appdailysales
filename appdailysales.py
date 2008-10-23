#!/usr/bin/python
#
# appdailysales.py
#
# iTune Connect Daily Sales Reports Downloader
# Copyright 2008 Kirby Turner
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
appleId = 'Your Apple Id'
password = 'Your Password'
# ----------------------------------------------------


import urllib
import urllib2
import cookielib
import datetime
import re

urlWebsite = 'https://itunesconnect.apple.com/WebObjects/iTunesConnect.woa'
urlActionLogin = 'https://itunesconnect.apple.com%s'
urlActionSalesReport = 'https://itunesconnect.apple.com%s'

print '-- begin script --'

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
	

cj = MyCookieJar();
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))



# Go to the iTunes Connect website and retrieve the
# form action for logging into the site.
urlHandle = opener.open(urlWebsite)
html = urlHandle.read()
match = re.search('action="(.*)"', html)
urlActionLogin = urlActionLogin % match.group(1)


# Login to iTunes Connect web site and retrieve the
# link to the sales report page.
webFormLoginData = urllib.urlencode({'theAccountName':appleId, 'theAccountPW':password})
urlHandle = opener.open(urlActionLogin, webFormLoginData)
html = urlHandle.read()
match =	re.search('href="(/WebObjects/iTunesConnect.woa/wo/.*)"><img', html)
urlActionSalesReport = urlActionSalesReport % match.group(1)


# Go to the sales report page, get the form action url and
# form fields.  Note the sales report page will actually
# load a blank page that redirects to the static URL. Best
# guess here is that the server is setting some session
# variables or something.
urlHandle = opener.open(urlActionSalesReport)
urlHandle = opener.open('https://itts.apple.com/cgi-bin/WebObjects/Piano.woa')
html = urlHandle.read()
match = re.findall('action="(.*)"', html)
urlDownload = "https://itts.apple.com%s" % match[1]


# Get the form field names needed to download the report.
match = re.findall('name="(.*?)"', html)
fieldNameReportType = match[3]
fieldNameReportPeriod = match[4]
fieldNameDayOrWeekSelection = match[6]
fieldNameSubmitTypeName = match[7]


# Ah...more fun.  We need to post the page with the form
# fields collected so far.  This will give us the remaining
# form fields needed to get the download file.
webFormSalesReportData = urllib.urlencode({fieldNameReportType:'Summary', fieldNameReportPeriod:'Daily', fieldNameDayOrWeekSelection:'Daily', fieldNameSubmitTypeName:'ShowDropDown'})
urlHandle = opener.open(urlDownload, webFormSalesReportData)
html = urlHandle.read()
match = re.findall('action="(.*)"', html)
urlDownload = "https://itts.apple.com%s" % match[1]
match = re.findall('name="(.*?)"', html)
fieldNameDayOrWeekDropdown = match[5]


# Set report date to yesterday's date.  This will be the most
# recent daily report available.  Another option would be to
# webscrape the dropdown list of available report dates and
# select the first item but setting the date to yesterday's
# date is easier.
today = datetime.date.today() - datetime.timedelta(1)
reportDate = '%i/%i/%i' % (today.month, today.day, today.year)


# And finally...we're ready to download yesterday's sales report.
webFormSalesReportData = urllib.urlencode({fieldNameReportType:'Summary', fieldNameReportPeriod:'Daily', fieldNameDayOrWeekDropdown:reportDate, fieldNameDayOrWeekSelection:'Daily', fieldNameSubmitTypeName:'Download'})
urlHandle = opener.open(urlDownload, webFormSalesReportData)
filename = urlHandle.info().getheader('content-disposition').split('=')[1]
filebuffer = urlHandle.read()
urlHandle.close()


print ' saving download file:', filename
downloadFile = open(filename, 'w')
downloadFile.write(filebuffer)
downloadFile.close()

print '-- end of script --'