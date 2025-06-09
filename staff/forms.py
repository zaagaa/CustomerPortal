from django import forms
from .models import StaffLeave

class StaffLeaveForm(forms.ModelForm):
    class Meta:
        model = StaffLeave
        fields = ['leave_date', 'leave_type', 'reason']
        widgets = {
            'leave_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'leave_type': forms.Select(attrs={'class': 'form-control'}),
        }
