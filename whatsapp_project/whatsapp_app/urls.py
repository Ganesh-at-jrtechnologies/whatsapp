from django.urls import path
from . import views

urlpatterns = [
    path('',views.dashboard,name='dashboard'),
    path('party/master/',views.party_master,name='party_master'),
    path('party/master/list/',views.list_party_master,name='list_party_master'),
    path('party/outstanding/',views.party_outstanding,name='party_outstanding'),
]
