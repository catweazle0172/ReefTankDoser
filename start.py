#Raspeberry for Web interface
#Arduino UNO with CNC Shield V3 for controlling the stepper motors
#MC2209 for controlling the Stepper dosing pumps
#Kamoer stepper dosing pumps

from DoserCore import Doser,getBasePath
import django
import rpyc
import os
import sys
import platform
import atexit
import threading
import time
import schedule
from rpyc.utils.server import ThreadedServer


remoteControlThreadRPYC=None
currentVersion='0.02'

def screenPresent(name):
	from subprocess import check_output
	var = str(check_output(["screen -ls; true"],shell=True))
	index=var.find(name)
	return index>-1

def runWebServer(doser,name):
	from subprocess import call
	generateWebLaunchFile(doser)
	call(["screen","-d","-m","-S",name,"bash", str(basePath) + "launchWebServer.sh"])   

def generateWebLaunchFile(doser):
	launchFile=basePath + "/launchWebServer.sh"
	launchText='python3 "' + basePath + 'manage.py" runserver 0.0.0.0:' + str(doser.webPort) + ' --insecure >> web.log 2>&1\n'
	f=open(launchFile,"w+")
	f.write(launchText)
	f.close()

def queueDoseJob(doser,jobToQueue,amount):
	print('Running job: ' + jobToQueue)
	doser.runDoseLock.acquire()
	doser.addJobToQueue(jobToQueue,amount)
	doser.runDoseLock.release()


def runDoseFromQueue():    
	while True:
		try:
			moreToDo=doser.anyMoreJobs()
			if moreToDo and doser.systemStatus=='Idle':
				doser.runDoseLock.acquire()
				nextJobToRun,amount=doser.getNextJob()
				doser.runDoseLock.release()
				if nextJobToRun is None:
					time.sleep(1)
				else:
					runDoseSequence(doser,nextJobToRun,amount)
					doser.abortJob=False
					doser.clearRunningJobs() 
			else:
				time.sleep(1)
		except:
			doser.debugLog.exception("Error in dose Runner...")
			time.sleep(1)

def runDoseSequence(doser,sequenceName,amount):
	doser.systemStatus="Running Dose"
	doser.loadDoseDefinitionsFromDB()

	doser.abortJob=False
	results=None
	doser.infoMessage('Running dose ' + sequenceName) 
	doser.currentDose=sequenceName
	doseSucceeded=None

	try:
		ts=doser.doseSequenceList[sequenceName]
		if amount>=0.01:
			ts.amount=amount

		newdosevalue,fluidRemainingInML=doser.addMLtoTotalML(ts,sequenceName)
		success=doser.dosePump(ts.arduinoNumber,ts.pumpName,newdosevalue)

		if success is not False:
			doseSucceeded=True
			doser.saveDoseResults(ts.amount)
			doser.doseStatus='Dosed: %.2f' % ts.amount
			print('Dosed: %.2f' % ts.amount)
		else:
			doser.saveTestSaveBadResults()
			doser.doseStatus='Dose Failed, No connection to Arduino ' + str(ts.arduinoNumber)
			print('Dose Failed, No connection to Arduino ' + str(ts.arduinoNumber))
			doser.reconnectToArduino()

	except:
		doser.debugLog.exception('Failure when running Dose')

	if fluidRemainingInML<ts.minimumThreshold:
		doser.sendReagentAlarm(doser,sequenceName,fluidRemainingInML,ts.alarmSent)

	doser.systemStatus="Idle"
	return doseSucceeded


def clearJobSchedules():
	schedule.clear()

def dailyMaintenance():
	doser.removeOldRecords()
	doser.resetAlarmSent()

def resetJobSchedules():
	clearJobSchedules()
	for ts in doser.doseSequenceList:
		try:
			setJobSchedules(ts) 
		except:
			pass 
	schedule.every().day.at('21:04').do(dailyMaintenance).tag('Maintenance')

