"""
this is a class to define a resort obj
when a user requests info regarding a specific resort, this resort obj will be instantiated and contain all necessary info 
to fulfill information requests made by the user

Upon init all data will be populated, this will result in calling a utility class to retrieve info from the json file ?.. perhaps
"""

import json
import urllib.request
class Resort:
    #suboptimal mapping from jason to name 
    jsonResortIndexMap ={
        "alpental":0,
        "crystal":1,
        "baker":2,
        "white-pass":3,
        "stevens":4
        }
    #keys for json extraction, to avoid errors when typing
    AREAS_TAG = "areas"
    PROPERTIES_TAG = "properties"
    NAMES_TAG = "name"
    DETAILED_FORECAST_TAG = "detailedForecast"
    PERIODS_TAG = "periods"


    def __init__(self,resortName):
        self.name = resortName
        self.validNOAA = False
        self.zoneUrlMap = self.getAreaDataFromJSON(resortName)
        #initialize periodForeCast dict
        self.periodForeCastData = dict(zip([zone for zone in self.zoneUrlMap.keys()],[ [] for x in self.zoneUrlMap.keys()]))
        self.setPeriodForeCastData()
        
        #boolean to see if noaa forecast api retrieval was successful, only for testing purposes

  
    #method for getting the zones of a resort , most only have 1, but some may have multiple desired zones for forecasts
    # fills dict {zone:forecastURL}
    def getAreaDataFromJSON(self,resortName):
        zoneNameApiMap = {}
        resortIndex = self.jsonResortIndexMap[resortName]
        # Opening JSON file 
        resortsJsonFile = open('resorts.json')
        # returns JSON object as  
        # a dictionary 
        data = json.load(resortsJsonFile) 
        areaInfo = data[resortIndex][self.AREAS_TAG]
        for subAreaDict in areaInfo:
            #populate zone array with name and corresponding urls
            zoneNameApiMap[subAreaDict['name']] = subAreaDict['url']
        #return the zone array to be assigned to area array in constructor
        return zoneNameApiMap
    

    def setPeriodForeCastData(self):
        #populate key value pairs with the forecasting data
        for zone in self.zoneUrlMap.keys():
            self.periodForeCastData[zone] = self.getZonePeriodData(zone)


    #method that extracts the desired forecasting data from a specific zone
    #returns an array of the form [(name of period,detailedForecast)]
    def getZonePeriodData(self,zoneName):
        zonePeriodData = []
        url = self.zoneUrlMap[zoneName]
        totalJsonData = None
        #urlib might throw urllib.error.HTTPError
        #need to handle this so it doesn't bring server down
        try:
            req = urllib.request.urlopen(url)
        except:
            print("http error detected")
        else: #block here only runs if an exception is not thrown
            self.validNOAA = True
            totalJsonData = json.load(req)
            
        # with urllib.request.urlopen(url) as url:
        #         totalJsonData = json.loads(url.read().decode())
        
        if self.validNOAA:
            #iterate through period blocks and extract name, detailedForecast descript
            forecastingPeriods = totalJsonData[self.PROPERTIES_TAG][self.PERIODS_TAG]
            for period in forecastingPeriods:
                nameOfPeriod = period[self.NAMES_TAG]
                detailedForecastDescript = period[self.DETAILED_FORECAST_TAG]
                #add this data to the zonePeriod array 
                zonePeriodData.append((nameOfPeriod,detailedForecastDescript))
        
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

            return msg
        else:
            return "NOAA failed"            




   



