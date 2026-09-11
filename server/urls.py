from django.urls import path, include

urlpatterns = [
    path('api/', include('users.urls')),
    path('api/', include('staff.urls')),
    path('api/', include('category.urls')),
    path('api/', include('inventory.urls')),
    path('api/', include('transactions.urls')),
]