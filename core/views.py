# AutoAggregator/core/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def homepage_view(request):
    return render(request, 'homepage.html')

@login_required # <--- Decorator to ensure only logged-in users can access
def user_profile_view(request): # <--- ADD THIS NEW VIEW FUNCTION
    return render(request, 'profile.html', {'user': request.user})