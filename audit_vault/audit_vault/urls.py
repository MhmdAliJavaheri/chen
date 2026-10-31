from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # No admin UI is required, but keeping the path for completeness
    path('admin/', admin.site.urls),
    # All ledger endpoints are under /api/v1/
    path('api/v1/', include('ledger.urls')),
]
