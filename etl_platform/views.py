from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    """
    Simple home page view that displays welcome message.
    """
    return render(request, 'home.html')
