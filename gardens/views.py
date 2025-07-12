from django.shortcuts import render
from django.http import HttpResponse

# Temporary views to prevent URL errors

def garden_list(request):
    return HttpResponse("Garden list page - coming soon!")

def garden_create(request):
    return HttpResponse("Create garden page - coming soon!")

def garden_detail(request, pk):
    return HttpResponse(f"Garden {pk} detail page - coming soon!")

def garden_edit(request, pk):
    return HttpResponse(f"Edit garden {pk} page - coming soon!")

def garden_delete(request, pk):
    return HttpResponse(f"Delete garden {pk} page - coming soon!")

def plant_library(request):
    return HttpResponse("Plant library page - coming soon!")

def plant_create(request):
    return HttpResponse("Create plant page - coming soon!")

def plant_edit(request, pk):
    return HttpResponse(f"Edit plant {pk} page - coming soon!")

def plant_delete(request, pk):
    return HttpResponse(f"Delete plant {pk} page - coming soon!")