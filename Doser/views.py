from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms.models import modelformset_factory
from django.http import HttpResponse,Http404,HttpResponseRedirect

from .models import DoserExternal,DoseDefinition,DoseSchedule,JobExternal,DoseResultsExternal,JobEntry
from DoserCore import getBasePath
import glob
import os
import rpyc
import traceback
import time


from .forms import ScheduleForm,DoserForm,DoseDefinitionForm,CalibrationForm

def sendCmdToDoser(cmd):
    try:
        c=rpyc.connect("localhost", 18862)
        res=c.root.doserOperation(cmd)
        print('Sent: ' + cmd) 
    except:
        print('Cmd: ' + cmd + 'failure reported') 

def index(request,formResult):
    return home(request,formResult) 

def navigate(request):
    jumpLoc=None
    try:
        whereToGo=request.GET['navButton']
        sendCmdToDoser('CLEAR') 
        jumpLoc="/doser/" + whereToGo + "/"
        return jumpLoc
    except:
        pass
    

@login_required
def home(request,formResult):
    pageName='Home'
    formToProcess=None
    if request.method=='GET':
        jumpLoc=navigate(request) 
        if not jumpLoc is None:
            return redirect(jumpLoc)     

    if request.method=='POST':
        try:
            doseSequenceNameToRun=request.POST['doseName']
            lastStepSize=request.POST['stepSize']
            formToProcess = 'queueJob'
        except:
            pass
        try:
            updateQueueAction=request.POST['jobAction']
            formToProcess = 'updateQueue'
        except:
            pass

        if formToProcess == 'queueJob':
            try:
                te=DoserExternal.objects.get(pk=1)
                newJob=JobExternal()
                newJob.jobToRun=DoseDefinition.objects.get(doseName=doseSequenceNameToRun)
                newJob.amount=lastStepSize
                newJob.save()
                            
                #return HttpResponseRedirect('run')
            except: 
                traceback.print_exc()
                print('Key error:' + doseSequenceNameToRun)
        if formToProcess == 'updateQueue':
            lastStepSize='1'
            print(updateQueueAction)
            updateIndex=updateQueueAction.split('-')
            updateID=int(updateIndex[1])
            if updateIndex[0]=='REMOVE':
                try:
                    JobExternal.objects.get(pk=updateID).delete()
                except:
                    pass
            elif updateIndex[0]=='DELETE':
                DoseResultsExternal.objects.get(pk=updateID).delete()
            elif updateIndex[0]=='CANCEL':
                sendCmdToDoser('HOME/Abort')
            else:
                print('Error, unknown action')
                #return HttpResponse("")

    else:
        lastStepSize='1'
    doseList=DoseDefinition.objects.all()
    jobQueue=JobExternal.objects.all()
    jobList=[]
    for job in reversed(jobQueue):
        newJob=JobEntry()
        newJob.jobName=job.jobToRun.doseName
        newJob.jobText=job.jobStatus
        newJob.jobAction= 'REMOVE'
        if job.jobStatus=='Running':
            newJob.jobAction='CANCEL'
        newJob.timeStamp=job.timeStamp
        newJob.jobIndex=job.pk
        jobList.append(newJob)
    maxResultsToShow=10
    currentResult=0
    resultsQueue=DoseResultsExternal.objects.all()
    for result in reversed(resultsQueue):
        if currentResult>=maxResultsToShow:
            break
        newJob=JobEntry()
        newJob.jobName=result.dosePerformed
        if result.status=='Completed':
            if result.results is None:
                newJob.jobText ='Failed'
            else:
                newJob.jobText='Completed (' + str(round(result.results,2)) + ')'
        elif result.status=='Failed':
            newJob.jobText='Failed'
        else:
            newJob.jobText='Unknown'
        newJob.jobAction='DELETE'
        newJob.timeStamp=result.datetimePerformed
        newJob.jobIndex=result.pk
        jobList.append(newJob)
        currentResult+=1
    stepSizeList=['1','5','10','30','90']
    context={'pageName':pageName,'doseList':doseList,'jobList':jobList,'lastStepSize':lastStepSize,'stepSizeList':stepSizeList}
    return render(request,'doser/home.html',context)


@login_required
def history(request,formResult):
    pageName='History'
    if request.method=='GET':
        jumpLoc=navigate(request) 
        if not jumpLoc is None:
            return redirect(jumpLoc)    
    if request.method=='POST':
        dose="All"
        cmd=request.POST['display']
        dose=request.POST['toDisplay']
        sendCmdToDoser('Train/' + cmd + '/' + dose)
    else:
        dose="All"
    doseList=DoseDefinition.objects.all()
    currentlySelected=dose
    if currentlySelected is None or currentlySelected=="All":
        resultsList=DoseResultsExternal.objects.all()
    else:
        resultsList=DoseResultsExternal.objects.filter(dosePerformed=currentlySelected)
    context={'pageName':pageName,'currentlySelected':currentlySelected,'doseList':doseList,'resultsList':resultsList}
    return render(request,'doser/history.html',context)


