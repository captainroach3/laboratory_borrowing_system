from django.urls import path
from .views import *

urlpatterns = [
    path('inventory/', InventoryList.as_view()),
]