def setJobSchedules(doseName):
	dose=doser.getJobDaysText(doseName)
	if dose.enableSchedule is False:
		doser.infoMessage(doseName + ' Schedule is disabled')
		return
	doser.infoMessage('Days to run for ' + doseName + ' was ' + dose.daysToRun)
	if dose.daysToRun=='Never':
		return

	times=doser.calculateTimes(dose)
	doser.saveHoursToRunList(dose,times)
	amount=doser.calculateDose(dose)
	for hour in times:
		print('Adding schedule for ' + doseName + ' on ' + dose.daysToRun + ' at ' + hour)
		if dose.daysToRun=='Everyday':
			schedule.every().day.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='2day':
			schedule.every(2).days.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='3day':
			schedule.every(3).days.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='4day':
			schedule.every(4).days.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='5day':
			schedule.every(5).days.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='10day':
			schedule.every(10).days.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='14day':
			schedule.every(14).days.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='21day':
			schedule.every(21).days.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='28day':
			schedule.every(28).days.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='Sunday':
			schedule.every().sunday.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='Monday':
			schedule.every().monday.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='Tuesday':
			schedule.every().tuesday.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='Wednesday':
			schedule.every().wednesday.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='Thursday':
			schedule.every().thursday.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='Friday':
			schedule.every().friday.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)
		elif dose.daysToRun=='Saturday':
			schedule.every().saturday.at(hour).do(queueDoseJob,doser,doseName,amount).tag(doseName)

def doserJobScheduler():
	resetJobSchedules()
	while True:
		if doser.resetJobSchedule:
			doser.resetJobSchedule=False
			resetJobSchedules()
		schedule.run_pending()
		time.sleep(0.1)

class DoserRemoteControl(rpyc.Service):
	def on_connect(self, conn):
		# code that runs when a connection is created
		# (to init the serivce, if needed)
		self.doser=doser

	def on_disconnect(self, conn):
		# code that runs when the connection has already closed
		# (to finalize the service, if needed)
		pass
	
	def doserOperation(self,operation):
		try:
			processWebCommand(doser,operation)
		except:
			doser.debugLog.exception("Continuing...")

def startHandler(threadName,operation): 
	doser.infoMessage('Thread: ' + threadName + ' started')
	operation.start() 


def exit_handler():
	global remoteControlThreadRPYC
	doser.debugMessage('Done')
	remoteControlThreadRPYC.close()


if __name__ == '__main__':
	from WebCmdHandler import processWebCommand
	basePath=getBasePath()
	sys.path.append(os.path.abspath(basePath))
	os.environ['DJANGO_SETTINGS_MODULE'] = 'ReefTankDoser.settings'
	django.setup()
	doser=Doser(1)

	if doser.manageDatabases:
		adminToUse=basePath + 'Doser/databaseAdminFull.py'
	else:
		adminToUse=basePath + 'Doser/databaseAdminEmpty.py'
	adminToReplace=basePath + 'Doser/databaseAdmin.py'
	try:
		fin=open(adminToUse,'r')
		text=fin.read()
		fin.close()
		fout=open(adminToReplace,'w+')
		fout.write(text)
		fout.close()
	except:
		doser.infoMessage('Admin update failed')
	doserWebName='DoserWeb'
	if platform.system()!='Windows':
		if screenPresent(doserWebName):
			doser.infoMessage('Web port already active, so not relaunched')
		else:
			doser.infoMessage('Web port not active, so launching webserver on port: ' + str(doser.webPort))
			runWebServer(doser,doserWebName)
	
	doser.runDoseLock=threading.Lock()
	doser.doserLog.info('Feeded Server Threaded Started')
	remoteControlThreadRPYC = ThreadedServer(DoserRemoteControl(), port = 18862,protocol_config = {"allow_public_attrs" : True})
	atexit.register(exit_handler)
	remoteControlThread=threading.Thread(target=startHandler,args=('Remote Control',remoteControlThreadRPYC))
	remoteControlThread.start()
	runDoseFromQueueThread=threading.Thread(target=runDoseFromQueue,name='Run Dose',args=())
	runDoseFromQueueThread.start()
	doser.infoMessage('Thread: ' + runDoseFromQueueThread.getName() + ' started')
	doserJobSchedulerThread=threading.Thread(target=doserJobScheduler,name='Job Scheduler',args=())
	doserJobSchedulerThread.start()
	doser.infoMessage('Thread: ' + doserJobSchedulerThread.getName() + ' started')
	doser.infoMessage('Doser Server version ' + currentVersion + ' loaded')
	doser.connectingArduino()
	doser.systemStatus="Idle"
	doser.resetTotalDoseAfterStartup()
	doser.infoMessage('Total Dose is reset to 0')


