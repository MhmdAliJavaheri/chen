from django.urls import path
from ledger import views

urlpatterns = [
    path('ledger/', views.create_entry_view, name='create_entry'),
    path('ledger/<int:entry_id>/', views.retrieve_entry_view, name='retrieve_entry'),
    path('ledger/latest/', views.latest_entry_view, name='latest_entry'),
    path('ledger/verify/', views.verify_chain_view, name='verify_chain'),
]
