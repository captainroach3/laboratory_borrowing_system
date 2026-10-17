from django.urls import path
from .views import *

urlpatterns = [
    path('transactions/', TransactionList.as_view()),
    path('transactions/create/', TransactionCreate.as_view()),
    path('transactions/mine/', MyTransactionList.as_view()),
    path('transactions/<int:pk>/', TransactionDetail.as_view()),
    path('transactions/<int:pk>/approve/', TransactionApprove.as_view()),
    path('transactions/<int:pk>/return/', TransactionReturn.as_view()),
    path('transactions/<int:pk>/delete/', TransactionDelete.as_view()),
]

