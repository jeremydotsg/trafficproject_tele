from django import forms
from .models import QueueStatus, QueueLength
from django.forms.utils import ErrorList
from django_recaptcha.widgets import ReCaptchaV3
from django_recaptcha.fields import ReCaptchaField
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
import logging

import sys
import os

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger('trafficdb')
class QueueStatusForm(forms.ModelForm):
    if os.getenv('ENVIRONMENT') in ['prod']:
        captcha = ReCaptchaField(widget = ReCaptchaV3(action='queue_update'), error_messages={
                'required': 'CAPTCHA Invalid.',
                'invalid': 'CAPTCHA Invalid.',
                'captcha_invalid': 'CAPTCHA Invalid.'
            })
    class Meta:
        model = QueueStatus
        fields = ['queueLength']  # Assuming 'queueLength' is a field in QueueLength model
    def __init__(self, *args, **kwargs):
        super(QueueStatusForm, self).__init__(*args, **kwargs)
        self.fields['queueLength'].queryset = QueueLength.objects.filter(queueTypeDisplay=True)
    def clean(self):
        queue_ip = get_remote_ip(self)
        if os.getenv('ENVIRONMENT') in ['prod'] and QueueStatus.has_reached_update_limit(queue_ip):
            logger.info('QueueStatusForm :: IP > 5 times')
            raise ValidationError('Too many updates, try again later.')

class DivErrorList(ErrorList):
    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ''
        return mark_safe('<div class="errorlist error alert alert-danger mt-1">%s</div>' % ''.join(['<div class="">%s</div>' % e for e in self]))
    
def get_remote_ip(self):
        f = sys._getframe()
        while f:
            request = f.f_locals.get("request")
            if request:
                real_ip = request.META.get("X_REAL_IP", "")
                remote_ip = request.META.get("REMOTE_ADDR", "")
                forwarded_ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
                logger.info('Forms - Real IP: ' + str(real_ip) + ', Remote IP: ' + str(remote_ip) + ', Forwarded IP: ' + str(forwarded_ip))
                ip = None
                if not real_ip:
                    if not forwarded_ip:
                        ip = remote_ip
                    else:
                        ip = forwarded_ip
                else:
                    ip = real_ip
                return ip
            f = f.f_back