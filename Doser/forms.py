from django import forms

from .models import DoseSchedule,DoseDefinition,DoserExternal

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = DoseSchedule
        exclude=()
        hidden=('doseToSchedule')
#        widgets = {
#            'doseToSchedule': Textarea(attrs={'cols': 80, 'rows': 20}),
#        }
    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['doseToSchedule'].widget.attrs['readonly'] = True
            self.fields['hoursToRun'].help_text="Control Select for more than on hour"


           
class DoseDefinitionForm(forms.ModelForm):
    class Meta:
        model = DoseDefinition
        exclude=('pumpSpeed','pumpSteps','totalDoseAfterStartup','calibrateValue')
#        widgets = {
#            'testToSchedule': Textarea(attrs={'cols': 80, 'rows': 20}),
#        }

class DoserForm(forms.ModelForm):
    class Meta:
        model = DoserExternal
        exclude=()

    def __init__(self, *args, **kwargs):
        super(DoserForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['doserName'].label="Name of the Doser"
            self.fields['doserName'].widget.attrs['title'] = "This is the name of the ReefTankDoser.  It will be sent in notifications"
            self.fields['doserVersion'].label="Software Version"
            self.fields['doserVersion'].widget.attrs['title'] = "This is the software version"
            self.fields['doserVersion'].widget.attrs['readonly'] = True
            self.fields['webPort'].label="WebServer Port"
            self.fields['webPort'].widget.attrs['title'] = "Port that the WebServer Listens On, Must be >1000"
            self.fields['telegramBotToken'].label="Telegram Bot Token"
            self.fields['telegramBotToken'].widget.attrs['title'] = "Set the Telegram Bot Token for sending alarms or reports"
            self.fields['telegramChatID'].label="Telegram Chat ID"
            self.fields['telegramChatID'].widget.attrs['title'] = "Set the Telegram Chat ID for sending alarms or reports"
            self.fields['daysOfResultsToKeep'].label="Days of Historical Results to Keep"
            self.fields['daysOfResultsToKeep'].widget.attrs['title'] = "Enter number of days of old results to keep"
            self.fields['enableConsoleOutput'].label="Enable Console Output"
            self.fields['enableConsoleOutput'].widget.attrs['title'] = "Checking this will cause a verbose stream to be displayed on the SSH program console"
            self.fields['manageDatabases'].label="Manage Databases"
            self.fields['manageDatabases'].widget.attrs['title'] = "Checking this and restarting will give access to the internal databases.  Caution in making changes"
            self.fields['arduino1'].label="Arduino 1 address"
            self.fields['arduino1'].widget.attrs['title'] = "Arduino 1 serial address, something like: /dev/cu.usbmodem101"
            self.fields['arduino2'].label="Arduino 2 address"
            self.fields['arduino2'].widget.attrs['title'] = "Arduino 2 serial address, something like: /dev/cu.usbmodem102"
            self.fields['arduino3'].label="Arduino 3 address"
            self.fields['arduino3'].widget.attrs['title'] = "Arduino 3 serial address, something like: /dev/cu.usbmodem103"
            self.fields['arduino4'].label="Arduino 4 address"
            self.fields['arduino4'].widget.attrs['title'] = "Arduino 4 serial address, something like: /dev/cu.usbmodem104"


class CalibrationForm(forms.ModelForm):
    class Meta:
        model = DoseDefinition
        exclude=('enableDose','amount','Arduino_Choices','arduinoNumber','pumpName','fluidRemainingInML','containerInML','totalDoseAfterStartup','changeDirection','pumpSteps','minimumThreshold')
#        widgets = {
#            'testToSchedule': Textarea(attrs={'cols': 80, 'rows': 20}),
#        }
    def __init__(self, *args, **kwargs):
        super(CalibrationForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['pumpSpeed'].label="Pump Speed"
            self.fields['pumpSpeed'].widget.attrs['title'] = "Total dosed liquid in ML Autotester"
            self.fields['calibrateValue'].label="Calibration amount"
            self.fields['calibrateValue'].widget.attrs['title'] = "Total dosed liquid that is dosed while calibrating"

