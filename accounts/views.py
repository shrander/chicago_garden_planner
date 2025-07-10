from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView,
    PasswordResetView, PasswordResetConfirmView
)
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm,
    UserProfileForm, CaseInsensitiveAuthenticationForm
)
from .models import UserProfile

class SignUpView(CreateView):
    """User reg view"""
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self,form):
        response = super().form_valid(form)
        # log the user in after successful reg
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        messages.success(self.request, 'Welcome to your garden planner')
        return response
    
class CustomLoginView(LoginView):
    """Custom login view with case-insensitive username"""
    form_class = CaseInsensitiveAuthenticationForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome Back, {form.get_user().get_short_name() or form.get_user().username}!")
        return super().form_valid(form)
    
class CustomPasswordChangeView(PasswordChangeView):
    """Password change view with custom template and success message"""
    template_name = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        messages.success(self.request, 'Your password has been successfully changed.')
        return super().form_valid(form)
    
@login_required
def profile_view(request):
    """display user profile"""
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'profile': request.user.profile
    })

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile information"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user.profile # type: ignore
    
    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated')
        return super().form_valid(form)

class AccountUpdateView(LoginRequiredMixin, UpdateView):
    """Update user account info"""
    form_class = CustomUserChangeForm
    template_name = 'accounts/account_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset = None): # type: ignore
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Your account info has been updated')
        return super().form_valid(form)

@login_required
def dashboard_view(request):
    """
    User dashboard showing their gardens
    """
    user_gardens = request.user.gardens.all()
    total_plants = sum(garden.get_plant_count() for garden in user_gardens)

    context = {
        'user_gardens': user_gardens[:5], # show latest 5 gardens
        'total_gardens': user_gardens.count(),
        'total_plants': total_plants,
    }
    return render(request, 'accounts/dashboard.html', context)
