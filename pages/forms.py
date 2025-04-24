from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=200)
    email = forms.CharField(max_length=200, widget=forms.TextInput(attrs={"type": "email"}))
    message = forms.CharField(widget=forms.Textarea())