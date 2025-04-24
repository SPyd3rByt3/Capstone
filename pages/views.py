from django.shortcuts import render
from .forms import ContactForm
from django.core.mail import send_mail

# Create your views here.

from django.shortcuts import render

def home(request):
    return render(request, 'base.html')

def about(request):
    return render(request, 'about.html')

def projects(request):
    # Placeholder projects page
    return render(request, 'projects.html')


def testing_view(request):
    return render(request, 'pages/test.html')  # Render the template with the given request

def about_view(request):
    return render(request, 'pages/about.html') #same as above for the ABOUT page

def contact_view(request):
    if request.method == "POST":

        # validate and send email
        form = ContactForm(request.POST)
        if form.is_valid():
            print("Valid data")

            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"] #emails are sent via SMTP-server like GMAIL as a sender for valid EMAIL!
            message = form.cleaned_data["message"]

            message_body = f"This is an email from your portfolio\nName:{name}\nEmail:{email}\nMessage:\n{message}"

            send_mail(
                "Email from Portfolio",
                message,
                email,
                ['dailydoseofseth@gmail.com'] # list of email addresses to send to  <---WHO should receive the email!
            )


        else:
            print("Invalid data")
    else:
        # DISPLAY THE FORM/page
        form = ContactForm()

    return render(request, 'pages/contact.html', {"form": form})