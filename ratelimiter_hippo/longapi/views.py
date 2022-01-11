from django.shortcuts import render
from django.http import JsonResponse
from time import sleep
# Create your views here
def index(request):
    print("Entered the view",request)
    #sleep(5)
    message = "Hello, world. You have hit the long api that takes 5 secs to process."
    return JsonResponse({'success':'true','message': message}, status=200)
    
def firstapi(request):
    print("Entered the firstapi view",request)
    #sleep(5)
    message = "Hello, world. You have hit the firstapi view."
    return JsonResponse({'success':'true','message': message}, status=200)

def secondapi(request):
    print("Entered the secondapi view",request)
    #sleep(5)
    message = "Hello, world. You have hit the secondapi view."
    return JsonResponse({'success':'true','message': message}, status=200)

def thirdapi(request):
    print("Entered the thirdapi view",request)
    #sleep(5)
    message = "Hello, world. You have hit the thirdapi view."
    return JsonResponse({'success':'true','message': message}, status=200)

def fourthapi(request):
    print("Entered the fourthapi view",request)
    #sleep(5)
    message = "Hello, world. You have hit the fourthapi view."
    return JsonResponse({'success':'true','message': message}, status=200)
    