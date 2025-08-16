# AutoAggregator/cars/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# Get the active User model (recommended by Django)
User = get_user_model() 

class Car(models.Model):
    # Basic Car Identification
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100) # CORRECTED: Removed redundant models.CharField()
    year = models.IntegerField()
    trim = models.CharField(max_length=100, blank=True, null=True) # e.g., "LE", "XSE"

    # Pricing Information
    msrp_starting = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    msrp_average = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Performance & Efficiency (Specifications)
    engine_type = models.CharField(max_length=100, blank=True, null=True)
    horsepower = models.IntegerField(null=True, blank=True)
    torque = models.IntegerField(null=True, blank=True)
    mpg_city = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    mpg_highway = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    drivetrain = models.CharField(max_length=50, blank=True, null=True)
    body_type = models.CharField(max_length=50, blank=True, null=True)

    # Ratings (Overall/Aggregated from reviews)
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    reliability_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    safety_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    # AI Insights / Aggregated Review Summaries
    ai_insight_summary = models.TextField(blank=True, null=True)
    top_pros = models.JSONField(blank=True, null=True)
    top_cons = models.JSONField(blank=True, null=True)

    # Metadata
    release_date = models.DateField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    # Image URLs
    main_image_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        unique_together = ('make', 'model', 'year', 'trim')
        ordering = ['-year', 'make', 'model']

    def __str__(self):
        return f"{self.year} {self.make} {self.model} {self.trim or ''}".strip()

class Review(models.Model):
    # Link to the Car model
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='reviews')

    # Review Content
    content = models.TextField()

    # Source Information
    source_name = models.CharField(max_length=200)
    source_url = models.URLField(max_length=500, blank=True, null=True)

    # Reviewer Information
    reviewer_name = models.CharField(max_length=100, blank=True, null=True)
    reviewer_id = models.CharField(max_length=100, blank=True, null=True)

    # Raw Rating
    source_upvotes = models.IntegerField(null=True, blank=True)

    # Date of Review
    review_date = models.DateField(null=True, blank=True)
    retrieval_date = models.DateTimeField(auto_now_add=True)

    # Basic AI-derived sentiment for this individual review
    sentiment_compound_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    sentiment_classification = models.CharField(max_length=20, blank=True, null=True)

    # Unique ID from the source system (e.g., Reddit post ID)
    reviewer_id = models.CharField(max_length=255, blank=True, null=True, db_index=True) # db_index for faster lookups.

    class Meta:
        ordering = ['-retrieval_date']
        # IMPORTANT: Add unique_together for robust duplicate prevention
        # This ensures same car + source + unique ID is not duplicated
        unique_together = ('car', 'source_name', 'reviewer_id')
        # If reviewer_id can be null, you might need conditional uniqueness or handle it via code.
        # For Reddit, IDs are unique, so this is good.

    def __str__(self):
        return f"Review for {self.car.year} {self.car.make} {self.car.model} by {self.reviewer_name or 'Anonymous'} from {self.source_name}"

class CarView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='car_views')
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    view_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'car', 'view_date')
        ordering = ['-view_date']

    def __str__(self):
        return f"{self.user.username} viewed {self.car.make} {self.car.model} on {self.view_date.strftime('%Y-%m-%d %H:%M')}"

class CarSave(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_cars')
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    save_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'car')
        ordering = ['-save_date']

    def __str__(self):
        return f"{self.user.username} saved {self.car.make} {self.car.model} on {self.save_date.strftime('%Y-%m-%d')}"

class SearchQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_queries', null=True, blank=True)
    query_text = models.CharField(max_length=255)
    make_filter = models.CharField(max_length=100, blank=True, null=True)
    model_filter = models.CharField(max_length=100, blank=True, null=True)
    year_filter = models.IntegerField(null=True, blank=True)
    body_type_filter = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Search Queries"

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"'{self.query_text}' by {user_str} on {self.timestamp.strftime('%Y-%m-%d')}"