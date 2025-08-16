# AutoAggregator/cars/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.db.models import Max
from django.utils import timezone
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Car, Review, CarView, CarSave, SearchQuery
from .serializers import (
    CarSerializer, ReviewSerializer,
    CarViewSerializer, CarSaveSerializer, SearchQuerySerializer,
    UserSerializer,
    UserRegistrationSerializer
)

User = get_user_model()

class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = {
        'make': ['exact', 'icontains'],
        'model': ['exact', 'icontains'],
        'year': ['exact', 'gte', 'lte'],
        'body_type': ['icontains'],
        'msrp_starting': ['gte', 'lte'],
        'overall_rating': ['gte', 'lte'],
        'release_date': ['gte', 'lte']
    }

    search_fields = ['make', 'model', 'trim', 'engine_type', 'body_type', 'ai_insight_summary']
    ordering_fields = ['make', 'model', 'year', 'msrp_starting', 'overall_rating', 'release_date']

    @action(detail=False, methods=['get'])
    def weekly_recommendation(self, request):
        """
        Returns a single car as the AI's weekly recommendation.
        MVP Logic: Pick the highest-rated car from the most recent year with available data.
        """
        recommended_car = None

        latest_year_with_ratings = Car.objects.filter(overall_rating__isnull=False).aggregate(Max('year'))['year__max']

        if latest_year_with_ratings:
            candidate_cars = Car.objects.filter(
                year=latest_year_with_ratings,
                overall_rating__isnull=False
            ).order_by('-overall_rating', '-release_date')

            if candidate_cars.exists():
                recommended_car = candidate_cars.first()

        if recommended_car:
            serializer = self.get_serializer(recommended_car)
            return Response(serializer.data)
        else:
            return Response({"detail": "No suitable recommendation found at this time."}, status=404)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def personalized_recommendations(self, request):
        """
        Returns personalized car recommendations for the authenticated user.
        Falls back to content-based or top-rated if no user interactions.
        """
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication required for personalized recommendations."}, status=401)

        recommendations = []
        if user.car_views.exists() or user.saved_cars.exists() or user.search_queries.exists():
            from cars.recommender_utils import get_personalized_recommendations # Import here to avoid circular dependency
            recommendations = get_personalized_recommendations(user, num_recommendations=5)
            print(f"DEBUG: Collaborative filtering recommendations for {user.username}: {[car.model for car in recommendations]}")

        if not recommendations:
            from cars.recommender_utils import get_simple_content_based_recommendations # Import here
            print(f"DEBUG: Falling back to content-based recommendations for {user.username}")
            recommendations = get_simple_content_based_recommendations(num_recommendations=5)

        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        'car': ['exact'],
        'source_name': ['exact', 'icontains'],
        'sentiment_classification': ['exact'],
        'review_date': ['exact', 'gte', 'lte'],
    }
    ordering_fields = ['review_date', 'source_rating', 'sentiment_compound_score']
    search_fields = ['content', 'reviewer_name']

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CarViewViewSet(viewsets.ModelViewSet):
    queryset = CarView.objects.all()
    serializer_class = CarViewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self): # Add this method
        user = self.request.user
        if user.is_authenticated:
            return CarView.objects.filter(user=user)
        return CarView.objects.none() # Return empty queryset for anonymous users

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None, view_date=timezone.now())


class CarSaveViewSet(viewsets.ModelViewSet):
    queryset = CarSave.objects.all()
    serializer_class = CarSaveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self): # Add this method
        user = self.request.user
        if user.is_authenticated:
            return CarSave.objects.filter(user=user)
        return CarSave.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, save_date=timezone.now())


class SearchQueryViewSet(viewsets.ModelViewSet):
    queryset = SearchQuery.objects.all()
    serializer_class = SearchQuerySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self): # Add this method
        user = self.request.user
        if user.is_authenticated:
            return SearchQuery.objects.filter(user=user)
        return SearchQuery.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None, timestamp=timezone.now())

# New: User Registration API View
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        login(request, user) # Log the user in immediately after registration
        return Response({
            "message": "User registered and logged in successfully!",
            "user_id": user.id,
            "username": user.username
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# New: User Login API View
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user) # This establishes the Django session
        return Response({
            "message": "Login successful!",
            "user_id": user.id,
            "username": user.username
        }, status=status.HTTP_200_OK)
    else:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

# New: User Logout API View
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated]) # Only authenticated users can log out
def user_logout(request):
    logout(request) # This destroys the Django session
    return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)