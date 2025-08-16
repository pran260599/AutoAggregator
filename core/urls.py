# AutoAggregator/core/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import homepage_view, user_profile_view 
from cars.views import (
    CarViewSet, ReviewViewSet,
    CarViewViewSet, CarSaveViewSet, SearchQueryViewSet,
    UserViewSet,
    register_user, 
    user_login,    
    user_logout    
)
from core.views import homepage_view

router = DefaultRouter()
router.register(r'cars', CarViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'car-views', CarViewViewSet)
router.register(r'car-saves', CarSaveViewSet)
router.register(r'search-queries', SearchQueryViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('', homepage_view, name='homepage'),
    path('api/register/', register_user, name='register_user'), 
    path('api/login/', user_login, name='user_login'),         
    path('api/logout/', user_logout, name='user_logout'),
    path('profile/', user_profile_view, name='user_profile'),
]