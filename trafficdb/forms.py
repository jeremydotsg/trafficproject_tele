from django import forms
from .models import QueueStatus, QueueLength
from django.forms.utils import ErrorList
from django_recaptcha.widgets import ReCaptchaV3
from django_recaptcha.fields import ReCaptchaField

class QueueStatusForm(forms.ModelForm):
    captcha = ReCaptchaField(
    widget = ReCaptchaV3(
            action='queue_update'
            )
    )
    class Meta:
        model = QueueStatus
        fields = ['queueLength']  # Assuming 'queueLength' is a field in QueueLength model
        
class DivErrorList(ErrorList):
    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ''
        return '<div class="errorlist">%s</div>' % ''.join(['<div class="error alert alert-danger mt-1">%s</div>' % e for e in self])