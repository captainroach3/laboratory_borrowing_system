from django.urls import path
from .views import *

urlpatterns = [
    path('transactions/', TransactionList.as_view()),
]