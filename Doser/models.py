from django.db import models
from django import forms
from datetime import datetime
from django.forms import ModelForm
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.contrib.postgres.fields import ArrayField
import django.contrib.postgres.fields

class DoserExternal(models.Model):
    doserName = models.CharField(max_length=200, default='Doser')
    doserVersion = models.CharField(max_length=40, default='v1.0')
    webPort = models.IntegerField(default=8000,validators=[MinValueValidator(1001),MaxValueValidator(65535)])
    measurementUnits = models.CharField(max_length=40, default='US Imperial')
    manageDatabases = models.BooleanField(default=False)
    telegramBotToken = models.CharField(max_length=50, default='None')
    telegramChatID = models.IntegerField(default=0)
    enableConsoleOutput = models.BooleanField(default=False)
    daysOfResultsToKeep = models.IntegerField(default=100)
    arduino1 = models.CharField(max_length=80, default='',blank=True)
    arduino2 = models.CharField(max_length=80, default='',blank=True)
    arduino3 = models.CharField(max_length=80, default='',blank=True)
    arduino4 = models.CharField(max_length=80, default='',blank=True)

    def __str__(self):
        return self.doserName

class DoseResultsExternal(models.Model):
    dosePerformed = models.CharField(max_length=200, default=None, help_text="This was the test that was run")
    results = models.FloatField(default=None, null=True, blank=True, help_text="Numeric results from running the test")
    status = models.CharField(max_length=200,default='Completed', help_text="Completion status of the test")
    datetimePerformed = models.DateTimeField(default=datetime.now, help_text="When the test was run")

    def __str__(self):
        return self.dosePerformed

    class Meta:
        ordering = ['datetimePerformed']



class DoseDefinition(models.Model):
    doseName = models.CharField(max_length=40, default='New Dose',unique=True, blank=False, validators=[RegexValidator(regex='^New Dose$',message='Pick a better name than New Dose',inverse_match=True)])
    enableDose = models.BooleanField(default=True)
    Arduino_Choices = (('ARDUINO1','Arduino1'),('ARDUINO2','Arduino2'),('ARDUINO3','Arduino3'),('ARDUINO4','Arduino4'))
    arduinoNumber = models.CharField(default='Aruino1', choices=Arduino_Choices, max_length=10)    
    Stepper_Pumps = (('X','X'),('Y','Y'),('Z','Z'))
    pumpName = models.CharField(max_length=1, default='Z', choices=Stepper_Pumps)
    fluidRemainingInML = models.FloatField(default=0, help_text="The amount of usable reagent remaining (computed by the machine)")
    containerInML = models.IntegerField(default=0, help_text="The amount of the container in ML")
    minimumThreshold = models.FloatField(default=0, help_text="Minium threshold for sending Telegram alarm")
    totalDoseAfterStartup = models.FloatField(default=0, help_text="The amount of the container in ML")
    changeDirection = models.BooleanField(default=False)
    pumpSpeed = models.IntegerField(default=60, help_text="The amount pumped in 1 minut")
    pumpSteps = models.IntegerField(default=2500, help_text="Steps for pumping 1ML")
    calibrateValue = models.FloatField(default=50, help_text="Total dosed while calibrating")


    def __str__(self):
        return self.doseName
    
    class Meta:
        ordering = ['doseName']

class JobExternal(models.Model):
    jobToRun = models.ForeignKey(DoseDefinition, on_delete=models.CASCADE)
    jobStatus= models.CharField(max_length=20, default='Queued')
    timeStamp = models.DateTimeField(default=datetime.now)
    JOB_INVOCATION=(('SCHEDULED','SCHEDULED'),('MANUAL','MANUAL'))
    jobCause = models.CharField(max_length=10, choices=JOB_INVOCATION, default='MANUAL',null=True)
    amount = models.FloatField(default=5.0, validators=[MinValueValidator(0),MaxValueValidator(65),])

    def __str__(self):
        return self.jobToRun.doseName + '/' + str(self.timeStamp)

    class Meta:
        ordering = ['timeStamp']

class DoseSchedule(models.Model):
    doseToSchedule=models.CharField(max_length=40,null=True,blank=False,default='Dummy')
    enableSchedule = models.BooleanField(default=True)  
    DAYS_TO_RUN = (('Everyday','Everyday'),('2day','Every 2 days'),('3day','Every 3 days'),('4day','Every 4 days'),('5day','Every 5 days'),('10day','Every 10 days'),
                   ('Sunday', 'Every Sunday'), ('Monday', "Every Monday"), ('Tuesday', "Every Tuesday"), ('Wednesday', 'Every Wednesday'),
                   ('Thursday', "Every Thursday"), ('Friday', 'Every Friday'), ('Saturday', 'Every Saturday'),
                   ('14day','Every 2 weeks'),('21day','Every 3 weeks'),('28day','Every 4 weeks'),('Never','Never'))
    daysToRun = models.CharField(max_length=10, choices=DAYS_TO_RUN, default='Never',null=True)
    startTime = models.TimeField(default='00:00')
    endTime = models.TimeField(default='23:59')
    dailyDosage = models.IntegerField(default=0, validators=[MinValueValidator(0),MaxValueValidator(50000)])
    dailyNumberOfDosage = models.IntegerField(default=0, validators=[MinValueValidator(0),MaxValueValidator(1440)])
    amountPerDose = models.FloatField(default=5.0, validators=[MinValueValidator(0),MaxValueValidator(65),])
    hoursToRun = models.TextField(blank=True)

    def __str__(self):
        return self.doseToSchedule

    class Meta:
        ordering = ['doseToSchedule']


class JobEntry(models.Model):  #This field is used for display and no instances exist in the db
    jobName = models.CharField(max_length=40)
    jobText = models.CharField(max_length=40)
    jobAction = models.CharField(max_length=40)
    timeStamp = models.DateTimeField(default=datetime.now)
    jobIndex = models.IntegerField(default=0)

    def __str__(self):
        return self.jobName + '/' + str(self.timeStamp)

    class Meta:
        ordering = ['timeStamp']
        
    
  