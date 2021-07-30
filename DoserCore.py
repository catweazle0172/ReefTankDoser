import serial
import time
from datetime import datetime, timedelta
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from django.utils import timezone
import traceback
import requests

currentVersion="0.04"

class doseSequence:
	def __init__(self,name):
		self.doseName=name

class Doser:
	def __init__(self, id):
		self.id = id
		self.ArduinoStepper=False
		self.arduinostepper=None
		self.loadDoserFromDB()
		self.doserLog=logging.getLogger('DoserLog')
		handler = RotatingFileHandler(getBasePath()+ "Logs/doser.log", maxBytes=2000, backupCount=4)
		simpleFormatter = logging.Formatter('%(asctime)s - %(message)s')
		normalFormatter = logging.Formatter('%(asctime)s - %(threadName)s - %(message)s')
		handler.setFormatter(simpleFormatter)
		handler.setLevel(logging.INFO)
		self.doserLog.addHandler(handler)
		self.doserLog.setLevel(logging.INFO)
		self.debugLog=logging.getLogger('Debug')
		console = logging.StreamHandler()
		console.setLevel(logging.DEBUG)
		console.setFormatter(normalFormatter)
		self.debugLog.addHandler(console)
		handler2 = RotatingFileHandler(getBasePath()+"Logs/debug.log", maxBytes=8000, backupCount=4)
		handler2.setFormatter(normalFormatter)
		handler2.setLevel(logging.INFO)
		self.debugLog.addHandler(handler2)
		self.debugLog.setLevel(logging.DEBUG)
		self.loadDoseDefinitionsFromDB()
		self.resetJobSchedule=False
		self.systemStatus='Initializing'
		self.runDoseLock=None


	def loadDoserFromDB(self):
		from Doser.models import DoserExternal
		te=DoserExternal.objects.get(pk=1)	
		self.doserName=te.doserName
		self.doserVersion=te.doserVersion
		self.webPort=te.webPort
		self.measurementUnits=te.measurementUnits
		self.telegramBotToken=te.telegramBotToken
		self.telegramChatID=te.telegramChatID
		self.manageDatabases=te.manageDatabases
		self.daysOfResultsToKeep=te.daysOfResultsToKeep
		self.arduino1=te.arduino1
		self.arduino2=te.arduino2
		self.arduino3=te.arduino3
		self.arduino4=te.arduino4

	def loadDoseDefinitionsFromDB(self):
		from Doser.models import DoseDefinition
		self.doseSequenceList={}
		sequenceList=DoseDefinition.objects.all()
		for seq in sequenceList:
			ts=doseSequence(seq.doseName)
			ts.enableDose=seq.enableDose
			ts.arduinoNumber=seq.arduinoNumber
			ts.pumpName=seq.pumpName
			ts.fluidRemainingInML=seq.fluidRemainingInML
			ts.containerInML=seq.containerInML
			ts.minimumThreshold=seq.minimumThreshold
			ts.totalDoseAfterStartup=seq.totalDoseAfterStartup
			ts.changeDirection=seq.changeDirection
			ts.pumpSpeed=seq.pumpSpeed
			ts.pumpSteps=seq.pumpSteps
			ts.calibrateValue=seq.calibrateValue

			self.doseSequenceList[ts.doseName]=ts

	def connectingArduino(self):
		if self.arduino1:
			try:
				self.ARDUINO1=serial.Serial(self.arduino1, 115200, timeout=.1)
				print('Arduino 1 connected')
				time.sleep(2)
				return True

			except:
				print('Unable to connect to Arduino 1')
				return False
		if self.arduino2:
			try:
				self.ARDUINO2=serial.Serial(self.arduino2, 115200, timeout=.1)
				print('Arduino 2 connected')
				time.sleep(2)
				return True

			except:
				print('Unable to connect to Arduino 2')
				return False
		if self.arduino3:
			try:
				self.ARDUINO3=serial.Serial(self.arduino3, 115200, timeout=.1)
				print('Arduino 3 connected')
				time.sleep(2)
				return True

			except:
				print('Unable to connect to Arduino 3')
				return False
		if self.arduino4:
			try:
				self.ARDUINO4=serial.Serial(self.arduino4, 115200, timeout=.1)
				print('Arduino 4 connected')
				time.sleep(2)
				return True

			except:
				print('Unable to connect to Arduino 4')
				return False

	def reconnectToArduino(self):	
		if self.arduino1:
			self.ARDUINO1.close()
			time.sleep(1)
		if self.arduino2:
			self.ARDUINO2.close()
			time.sleep(1)
		if self.arduino3:
			self.ARDUINO3.close()
			time.sleep(1)
		if self.arduino4:
			self.ARDUINO4.close()
			time.sleep(1)

		self.connectingArduino()
		self.resetTotalDoseAfterStartup()

	def infoMessage(self,message):
		try:
			self.debugLog.info(message)
		except:  #Might not have initialized yet
			print(message)

	def debugMessage(self,message):
		try:
			if self.enableConsoleOutput:
				self.debugLog.debug(message)
		except:  #Might not have initialized yet
			print(message)

	def addJobToQueue(self,jobToQueue,amount):
		from Doser.models import JobExternal,DoseDefinition
		newJob=JobExternal()
		newJob.jobToRun=DoseDefinition.objects.get(doseName=jobToQueue)
		newJob.amount=amount
		newJob.save()

	def anyMoreJobs(self):
		from Doser.models import JobExternal
		jobsQueued=JobExternal.objects.filter(jobStatus='Queued')
		for job in jobsQueued:
			if job.timeStamp<=timezone.now():
				return True
		return False

	def getJobDaysText(self,doseName):
		from Doser.models import DoseSchedule
		try:
			dose=DoseSchedule.objects.get(doseToSchedule=doseName)
			return dose
		except:
			return 'Never'

	def getNextJob(self):
		from Doser.models import JobExternal,DoseResultsExternal
		jobsQueued=JobExternal.objects.filter(jobStatus='Queued')
		for job in jobsQueued:
			if job.timeStamp<=timezone.now():
				if not job.jobToRun.enableDose:
					self.infoMessage('Job ' + job.jobToRun.doseName + ' skipped since test disabled')
					skippedDose=DoseResultsExternal()
					skippedDose.testPerformed=job.jobToRun.doseName
					skippedDose.status='Skipped'
					skippedDose.datetimePerformed=timezone.now()
					skippedDose.save()
					job.delete()
				else:
					job.jobStatus='Running'
					job.save()                
					return job.jobToRun.doseName,job.amount
		return None

	def saveHoursToRunList(self,dose,times):
		from Doser.models import DoseSchedule
		try:
			dose=DoseSchedule.objects.get(doseToSchedule=dose.doseToSchedule)
			dose.hoursToRun=times
			dose.save()

		except:
			pass

	def calculateDose(self,dose):
		from Doser.models import DoseSchedule
		try:
			dose=DoseSchedule.objects.get(doseToSchedule=dose.doseToSchedule)
			dose.amountPerDose=round(dose.dailyDosage/dose.dailyNumberOfDosage,2)
			dose.save()

		except:
			pass

		return dose.amountPerDose

	def clearRunningJobs(self):
		from Doser.models import JobExternal
		JobExternal.objects.filter(jobStatus='Running').delete()

	def removeOldRecords(self):
		removeRecordsOlderThan=timezone.now()-timedelta(days=self.daysOfResultsToKeep)
		print('Removing records older than: ' + str(removeRecordsOlderThan))
		try:
			from Doser.models import DoseResultsExternal
			oldRecords=DoseResultsExternal.objects.filter(datetimePerformed__lte=removeRecordsOlderThan)
			for oldRecord in oldRecords:
				oldRecord.delete()

		except:
			traceback.print_exc()                        
		return


	def saveTestSaveBadResults(self):
		try:
			from Doser.models import DoseResultsExternal
			tre=DoseResultsExternal()
			tre.dosePerformed=self.currentDose
			whenPerformed=timezone.now()
			tre.datetimePerformed=whenPerformed
			if self.abortJob:
				tre.status='Aborted'
			else:
				tre.status='Failed'
			tre.results=None
			tre.save()
			return True
		except:
			traceback.print_exc()
			return False


	def saveDoseResults(self,ml):
		try:
			from Doser.models import DoseResultsExternal
			tre=DoseResultsExternal()
			tre.dosePerformed=self.currentDose
			if ml is None:
				tre.ml=None
				tre.status='Failed'
			else:
				tre.status='Completed'
				tre.results=str(ml)
			whenPerformed=timezone.now()
			tre.datetimePerformed=whenPerformed
			tre.save()
			return True
		except:
			traceback.print_exc()
			return False

	def addMLtoTotalML(self,ts,sequenceName):
		try:
			from Doser.models import DoseDefinition
			Jobs=DoseDefinition.objects.get(doseName=sequenceName)
			if ts.changeDirection is False:
				Jobs.totalDoseAfterStartup=round(ts.totalDoseAfterStartup+ts.amount,2)
			else:
				Jobs.totalDoseAfterStartup=round(ts.totalDoseAfterStartup-ts.amount,2)

			Jobs.fluidRemainingInML=round(ts.fluidRemainingInML-ts.amount,2)
			Jobs.save()
			return Jobs.totalDoseAfterStartup,Jobs.fluidRemainingInML
		except:
			traceback.print_exc()
			return False


	def calculateTimes(self,dose):
		timebetweendoseinsec = 86400/dose.dailyNumberOfDosage

		start = datetime.strptime(str(dose.startTime), '%H:%M:%S')
		end = datetime.strptime(str(dose.endTime), '%H:%M:%S')
		delta = timedelta(seconds=timebetweendoseinsec)
		times = []
		while start <= end:
		    times.append(start.strftime('%H:%M'))
		    start += delta
		return times


	def dosePump(self,arduino,pump,ML):
		if arduino=='ARDUINO1':
			try:
				self.ARDUINO1.write(str.encode(pump + str(ML) + '\n'))
				time.sleep(1)
				while True: 
					self.ARDUINO1.write(str.encode("?" + '\n'))
					self.ARDUINO1.flushInput() 
					time.sleep(0.2)
					grbl_out = str(self.ARDUINO1.readline()) 
					grbl_out_strip = grbl_out.split("|")
					grbl_out_split = grbl_out_strip[1].split (',',3)

					xas, yas, zas = grbl_out_split
					statuscorrect = grbl_out_strip[0].replace("b'<", '')
					xascorrect = xas.replace('MPos:', '')

					if pump=='X':
						if (round(float(xascorrect),2)) == float(ML):
							return True

					if pump=='Y':
						if (round(float(yas),2)) == float(ML):
							return True

					if pump=='Z':
						if (round(float(zas),2)) == float(ML):
							return True
			except:
				return False

		if arduino=='ARDUINO2':
			try:
				self.ARDUINO2.write(str.encode(pump + str(ML) + '\n'))
				time.sleep(1)
				while True: 
					self.ARDUINO2.write(str.encode("?" + '\n'))
					self.ARDUINO2.flushInput() 
					time.sleep(0.2)
					grbl_out = str(self.ARDUINO2.readline()) 
					grbl_out_strip = grbl_out.split("|")
					grbl_out_split = grbl_out_strip[1].split (',',3)

					xas, yas, zas = grbl_out_split
					statuscorrect = grbl_out_strip[0].replace("b'<", '')
					xascorrect = xas.replace('MPos:', '')

					if pump=='X':
						if (round(float(xascorrect),2)) == float(ML):
							return True

					if pump=='Y':
						if (round(float(yas),2)) == float(ML):
							return True

					if pump=='Z':
						if (round(float(zas),2)) == float(ML):
							return True

			except:
				return False

		if arduino=='ARDUINO3':
			try:
				self.ARDUINO3.write(str.encode(pump + str(ML) + '\n'))
				time.sleep(1)
				while True: 
					self.ARDUINO3.write(str.encode("?" + '\n'))
					self.ARDUINO3.flushInput() 
					time.sleep(0.2)
					grbl_out = str(self.ARDUINO3.readline()) 
					grbl_out_strip = grbl_out.split("|")
					grbl_out_split = grbl_out_strip[1].split (',',3)

					xas, yas, zas = grbl_out_split
					statuscorrect = grbl_out_strip[0].replace("b'<", '')
					xascorrect = xas.replace('MPos:', '')

					if pump=='X':
						if (round(float(xascorrect),2)) == float(ML):
							return True

					if pump=='Y':
						if (round(float(yas),2)) == float(ML):
							return True

					if pump=='Z':
						if (round(float(zas),2)) == float(ML):
							return True

			except:
				return False

		if arduino=='ARDUINO4':
			try:
				self.ARDUINO4.write(str.encode(pump + str(ML) + '\n'))
				time.sleep(1)
				while True: 
					self.ARDUINO4.write(str.encode("?" + '\n'))
					self.ARDUINO4.flushInput() 
					time.sleep(0.2)
					grbl_out = str(self.ARDUINO4.readline()) 
					grbl_out_strip = grbl_out.split("|")
					grbl_out_split = grbl_out_strip[1].split (',',3)

					xas, yas, zas = grbl_out_split
					statuscorrect = grbl_out_strip[0].replace("b'<", '')
					xascorrect = xas.replace('MPos:', '')

					if pump=='X':
						if (round(float(xascorrect),2)) == float(ML):
							return True

					if pump=='Y':
						if (round(float(yas),2)) == float(ML):
							return True

					if pump=='Z':
						if (round(float(zas),2)) == float(ML):
							return True

			except:
				return False

	def calibrate(self,dose):
		from Doser.models import DoseDefinition
		Jobs=DoseDefinition.objects.get(doseName=dose)
		steps=Jobs.pumpSteps
		amount=Jobs.calibrateValue
		Jobs.pumpSteps=int(50*(steps/amount))
		Jobs.save()
		print(Jobs.pumpSteps)
		if Jobs.pumpName=='X':
			steps=100
			speed=110

		if Jobs.pumpName=='Y':
			steps=101
			speed=111

		if Jobs.pumpName=='Z':
			steps=102
			speed=112

		try:

			if Jobs.arduinoNumber=='ARDUINO1':
				self.ARDUINO1.write(str.encode('$' + str(steps) + '=' + str(Jobs.pumpSteps) + '\n'))
				time.sleep(1)
				self.ARDUINO1.write(str.encode('$' + str(speed) + '=' + str(Jobs.pumpSpeed) + '\n'))
				time.sleep(1)
			elif Jobs.arduinoNumber=='ARDUINO2':
				self.ARDUINO2.write(str.encode('$' + str(steps) + '=' + str(Jobs.pumpSteps) + '\n'))
				time.sleep(1)
				self.ARDUINO2.write(str.encode('$' + str(speed) + '=' + str(Jobs.pumpSpeed) + '\n'))
				time.sleep(1)
			elif Jobs.arduinoNumber=='ARDUINO3':
				self.ARDUINO3.write(str.encode('$' + str(steps) + '=' + str(Jobs.pumpSteps) + '\n'))
				time.sleep(1)
				self.ARDUINO3.write(str.encode('$' + str(speed) + '=' + str(Jobs.pumpSpeed) + '\n'))
				time.sleep(1)
			elif Jobs.arduinoNumber=='ARDUINO4':
				self.ARDUINO4.write(str.encode('$' + str(steps) + '=' + str(Jobs.pumpSteps) + '\n'))
				time.sleep(1)
				self.ARDUINO4.write(str.encode('$' + str(speed) + '=' + str(Jobs.pumpSpeed) + '\n'))
				time.sleep(1)

			self.reconnectToArduino()

		except:
			return


	def resetTotalDoseAfterStartup(self):
		from Doser.models import DoseDefinition

		testList=DoseDefinition.objects.all()
		for tests in testList:
			Jobs=DoseDefinition.objects.get(doseName=tests)
			Jobs.totalDoseAfterStartup='0'
			Jobs.save()

	def telegram_bot_sendtext(self,message):
		send_text = 'https://api.telegram.org/bot' + (str(self.telegramBotToken)) + '/sendMessage?chat_id=' + (str(self.telegramChatID)) + '&parse_mode=Markdown&text=' + (str(message))
		print('send mesage: ' + message)
		response = requests.get(send_text)

		return response.json()

	def sendReport(self,doser,testRun,testKey):
		message=str('Message from: ' + self.doserName + ', ' + testRun + ', This Was a Test')
		self.telegram_bot_sendtext(message)

	def sendReagentAlarm(self,doser,dose,remainingML):
		message=str('From: ' + self.doserName + '\nReagent ' + str(dose) + ' Low, Remaining ML: '+ (str(remainingML)))
		self.telegram_bot_sendtext(message)

def getBasePath():
	programPath=os.path.realpath(__file__)
	programPathForwardSlash=programPath.replace('\\','/')
	programPathList=programPathForwardSlash.split('/')
	numPathSegments=len(programPathList)
	basePath=''
	pathSegment=0
	while pathSegment<numPathSegments-1:
		basePath+=programPathList[pathSegment] + '/'
		pathSegment+=1
	#print(basePath)
	return basePath


if __name__ == '__main__':
	basePath=getBasePath()
	sys.path.append(os.path.abspath(basePath))
	os.environ['DJANGO_SETTINGS_MODULE'] = 'ReefTankDoser.settings'
	django.setup()
	a=Doser(1)