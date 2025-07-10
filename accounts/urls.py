from django.urls import path
from django.contrib.auth.views import (
    LogoutView, 
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from . import views

app_name = 'accounts'

urlpatterns = [
    # auth
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='gardens:garden_list'), name='logout'),
    
    # profile and account management 
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('account/edit/', views.AccountUpdateView.as_view(), name='account_edit'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # password management 
    path('password/change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', 
         PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             success_url='/accounts/password/reset/done/'
         ),
         name='password_reset'),
    path('password/reset/done/',
         PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password/reset/<uuid64>/<token>/',
         PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/accounts/password/reset/complete/'
         ),
         name='password_reset_confirm'),
    path('password/reset/complete/',
         PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]