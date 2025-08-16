# AutoAggregator/cars/recommender_utils.py

from django.contrib.auth import get_user_model
from django.db.models import Count
from cars.models import Car, CarView, CarSave, SearchQuery # Import user interaction models

User = get_user_model() # Get the User model

def get_user_car_interactions(user):
    """
    Gathers a user's explicit (saves) and implicit (views, search terms) interactions with cars.
    Returns a dictionary where keys are Car objects and values are a 'score' based on interaction type.
    """
    interactions = {}

    # 1. Saved Cars (Strong explicit signal)
    saved_cars = CarSave.objects.filter(user=user).select_related('car')
    for save in saved_cars:
        interactions[save.car] = interactions.get(save.car, 0) + 5 # High score for saving

    # 2. Viewed Cars (Implicit signal) - More recent views might be weighted higher
    viewed_cars = CarView.objects.filter(user=user).select_related('car').order_by('-view_date')[:50] # Limit to recent views
    for view in viewed_cars:
        interactions[view.car] = interactions.get(view.car, 0) + 1 # Lower score for viewing

    # 3. Search Queries (Implicit signal) - Analyze search terms for car characteristics
    search_terms = SearchQuery.objects.filter(user=user).order_by('-timestamp').values_list('query_text', flat=True)[:20] # Limit recent searches

    # This part is a very simplified integration of search queries into collaborative filtering.
    # In a more advanced system, you'd use NLP on query_text to find similar cars.
    # For now, let's just use it as a general signal for broad preferences.

    return interactions

def calculate_user_similarity(user1, user2):
    """
    Calculates a simple similarity score between two users based on their shared car interactions.
    Returns a score between 0 and 1.
    """
    user1_interactions = get_user_car_interactions(user1)
    user2_interactions = get_user_car_interactions(user2)

    if not user1_interactions or not user2_interactions:
        return 0 # Cannot compare if no interactions

    # Find common cars
    common_cars = set(user1_interactions.keys()) & set(user2_interactions.keys())

    if not common_cars:
        return 0 # No common cars, no similarity

    # Simple similarity: sum of interaction scores for common cars / total possible score
    # For simplicity, let's just use Jaccard similarity based on shared unique cars
    all_cars = set(user1_interactions.keys()) | set(user2_interactions.keys())

    return len(common_cars) / len(all_cars) if all_cars else 0

def get_personalized_recommendations(target_user, num_recommendations=5):
    """
    Generates personalized car recommendations for the target_user using a simplified
    user-based collaborative filtering approach.
    """
    other_users = User.objects.exclude(id=target_user.id).prefetch_related('car_views', 'saved_cars')

    user_similarities = []
    for other_user in other_users:
        similarity = calculate_user_similarity(target_user, other_user)
        if similarity > 0:
            user_similarities.append({'user': other_user, 'similarity': similarity})

    # Sort by similarity (most similar first)
    user_similarities.sort(key=lambda x: x['similarity'], reverse=True)

    recommended_cars = {} # Stores {Car: score}

    # For the most similar users, find cars they interacted with that target_user hasn't
    target_user_interacted_cars = set(get_user_car_interactions(target_user).keys())

    for similar_user_data in user_similarities:
        similar_user = similar_user_data['user']
        similar_user_interactions = get_user_car_interactions(similar_user)

        for car, score in similar_user_interactions.items():
            if car not in target_user_interacted_cars: # Only recommend new cars
                # Score recommendation by similarity * interaction score
                recommended_cars[car] = recommended_cars.get(car, 0) + (score * similar_user_data['similarity'])

    # Sort recommended cars by their score
    sorted_recommendations = sorted(recommended_cars.items(), key=lambda item: item[1], reverse=True)

    # Return only the Car objects, limited by num_recommendations
    return [car for car, score in sorted_recommendations[:num_recommendations]]

# --- For debugging and testing without full user interactions ---
def get_simple_content_based_recommendations(target_car=None, num_recommendations=5):
    """
    Generates simple content-based recommendations (cars similar by body_type/make/model segment).
    Used as a fallback or for new users without interaction history.
    """
    if not target_car:
        # If no target car, recommend top overall cars (fallback)
        return Car.objects.filter(overall_rating__isnull=False).order_by('-overall_rating')[:num_recommendations]

    # Find cars with similar body_type and within similar price range
    similar_cars = Car.objects.filter(
        body_type=target_car.body_type,
        msrp_starting__gte=target_car.msrp_starting * 0.8, # within 20% price range
        msrp_starting__lte=target_car.msrp_starting * 1.2
    ).exclude(id=target_car.id).order_by('-overall_rating')[:num_recommendations]

    return list(similar_cars)