from django.urls import path
from .views import *

urlpatterns = [
    path('categories/', CategoryListCreate.as_view()),
]