from django.shortcuts import render
from django.http import HttpResponse

def frontend_home(request):
    return HttpResponse("Frontend app home page")
