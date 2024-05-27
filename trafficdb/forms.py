from django import forms
from .models import QueueStatus, QueueLength

class QueueStatusForm(forms.ModelForm):
    class Meta:
        model = QueueStatus
        fields = ['queueLength']  # Assuming 'queueLength' is a field in QueueLength model
