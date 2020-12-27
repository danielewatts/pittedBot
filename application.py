from flask import Flask,request,redirect
from resorts import Resort
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)
# a mapping to be used for incoming text messages to the correct names of the resorts
resortMapping = {
    "mrs":"stevens",
    "mrb":"baker",
    "mrw":"white-pass",
    "mra":"alpental",
    "mrc":"crystal"
}

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

@app.route("/sms",methods = ['GET','POST'])
def smsReply():
    ##get incoming text msg, clean up

    body = request.values.get('Body',None)
    body = cleanedBodySMS(body)
    resp = MessagingResponse()
    skiResort = None
    #check if incoming msg is valid
    if validateInput(body):
        skiResort = getIntendedResort(body)
    else:
        errorMsg = "invalid, please ONLY enter a 3 character resort code, ie \n {0}".format(list(resortMapping.keys()))
        resp.message(errorMsg)
        return str(resp)

    #we have a valid ski resort, return weather data
    resortWeather = skiResort.getWeatherMsg()
    resp.message(resortWeather)

    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
