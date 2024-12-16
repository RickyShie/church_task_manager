from django import forms
from .models import RoleAssignment

class RoleAssignmentForm(forms.ModelForm):
    class Meta:
        model = RoleAssignment
        fields = ['schedule', 'role', 'person']
        widgets = {
            'schedule': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'person': forms.Select(attrs={'class': 'form-control'}),
        }