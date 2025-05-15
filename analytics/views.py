from django.shortcuts import render
from django.http import HttpResponse

def analytics_home(request):
    return HttpResponse("Analytics app home page")
