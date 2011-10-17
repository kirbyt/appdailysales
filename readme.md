# Introduction

AppDailySales is a Python script that will download daily sales report files from the iTunes Connect web site.  

# How to Use

AppDailySales can be used as a stand-alone program or as part of another script.

## Use as Stand-alone Program

Download the script appdailysales.py and run the command line:

**python appdailysales.py**

    usage: appdailysales.py [options]
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
	-n      : used with -f, skips downloading of report files that already exist (also --noOverWriteFiles)
	--proxy : URL of the proxy
    --debug : debug output, default is off

You can also change the option variables located towards the top of the script file if you prefer to not use the command line options. However, this approach is not recommended with version 1.2 and greater of the script file.

**Note:** The script will return the exit code 0 if successful, otherwise exit code 1 is returned.

## Use as Part of Another Script

As of Version 1.3 the AppDailySales script can be used as part of another script.  Simply import appdailysales, set the report options, and call the downloadFile function.  Here is a sample script file to help you get started:

    #!/usr/bin/python

    import sys
    import traceback
    import appdailysales

    def main():
      options = appdailysales.ReportOptions()
      options.appleId = 'Your Apple Id'
      options.password = 'Your Password'
      options.outputDirectory = ''
      options.unzipFile = False
      options.verbose = False
      try:
        filename = appdailysales.downloadFile(options)
        print 'Report file downloaded: ', filename
      except:
        traceback.print_exc()
	
    if __name__ == '__main__':
      main()

The function **appdailysales.downloadFile** will return the name of the last file downloaded. Be sure to include a try..except block around the call to gracefully handle any errors that might occur during the download.

## Download Reports Multiple Days

As of version 1.6, there is a -d (also --days) option that is used to specify the number of days to download.  The default is 1, which will download yesterday's report and keeps the script backwards compatible with the previous versions. Any value can be used for this option.  However please note that as of now Apple only stores the last 7 days of daily sales reports.  Using a value greater than 7 will result in a "report not available" error. 

Why not add a check in the script to prevent values greater than 7? I decided not to include the check on the off chance Apple decides to provide access to reports older than 7 days.  

## Report File Name Formatting

Version 2.1 introduces the new -f (also --format) option. This option allows you to reformat the report file name. The format is specific as per strftime (see man page), e.g. "%Y-%m-%d-daily.txt.gz" would give you "2010-09-16-daily.txt.gz".

By default, the report file is compressed. When using the -f option, be sure to include the appropriate file name extension, e.g., ".gz". Use the -u option to have the script uncompress the file for you. The script will automatically strip the .gz extension if present.

## What Version of Python

The script was written for and has been tested with **Python version 2.5.x, 2.6.x, and 2.7.x**. It is doubtful the script will work with Python 3.x without some tweaking.

## Debugging the Script

Version 2.4 introduces the new --debug flag. This flag will display additional verbose output for debugging and troubleshooting the script. Also, when this flag is turned on and the script encounters a screen scraping error, a file named temp.html is created and stored in the output directory. This file contains the HTML downloaded in the last web request.

# Change History

**Version 2.9.2**

  * Updated script to work with latest iTC changes.

**Version 2.9**

  * Automatically creates nested directories added to format (-f) strings (eg. -f %Y/%Y-%m/Daily-%Y-%m-%d.txt).  Works with outputDirectory (-o). (Thanks Mike Kasprzak)
  * New command line option "-n". Used with format (-f), any file that already exists isn't downloaded. (Thanks Mike Kasprzak)
  * Added proxy support. (Thanks stakemura)

