from django.urls import path
from . import views

app_name = 'gardens'

urlpatterns = [
    # garden views
    path('', views.garden_list, name='garden_list'),
    path('create/', views.garden_create, name='garden_create'),
    path('<int:pk>/', views.garden_detail, name='garden_detail'),
    path('<int:pk>/edit/', views.garden_edit, name='garden_edit'),
    path('<int:pk>/delete/', views.garden_delete, name='garden_delete'),
    path('<int:pk>/duplicate/', views.garden_duplicate, name='garden_duplicate'),
    path('<int:pk>/clear/', views.garden_clear, name='garden_clear'),
    path('<int:pk>/save-layout/', views.garden_save_layout, name='garden_save_layout'),
    path('<int:pk>/update-name/', views.garden_update_name, name='garden_update_name'),
    path('<int:pk>/ai-suggest/', views.garden_ai_assistant, name='garden_ai_assistant'),

    # plant views
    path('plants/', views.plant_library, name='plant_library'),
    path('plants/create/', views.plant_create, name='plant_create'),
    path('plants/<int:pk>/', views.plant_detail, name='plant_detail'),
    path('plants/<int:pk>/edit/', views.plant_edit, name='plant_edit'),
    path('plants/<int:pk>/delete/', views.plant_delete, name='plant_delete'),
]