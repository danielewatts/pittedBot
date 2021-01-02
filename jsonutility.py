"""
This class is designed to be a support class for the resort.py file
Methods in this class are designed to extract data from json response objects as well as retrieve response 
objects from URLs 
"""

import json,re,urllib,socket
from urllib.request import Request, urlopen
import logging 
from opencensus.ext.azure.log_exporter import AzureLogHandler

CONNECTION_STRING = 'InstrumentationKey=5143d3c6-3d1e-444f-a65d-7aac7c370e32;IngestionEndpoint=https://centralus-0.in.applicationinsights.azure.com/'
logger = logging.getLogger(__name__)
logger.addHandler(
    AzureLogHandler(connection_string = CONNECTION_STRING)
)

NOAA_REQ_HEADER = ('accept','text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8')

#this method will try and get a json response object
#if an http error is thrown, it will return None
def getJsonResponseObj(url,headerType=None,headerString=None):
    try:
        req = Request(url)
        if (headerType and headerString):
            req.add_header(headerType,headerString)

        response = urlopen(req)
        jsonResponse = json.load(response)
        return jsonResponse

    except urllib.error.HTTPError as er:
        logger.warning("in urlib http error block, ERROR INFO: {} ".format(er))
        #failed to retrieve anything so return None
        return None
    
    except socket.timeout as socketError:
        logger.warning("SOCKET time out, ERROR INFO: {}".format(socketError))
        #failed to retrieve anything so return None
        return None


#returns json resp object as dict
def openLocalJson(filePath):
    jsonFile = open(filePath)
    data = json.load(jsonFile)
    return data
