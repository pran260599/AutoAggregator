# AutoAggregator/cars/management/commands/analyze_reviews.py

import os # <--- ADD THIS LINE HERE

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Avg
from cars.models import Car, Review
from cars.nlp_utils import get_sentiment, classify_sentiment, perform_aspect_sentiment_analysis
from django.utils import timezone 

class Command(BaseCommand):
    help = 'Analyzes review data from the Review model and updates Car models with AI insights.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting review analysis and car insights update...'))

        processed_cars_count = 0
        errors_count = 0

        cars_with_reviews = Car.objects.filter(reviews__isnull=False).distinct()

        if not cars_with_reviews.exists():
            self.stdout.write(self.style.WARNING('No cars with associated reviews found. Please add reviews in the Django admin or import them.'))
            return

        for car in cars_with_reviews:
            self.stdout.write(self.style.SUCCESS(f'--- Analyzing reviews for: {car.year} {car.make} {car.model} {car.trim or ""} ---'))

            try:
                with transaction.atomic():
                    reviews_for_car = car.reviews.all()

                    if not reviews_for_car.exists():
                        self.stdout.write(self.style.WARNING(f'No reviews found for {car}, skipping AI analysis.'))
                        continue

                    self.stdout.write(f"DEBUG: Processing car: {car.make} {car.model} {car.year} {car.trim or ''}")

                    review_contents = [review.content for review in reviews_for_car]
                    all_compound_scores = []

                    for review_obj in reviews_for_car:
                        scores = get_sentiment(review_obj.content)
                        compound_score = scores['compound']

                        all_compound_scores.append(compound_score)

                        review_obj.sentiment_compound_score = round(compound_score, 4)
                        review_obj.sentiment_classification = classify_sentiment(compound_score)
                        review_obj.save()

                        self.stdout.write(f"DEBUG: Analyzed review (ID: {review_obj.reviewer_id or 'N/A'}, Upvotes: {review_obj.source_upvotes or 'N/A'}) for '{review_obj.content[:50]}...'")

                    if all_compound_scores:
                        avg_compound = sum(all_compound_scores) / len(all_compound_scores)
                        overall_rating = round(((avg_compound + 1) / 2) * 5, 2)

                        # --- Use new ABSA function here ---
                        top_pros_absa, top_cons_absa = perform_aspect_sentiment_analysis(review_contents)

                        # Refine AI Insight Summary to use ABSA insights
                        ai_summary_parts = []
                        if top_pros_absa:
                            pro_aspects = [p['aspect'] for p in top_pros_absa]
                            ai_summary_parts.append(f"Highly praised for {', '.join(pro_aspects[:2])}.")
                        if top_cons_absa:
                            con_aspects = [c['aspect'] for c in top_cons_absa]
                            ai_summary_parts.append(f"Some concerns regarding {', '.join(con_aspects[:2])}.")

                        if not ai_summary_parts: # Fallback if no specific aspects found
                            sentiment_classification = classify_sentiment(avg_compound)
                            if sentiment_classification == "Positive":
                                ai_summary_parts.append("Generally well-received overall.")
                            elif sentiment_classification == "Negative":
                                ai_summary_parts.append("Receives mixed to negative feedback.")
                            else:
                                ai_summary_parts.append("Offers a balanced experience.")

                        ai_summary = f"Overall ({overall_rating}/5). " + " ".join(ai_summary_parts)
                        ai_summary = ai_summary.strip()
                        # Ensure ai_summary is not too long for TextField (max_length not set)
                        # You might truncate it if it gets excessively long.

                        # Update Car model fields with ABSA results
                        car.overall_rating = overall_rating
                        car.ai_insight_summary = ai_summary
                        car.top_pros = top_pros_absa
                        car.top_cons = top_cons_absa
                        car.save()

                        self.stdout.write(self.style.SUCCESS(f'Updated AI insights for: {car} (Rating: {overall_rating})'))
                        self.stdout.write(f'  ABSA Pros: {car.top_pros}, ABSA Cons: {car.top_cons}')
                        processed_cars_count += 1
                    else:
                        self.stdout.write(self.style.WARNING(f'Could not calculate sentiment for {car} (no valid review scores).'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {car}: {e}'))
                errors_count += 1

        self.stdout.write(self.style.SUCCESS('--- Review analysis process finished ---'))
        self.stdout.write(self.style.SUCCESS(f'Total Cars Processed: {processed_cars_count}'))
        self.stdout.write(self.style.WARNING(f'Total Errors: {errors_count}'))