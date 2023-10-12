from django import forms
from django.contrib.auth.forms import AuthenticationForm

from userprofile.models import UserProfile


class RegisterForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ['email', 'name', 'dob', 'doj', 'gender', 'designation', 'manager', 'pic', 'password']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'doj': forms.DateInput(attrs={'type': 'date'}),
            'pic': forms.FileInput(attrs={'class': 'form-control py-2', 'type': 'file', 'id': 'formFile'}),
            'password': forms.PasswordInput(),
            'gender': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'designation': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }
    
    def save(self):
        data = self.cleaned_data
        password = data.pop('password', None)
        user = UserProfile(**data)
        user.set_password(password)
        user.save()
        return user


class CustomAuthentication(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'text', 'name': 'email', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'password', 'name': 'password', 'placeholder': 'Password'}))


class UserDetailsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['id', 'name', 'dob', 'doj', 'gender', 'designation', 'manager', 'pic']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'doj': forms.DateInput(attrs={'type': 'date','class': 'form-control'}),
            'pic': forms.FileInput(attrs={'class': 'form-control py-2', 'type': 'file', 'id': 'formFile'}),
            'gender': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'designation': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'manager':forms.TextInput(attrs={'class': 'form-control'}),
        }