@login_required
def control(request,formResult):
    pageName='Control'
    if request.method=='GET':
        jumpLoc=navigate(request) 
        if not jumpLoc is None:
            return redirect(jumpLoc)    
    if request.method=='POST':
        try:
            cmd=request.POST['button']
            sendCmdToDoser('CONTROL/' + cmd + '/')

        except:
            pass
        try:
            cmd=request.POST['diag-button']
            sendCmdToDoser('DIAGNOSTIC/' + cmd + '/')
        except:
            pass

        try:
            cmd=request.POST['diag-button']
            sendCmdToDoser('DIAGNOSTIC/' + cmd + '/')
        except:
            pass

    context={'pageName':pageName}
    return render(request,'doser/control.html',context)

@login_required
def calibrate(request,formResult):
    pageName='Calibration'
    if request.method=='GET':
        jumpLoc=navigate(request) 
        if not jumpLoc is None:
            return redirect(jumpLoc)    
    

    if request.method=='POST':
        DoserCalibrationFormSet=modelformset_factory(DoseDefinition, form=CalibrationForm,extra=0)
        doserCalFormSet=DoserCalibrationFormSet(request.POST)
        adminAction=request.POST["actionButton"]

        if (doserCalFormSet.is_valid()):
            Update='UPDATE'
            if Update in adminAction:
                doserCalFormSet.save() 
                sendCmdToDoser('SCHEDULE/reloadSchedules')           
                messages.success(request,'Schedules updated')
        else:
            messages.error(request,doserCalFormSet.errors)

        try:
            cmd=request.POST['actionButton']
            sendCmdToDoser('CALIBRATE/' + cmd + '/')

        except:
            pass
    else:     
        DoserCalibrationFormSet=modelformset_factory(DoseDefinition, form=CalibrationForm,extra=0)
        doserCalFormSet=DoserCalibrationFormSet()
    context={'pageName':pageName,'doserCalFormSet':doserCalFormSet}
    return render(request,'doser/calibrate.html',context)


@login_required
def schedule(request,formResult):
    pageName='Setup Schedules'
    if request.method=='GET':
        jumpLoc=navigate(request) 
        if not jumpLoc is None:
            return redirect(jumpLoc)    
    if request.method=='POST':
        ScheduleFormSet=modelformset_factory(DoseSchedule, form=ScheduleForm,extra=0)
        schedFormSet=ScheduleFormSet(request.POST)
        try:
            whatToDoWithFormset=request.POST['actionButton']
        except:
            whatToDoWithFormset='CANCEL'
        if whatToDoWithFormset=='CANCEL':
            schedFormSet=ScheduleFormSet()
            messages.success(request,'Changes Reset')
        if (schedFormSet.is_valid()):
            if whatToDoWithFormset=='UPDATE':
                schedFormSet.save() 
                sendCmdToDoser('SCHEDULE/reloadSchedules')           
                messages.success(request,'Schedules updated')
                time.sleep(0.2)
                ScheduleFormSet=modelformset_factory(DoseSchedule, form=ScheduleForm,extra=0)
                schedFormSet=ScheduleFormSet()
        else:
            messages.error(request,schedFormSet.errors)
    else:
        ScheduleFormSet=modelformset_factory(DoseSchedule, form=ScheduleForm,extra=0)
        schedFormSet=ScheduleFormSet()
    context={'pageName':pageName,'schedFormSet':schedFormSet}
    return render(request,'doser/schedule.html',context)
    

