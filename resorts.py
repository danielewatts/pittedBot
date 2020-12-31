"""
this is a class to define a resort obj
when a user requests info regarding a specific resort, this resort obj will be instantiated and contain all necessary info 
to fulfill information requests made by the user

Upon init all data will be populated, this will result in calling a utility class to retrieve info from the json file ?.. perhaps
"""

import json,re
import urllib,socket #importing socket to handle socket timeouts 
from urllib.request import Request,urlopen
#importing logging and azure logging tools to detect possible http errors and report them to azure logging tools
import logging 
from opencensus.ext.azure.log_exporter import AzureLogHandler
from collections import OrderedDict

class Resort:
    #class instance logger for debugging purposes
    CONNECTION_STRING = 'InstrumentationKey=5143d3c6-3d1e-444f-a65d-7aac7c370e32;IngestionEndpoint=https://centralus-0.in.applicationinsights.azure.com/'
    logger = logging.getLogger(__name__)
    logger.addHandler(
        AzureLogHandler(connection_string = CONNECTION_STRING)
    )
    #suboptimal mapping from jason to name 
    jsonResortIndexMap ={
        "alpental":0,
        "crystal":1,
        "baker":2,
        "white-pass":3,
        "stevens":4
        }
    elevationMapping = {
        "alpental":("4776","3087"),
        "crystal":("5233",""),
        "baker":("3901",""),
        "white-pass":("5827",""),
        "stevens":("4049","")
    }

    #keys for json extraction, to avoid errors when typing
    TEMPERATURE_TAG = 'temperature'
    SHORT_FORECAST_TAG = 'shortForecast'
    AREAS_TAG = "areas"
    PROPERTIES_TAG = "properties"
    NAMES_TAG = "name"
    DETAILED_FORECAST_TAG = "detailedForecast"
    PERIODS_TAG = "periods"
    NOAA_ERROR_MESSAGE = "NOAA failed :-( try entering prev request again"
    HTTP_REQ_TIMELIMIT = 3

    def __init__(self,resortName):
        self.logger.warning("Entered resort constructer")
        self.name = resortName
        self.forecastPeriods = []
        self.validNOAA = False
        self.zoneUrlMap = self.getAreaDataFromJSON(resortName)
        #initialize periodForeCast dict
        self.periodForeCastData = dict(zip([zone for zone in self.zoneUrlMap.keys()],[ [] for x in self.zoneUrlMap.keys()]))
        self.setPeriodForeCastData()
        #boolean to see if noaa forecast api retrieval was successful, only for testing purposes

  
    #method for getting the zones of a resort , most only have 1, but some may have multiple desired zones for forecasts
    # fills dict {zone:forecastURL}
    def getAreaDataFromJSON(self,resortName):
        zoneNameApiMap = OrderedDict()
        resortIndex = self.jsonResortIndexMap[resortName]
        # Opening JSON file 
        resortsJsonFile = open('resorts.json')
        # returns JSON object as  
        # a dictionary 
        data = json.load(resortsJsonFile) 
        self.logger.warning("opened up json file")
        areaInfo = data[resortIndex][self.AREAS_TAG]
        for subAreaDict in areaInfo:
            #populate zone array with name and corresponding urls
            zoneNameApiMap[subAreaDict['name']] = subAreaDict['url']
        #return the zone array to be assigned to area array in constructor
        self.logger.warning("returning url dict from local json")
        return zoneNameApiMap
    

    def setPeriodForeCastData(self):
        #populate key value pairs with the forecasting data
        for zone in self.zoneUrlMap.keys():
            self.periodForeCastData[zone] = self.getZonePeriodData(zone)


    #method that extracts the desired forecasting data from a specific zone
    #returns an array of the form [(name of period,detailedForecast)]
    def getZonePeriodData(self,zoneName):
        zonePeriodData = []
        noaaUrl = self.zoneUrlMap[zoneName]
        totalJsonData = None
        try:
            req = Request(noaaUrl)
            # req = urllib.request.urlopen(url,timeout=5)
            # req.headers.add_header('Accept','application/vnd.noaa.dwml+json;version=1')
            req.add_header('Accept','application/vnd.noaa.dwml+json;version=1')
            response = urlopen(req)
        except urllib.error.HTTPError as error:
            self.logger.warning("in urlib http error block, ERROR INFO: {} ".format(error))
            self.validNOAA = False
            print("http error detected")
        except socket.timeout:
            self.validNOAA = False
            self.logger.warning("Socket TIMED OUT !!")
        else: #block here only runs if an exception is not thrown
            self.validNOAA = True
            # totalJsonData = json.load(req)
            totalJsonData = json.load(response)
            forecastingPeriod = totalJsonData[self.PROPERTIES_TAG][self.PERIODS_TAG]
            self.forecastPeriods.append(forecastingPeriod) 
            for period in forecastingPeriod:
                nameOfPeriod = period[self.NAMES_TAG]
                detailedForecastDescript = period[self.DETAILED_FORECAST_TAG]
                #add this data to the zonePeriod array 
                zonePeriodData.append((nameOfPeriod,detailedForecastDescript))
            
            self.logger.warning("loaded up zone period data")
                
        return zonePeriodData
    

    #method for generating the forecast summary msg
    def getWeatherMsg(self):
        if self.validNOAA:
            msg = ""
            desiredPeriods = 4
            TEST_PERIODS = 1
            desiredPeriods = TEST_PERIODS
            #for each zone generate a message
            for zone in self.zoneUrlMap.keys():
                msg += "Area: " + self.name +", ZONE: " + str(zone) + "\n" 
                forecast = self.periodForeCastData[zone]
                for i in range(0,desiredPeriods):
                    periodName,descript = forecast[i] #returns a tuple (periodName, detailedDescript)
                    dayMsg = periodName + " : " + descript
                    msg += "" + dayMsg + "\n"
                #add spacing between zone summaries if more than one zone
                if len(self.zoneUrlMap.keys())>1:
                    msg+="\n"

            self.logger.warning("returning forecast msg")
            return msg
        else:
            self.logger.warning("returning error msg from getWeatherMsg method")
            return self.NOAA_ERROR_MESSAGE    
        
    def getPeriodSnowAccum(self,period):
        detailedDescript = period[self.DETAILED_FORECAST_TAG]
        try:
            idx = detailedDescript.index("New")
            return detailedDescript[idx::]
        except ValueError:
            return "No new snow"

        

            
    def getMultiPeriodMsg(self,desiredPeriods):
        if self.validNOAA:
            msg = ''
            zoneIdx = 0
            for zone in self.zoneUrlMap.keys():
                elevation = self.elevationMapping[self.name][zoneIdx]
                msg+= "Area: {}, Zone: {} at {}ft \n".format(self.name,str(zone),elevation) 
                forecast = self.periodForeCastData[zone]
                for i in range(0,desiredPeriods):
                    currPeriod = self.forecastPeriods[zoneIdx][i]
                    periodName = forecast[i][0] #returns a tuple (periodName, detailedDescript)
                    periodTemp,periodShortForecast = currPeriod[self.TEMPERATURE_TAG],currPeriod[self.SHORT_FORECAST_TAG]
                    periodSnowAccumulation = self.getPeriodSnowAccum(currPeriod)
                    dayMsg =  "{}: {}F, {}, {}".format(periodName,periodTemp,periodShortForecast,periodSnowAccumulation)
                    msg += dayMsg + "\n"
                #add spacing between zone summaries if more than one zone
                if len(self.zoneUrlMap.keys())>1:
                    msg+="\n"

                zoneIdx+=1

            self.logger.warning("returning multiDay forecast from multiDay")
            return msg
        else:
            self.logger.warning("returning error msg from getMultiPeriodMsg")
            return self.NOAA_ERROR_MESSAGE 
      




