# AutoAggregator/cars/admin.py

from django.contrib import admin
from .models import Car, Review, CarView, CarSave, SearchQuery # <--- Import new models here
from django.contrib.auth.models import User # Import User for filtering if needed

# Register your Car model with the admin site
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    # Customize how the Car model appears in the admin list view
    list_display = ('make', 'model', 'year', 'trim', 'msrp_starting', 'overall_rating', 'release_date')
    # Add filters to the sidebar for easy searching
    list_filter = ('make', 'year', 'body_type')
    # Add search box for specific fields
    search_fields = ('make', 'model', 'trim')
    # Default ordering for the list
    ordering = ('-year', 'make', 'model')

    # Optional: Organize fields into collapsible sections in the detail view
    fieldsets = (
        (None, { # General Info
            'fields': ('make', 'model', 'year', 'trim', 'release_date')
        }),
        ('Pricing', {
            'fields': ('msrp_starting', 'msrp_average')
        }),
        ('Specifications', {
            'fields': ('engine_type', 'horsepower', 'torque', 'mpg_city', 'mpg_highway', 'drivetrain', 'body_type')
        }),
        ('Ratings & AI Insights', {
            'fields': ('overall_rating', 'reliability_rating', 'safety_rating', 'ai_insight_summary', 'top_pros', 'top_cons')
        }),
        ('Imagery', {
            'fields': ('main_image_url',)
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('car', 'source_name', 'reviewer_name', 'source_upvotes', 'review_date', 'sentiment_classification')
    list_filter = ('source_name', 'sentiment_classification', 'review_date')
    search_fields = ('car__make', 'car__model', 'content', 'reviewer_name')
    raw_id_fields = ('car',) # Use a raw ID input for car field for efficiency
    date_hierarchy = 'review_date' # Adds date drill-down
    ordering = ('-review_date',)

# New: Register CarView
@admin.register(CarView)
class CarViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'view_date')
    list_filter = ('user', 'car__make', 'car__model', 'view_date')
    raw_id_fields = ('user', 'car',) # Use raw ID input for user and car

# New: Register CarSave
@admin.register(CarSave)
class CarSaveAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'save_date')
    list_filter = ('user', 'car__make', 'car__model', 'save_date')
    raw_id_fields = ('user', 'car',)

# New: Register SearchQuery
@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query_text', 'body_type_filter', 'timestamp')
    list_filter = ('user', 'body_type_filter', 'timestamp')
    search_fields = ('query_text', 'make_filter', 'model_filter')
    raw_id_fields = ('user',) # Optional, if you want to quickly link to users