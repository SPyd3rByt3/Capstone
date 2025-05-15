from django.shortcuts import render
from django.http import HttpResponse

def core_home(request):
    return HttpResponse("Core app home page")