**Version 2.8**

  * Updated the script to support the latest iTC changes.
  * Move source code repository to github. (https://github.com/kirbyt/appdailysales)

**Version 2.7**

  * Modified the script to make multiple attempts at loading the vendor default page before reporting an error.
  * Changed how content-disposition is checked to avoid attempts of unzipping HTML.

**Version 2.6**
  
  * Updated the script to support the new URL to the Sales and Trends web site. (Thanks ferenc.vehmann)
  * Enabled RFC2965 cookie support. (Thanks troegenator)

**Version 2.5**

  * Updated to display notification messages, if any, from Apple displayed on the sales and trends dashboard. Must use the -v or --verbose flag to see the notification message.

**Version 2.4**

  * Updated to support the latest iTC web site changes.
  * Updated -v (--verbose) flag to display user friendlier messages.
  * Added --debug flag. Provides addition verbose output for debugging and troubleshooting.
  * Updated to scrape the vendor page and make the default vendor setting.
  * Updated to scrape for the list of available report dates.
  * Updated to download only available reports. A message is displayed when a requested report is not available.

**Version 2.3**

  * Update to screen scrape for the sales and trends URL.

**Version 2.2**

  * Replaced the "with" statement, which was causing problems on different platforms and with different version of python, with more compatible code.

**Version 2.1**

  * Adds new -f (also --format) option to reformat the report file name. (Thanks Daniel Dickison.)
  * Updated to display invalid login credential message if the login process fails. (Thanks Daniel Dickison.)
  * The -v (also --verbose) will save the last retrieved html to the file temp.html. This is helpful when troubling a problem with screen scraping the web site. The temp.html is automatically deleted when the script successfully downloads the report. (Thanks Daniel Dickison.)
  * The -P (also --passwordStdin) now displays the prompt "Password:"

**Version 2.0.2**

  * Removed invalid parameter used to focus an error and test new error reporting.

**Version 2.0.1**

  * Improved error reporting

**Version 2.0**

  * Updated to support September 9, 2010 iTunes Connect changes.
  * Dropped BeautifulSoup support. I don't have the time to support two separate screen scraping approaches. 

**Version 1.10**

  * Fixed bugs caused by recent iTunes Connect changes.

**Version 1.9**

  * Applied patch that adds new option to read the password from the stdin (thanks Maarten Billemont).

**Version 1.8.1**

  * Modified code to work with latest iTunes Connect changes (thanks Andrew de los Reyes).

**Version 1.8**

  * Now uses os.path.join to avoid problems with trailing slash or the lack of when specifying the output directory (thanks Keith Simmons).

**Version 1.7**

  * Removed code that received available report dates from the HTML. This broke backwards compatibility when using BeautifulSoup and was misleading when Apple delayed "yesterday's" reports.
  * Added in -D (also --date) option that allows the download of a specific date. Note: date must be in mm/dd/yyyy format.

**Version 1.6**

  * Modified to use BeautifulSoup is available (thanks Rogue Amoeba Software, LLC)
  * Modified unzip logic to work in memory only, making it faster and less error prone (thanks Rogue Amoeba Software, LLC)
  * Added days to download option (-d or --days), can be used to download all available reports

**Version 1.5**

  * Updated script to work with latest web site changes
  * Removed trackback output when usage is displayed

**Version 1.4**

  * Modified to use itts.apple.com as the starting point; eliminates 2 HTTP calls (thanks to Leon Ho for providing the change)
  * Added error check for download file; prints 'report not available' message if detected

**Version 1.3**

  * Modified script to run as stand-alone program or as part of another script

**Version 1.2**

  * Added command line options (editing script file no longer needed)
  * Added option to unzip download file

**Version 1.1**

  * Initial release

# Contributors

Special thanks goes out to the following individuals for contributing to this project:

  * Leon Ho
  * Rogue Amoeba Software, LLC
  * Keith Simmons
  * Andrew de los Reyes
  * Maarten Billemont
  * Daniel Dickison
  * Mike Kasprzak
  * Shintaro TAKEMURA

# Code License

[MIT License](http://www.opensource.org/licenses/mit-license.php)

# Some Final Words

I created this script with the iPhone developer in mind.  Being an iPhone developer myself I don't want to remember to download the daily sales report from yesterday's activity so I wrote this script.  I have a cron job scheduled on a server that will download each day's report for me so I don't have to.  Ain't automation great.