@login_required
def dosedef(request,formResult):
    pageName='Define Dose Sequences'
    if request.method=='GET':
        jumpLoc=navigate(request) 
        if not jumpLoc is None:
            return redirect(jumpLoc)    
    if request.method=='POST':
        try:
            doseListButtonStr=request.POST['doseListAction']
            doseAction=doseListButtonStr.split(' ')[0]
            doseToChange=doseListButtonStr[len(doseAction)+1:]
        except:
            doseAction=None
            doseToChange=None
        try:
            doseButtonStr=request.POST['doseAction']
        except:
            doseButtonStr=None
        try:
            originalDoseName=request.POST['originalDoseName']
        except:
            originalDoseName=None
        if doseAction=='EDIT':
            doseBeingEdited=DoseDefinition.objects.get(doseName=doseToChange)
            doseDef=DoseDefinitionForm(instance=doseBeingEdited)
            originalDoseName=doseToChange
            context={'originalDoseName':originalDoseName,'doseToChange':doseToChange,'doseDef':doseDef}
        elif doseAction=='DELETE':
            doseBeingEdited=DoseDefinition.objects.get(doseName=doseToChange).delete()
            doseDefList=DoseDefinition.objects.all()
            try:
                DoseSchedule.objects.get(doseToSchedule=doseToChange).delete()
                sendCmdToDoser('RELOAD/DoseDefs')           
            except:
                pass
            context={'doseDefList':doseDefList}
            messages.success(request,'Dose ' + doseToChange + ' deleted')
        elif doseButtonStr=='CREATE NEW':
            doseDef=DoseDefinitionForm()
            doseToChange='New Dose'
            originalDoseName='New Dose'
            context={'originalDoseName':originalDoseName,'doseToChange':doseToChange,'doseDef':doseDef}
        elif doseButtonStr=='Save':
            if originalDoseName=='New Dose':
                doseDef=DoseDefinitionForm(request.POST)
            else:
                try:
                    originalDoseDef=DoseDefinition.objects.get(doseName=originalDoseName)
                    doseDef=DoseDefinitionForm(request.POST,instance=originalDoseDef)
                except:
                    doseDef=DoseDefinitionForm(request.POST)
            if doseDef.is_valid():                
                doseDefToSave=doseDef.save(commit=False)
                retryDoseSetup=False
                newDoseName=doseDefToSave.doseName

                #We saved the new or changed dose def.  Now update any schedule objects
                doseDefToSave.save()
                doseDef.save_m2m()
                sendCmdToDoser('RELOAD/DoseDefs')           
                messages.success(request,'Dose ' + doseDefToSave.doseName + ' saved')
                if originalDoseName=='New Dose':
                    newDoseSched=DoseSchedule()
                    newDoseSched.doseToSchedule=newDoseName
                    newDoseSched.save()
                else:
                    if originalDoseName==newDoseName:
                        pass  #New and old name the same, no need to do anything
                    else:
                        try:
                            oldDoseSched=DoseSchedule.objects.get(doseToSchedule=originalDoseName)
                        except:
                            oldDoseSched=DoseSchedule()
                        oldDoseSched.doseToSchedule=newDoseName
                        oldDoseSched.save()                    
                doseDefList=DoseDefinition.objects.all()
                if retryDoseSetup:
                    context={'originalDoseName':newDoseName,'doseToChange':newDoseName,'doseDef':doseDef}
                else:    
                    context={'pageName':pageName,'doseDefList':doseDefList}
            else:
                doseToChange=originalDoseName
                context={'pageName':pageName,'originalDoseName':originalDoseName,'doseToChange':doseToChange,'doseDef':doseDef}
        elif doseButtonStr=='Cancel':
            return redirect('/doser/dosedef/')
    else:
        doseDefList=DoseDefinition.objects.all()
        context={'pageName':pageName,'doseDefList':doseDefList}
    return render(request,'doser/dosedef.html',context)


@login_required
def logs(request,formResult):
    pageName='Display Logs'
    if request.method=='GET':
        jumpLoc=navigate(request) 
        if not jumpLoc is None:
            return redirect(jumpLoc)    
    logToDisplay="Info"
    logPath=getBasePath() + 'Logs'
    if request.method=='POST':
        try:
            logToDisplay=request.POST["radioLogDisplay"]
        except:
            pass
    print(logToDisplay)
    scrollLog=""
    if logToDisplay=='Info':
        try:
            f=open(logPath + '/' + 'doser.log.1','r')
            scrollLog=f.read()
            f.close()
            f=open(logPath + '/' + 'doser.log','r')
            scrollLog=scrollLog + f.read()
            f.close()
        except:
            traceback.print_exc()
    else:
        try:
            f=open(logPath + '/' + 'debug.log.1','r')
            scrollLog=f.read()
            f.close()
            f=open(logPath + '/' + 'debug.log','r')
            scrollLog=scrollLog + f.read()
            f.close()
        except:
            traceback.print_exc()
    context={'pageName':pageName,'logToDisplay':logToDisplay,'scrollLog':scrollLog}
    return render(request,'doser/logs.html',context)
    
@login_required
def admin(request,formResult):
    pageName='Administrative Setup'
    if request.method=='GET':
        jumpLoc=navigate(request) 
        if not jumpLoc is None:
            return redirect(jumpLoc)    
    if request.method=='POST':
        adminAction=request.POST["actionButton"]
        if adminAction=='CANCEL':
            messages.success(request,'Changes reverted')
            adminInfo=DoserExternal.objects.get(pk=1)
            doserAdminForm=DoserForm(instance=adminInfo)
        elif adminAction=="Test Telegram": 
            try:
                adminInfo=DoserExternal.objects.get(pk=1)
                doserAdminForm=DoserForm(request.POST,instance=adminInfo)
                partialdata=doserAdminForm.save(commit=False)
                newKey=partialdata.telegramBotToken
                sendCmdToDoser('ALARMS/testTelegram/' + newKey)
                messages.success(request,'Test Message Sent')
            except:
                traceback.print_exc()
        elif adminAction=='UPDATE':
            adminInfo=DoserExternal.objects.get(pk=1)
            doserAdminForm=DoserForm(request.POST,instance=adminInfo)
            try:
                doserAdminForm.save()
                messages.success(request,'Changes saved. Will take affect after program restarted')
            except:
                traceback.print_exc()
    else:           
        adminInfo=DoserExternal.objects.get(pk=1)
        doserAdminForm=DoserForm(instance=adminInfo)
    context={'pageName':pageName,'doserAdminForm':doserAdminForm}
    return render(request,'doser/admin.html',context)



