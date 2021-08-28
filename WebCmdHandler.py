from DoserCore import Doser
from start import queueDoseJob
import time


def parseHome(doser,cmdOperation,cmdObject,cmdValue):
    try:
        if cmdOperation=='Abort':
            doser.abortJob=True
        else:
            print('Unknown HOME operation: ' + cmdOperation)                               
    except:
        doser.debugLog.exception("Error in HOME parsing")

def parseSchedule(doser,cmdOperation,cmdObject,cmdValue):
    try:
        if cmdOperation=='reloadSchedules':
            doser.resetJobSchedule=True

        else:
            print('Unknown SCHEDULE operation: ' + cmdOperation)                               
    except:
        doser.debugLog.exception("Error in SCHEDULE parsing")

def parseReload(doser,cmdOperation,cmdObject,cmdValue):
    try:
        if cmdOperation=='DoseDefs':
            doser.loadDoseDefinitionsFromDB()
        else:
            print('Unknown RELOAD operation: ' + cmdOperation)                               
    except:
        doser.debugLog.exception("Error in SCHEDULE parsing")


def parseOperate(doser,cmdOperation,cmdObject,cmdValue):
    try:
        queueDoseJob(doser,cmdOperation,cmdObject)                    
                                        
    except:
        print('Unknown OPERATE operation: ' + cmdOperation)   
        doser.debugLog.exception("Error in OPERATE parsing")


def parseCalibrate(doser,cmdOperation,cmdObject,cmdValue):
    doser.loadDoseDefinitionsFromDB()
    if cmdOperation in doser.doseSequenceList:
        try:
            ts=doser.doseSequenceList[cmdOperation]
            ts.amount=int(cmdObject)
            print(ts.amount)
            newdosevalue,fluidRemainingInML=doser.addMLtoTotalML(ts,cmdOperation)
            print(newdosevalue)
            doser.dosePump(ts.arduinoNumber,ts.pumpName,newdosevalue)
            print('Dose calibration value +- 50ML')
            return True
        except:
            doser.debugLog.exception("Error in CALIBRATION parsing")

    if cmdOperation=='UPDATE':
        time.sleep(1)
        doser.calibrate(cmdObject)
    else:
        print('Unknown CALIBRATE operation: ' + cmdOperation)   

def parseAlarms(doser,cmdOperation,cmdObject,cmdValue):
    try:
        if cmdOperation=='testTelegram':
            doser.sendReport(doser,'Telegram Test',cmdObject)                    
        else:
            print('Unknown ALARMS operation: ' + cmdOperation)                               
    except:
        doser.debugLog.exception("Error in ALARMS parsing")

def processWebCommand(doser,commandString):
    print('Command String Received: ' + str(commandString))
#    if tester.simulation:
#        return
    cmdParts=commandString.split('/')
    cmdCategory=None
    cmdOperation=None
    cmdObject=None
    cmdValue=None
    try:
        cmdCategory=cmdParts[0]
        cmdOperation=cmdParts[1]
        cmdObject=cmdParts[2]
        cmdValue=cmdParts[3]
    except:
        pass
    if cmdCategory=='HOME':
        parseHome(doser,cmdOperation,cmdObject,cmdValue)
    elif cmdCategory=='OPERATE':
        parseOperate(doser,cmdOperation,cmdObject,cmdValue)
    elif cmdCategory=='SWATCH':
        parseSwatch(doser,cmdOperation,cmdObject,cmdValue)
    elif cmdCategory=='DIAGNOSTIC':
        parseDiagnostics(doser,cmdOperation,cmdObject,cmdValue)
    elif cmdCategory=='CALIBRATE':
        parseCalibrate(doser,cmdOperation,cmdObject,cmdValue)
    elif cmdCategory=='ALARMS':
        parseAlarms(doser,cmdOperation,cmdObject,cmdValue)
    elif cmdCategory=='SCHEDULE':
        parseSchedule(doser,cmdOperation,cmdObject,cmdValue)
    elif cmdCategory=='RELOAD':
        parseReload(doser,cmdOperation,cmdObject,cmdValue)
    elif cmdCategory=='CLEAR':
        pass
    else:
        doser.debugLog.info('Unknown category in web command string: ' + commandString)    

if __name__ == '__main__':
    pass