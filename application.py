from flask import Flask,request,redirect
from resorts import Resort
from twilio.twiml.messaging_response import MessagingResponse
import os
import logging 
from opencensus.ext.azure.log_exporter import AzureLogHandler

CONNECTION_STRING = 'InstrumentationKey=5143d3c6-3d1e-444f-a65d-7aac7c370e32;IngestionEndpoint=https://centralus-0.in.applicationinsights.azure.com/'
logger = logging.getLogger(__name__)
logger.addHandler(
    AzureLogHandler(connection_string = CONNECTION_STRING)
)

app = Flask(__name__)
# a mapping to be used for incoming text messages to the correct names of the resorts
resortMapping = {
    "mrs":"stevens",
    "mrb":"baker",
    "mrw":"white-pass",
    "mra":"alpental",
    "mrc":"crystal",
    "all":("alpental","crystal","baker","stevens","white-pass")
}

PERIODS_TO_FORECAST = 3
ALL_RESORT_PERIOD_RANGE = 1
# constructs and returns the correct resort
def getIntendedResort(userString):
    return Resort(resortMapping[userString])

#is input valid, ie is it in the resort mapping
def validateInput(incomingMsg):
    return (incomingMsg in resortMapping)

#gets rid of all spaces, returns first contigous string element
def cleanedBodySMS(sms):
    sms = sms.lower()
    sms = sms.split()
    return sms[0]

def getAllAreasReport(desiredPeriods):
    report = ''
    skiResorts = [skiResort for skiResort in resortMapping['all']]
    #created list of all ski resort objects
    for skiArea in skiResorts:
        report += skiArea.getMultiPeriodMsg(desiredPeriods)
        #seperates resorts
        if skiArea.name != 'alpental':
            report += '\n'

    logger.warning("all ski area report is {} chars".format(len(report)))
    return report

@app.route("/sms",methods = ['GET','POST'])
def smsReply():
    ##get incoming text msg, clean up
    logger.warning("Entered sms reply")

    body = request.values.get('Body',None)
    body = cleanedBodySMS(body)

    logger.warning("cleaned up and stored body of sms")

    resp = MessagingResponse()
    # skiResort = None
    #check if incoming msg is valid
    if validateInput(body) and body!="all":
        skiResort = getIntendedResort(body)
        logger.warning("created my resort obj")
        resortWeather = skiResort.getMultiPeriodMsg(PERIODS_TO_FORECAST)
        resp.message(resortWeather) 
        logger.warning("returning {}'s forecast to twilio".format(skiResort.name))
        return str(resp)    

    elif validateInput(body) and body=="all":
        #user is requesting a summary of all ski areas
        #instantiate all areas and return a large msg
        allWeather = getAllAreasReport(ALL_RESORT_PERIOD_RANGE)
        resp.message(allWeather)
        logger.warning("returning all forecasts to twilio")
        return str(resp)
    else:
        errorMsg = "invalid, please ONLY enter a 3 character resort code, capitilization is not important. \n options: {0}".format(list(resortMapping.keys()))
        resp.message(errorMsg)
        return str(resp)

# def localTest():
#     skiArea = Resort('stevens')
#     print(skiArea.getMultiPeriodMsg(3))


if __name__ == '__main__':
    app.run(debug=True)
    # localTest()
