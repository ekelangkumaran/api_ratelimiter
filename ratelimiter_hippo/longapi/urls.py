from django.urls import path,re_path

from . import views

urlpatterns = [
            path('', views.index, name='index'),
            re_path(r'^firstapi/', views.firstapi, name='firstapi'),
            re_path(r'^secondapi/', views.secondapi, name='secondapi'),
            re_path(r'^thirdapi/', views.thirdapi, name='thirdapi'),
            re_path(r'^fourthapi/', views.fourthapi, name='fourthapi')
            
            ]
