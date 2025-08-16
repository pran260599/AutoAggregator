# AutoAggregator/cars/management/commands/ingest_reviews.py

import requests
import os
import time
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from cars.models import Car, Review
from datetime import date
from django.utils import timezone
from requests.exceptions import RequestException, HTTPError


# --- Reddit API Configuration (REPLACE WITH YOUR ACTUAL CREDENTIALS) ---
REDDIT_CLIENT_ID = "z0tM0DbgYeuybQXHHQonWA"
REDDIT_CLIENT_SECRET = "rmw5Z89LY6yFn8BPN_CnEIt6wEPvtw"
REDDIT_USERNAME = "ImpressiveToe5639"
REDDIT_PASSWORD = "pRaN26@05" 

REDDIT_API_BASE_URL = "https://oauth.reddit.com"
REDDIT_AUTH_URL = "https://www.reddit.com/api/v1/access_token"

# --- Reddit Rate Limit Constants ---
REDDIT_REQUEST_INTERVAL = 3 # seconds to wait between individual Reddit API calls
# --- END Reddit API Configuration ---


class Command(BaseCommand):
    help = 'Ingests review data from Reddit API for analysis.'

    def add_arguments(self, parser):
        parser.add_argument('--make', type=str, help='Filter reviews by car make (e.g., Toyota)')
        parser.add_argument('--model', type=str, help='Filter reviews by car model (e.g., Camry)')
        parser.add_argument('--year', type=int, help='Filter reviews by car year (e.g., 2024)')
        parser.add_argument('--limit', type=int, default=10, help='Limit the number of posts to fetch per query. Max 100 for Reddit search.')
        parser.add_argument('--max-pages', type=int, default=1, help='Max number of pages (API calls) to fetch for each car. Each page returns "limit" items.')
        parser.add_argument('--subreddit', type=str, default='cars', help='Specify Reddit subreddit to search (e.g., cars, whatcarshouldibuy)')
        parser.add_argument('--fetch-comments', action='store_true', default=False, help='Fetch comments for each post (increases API calls).')

    def get_reddit_access_token(self):
        # ... (unchanged) ...
        self.stdout.write(self.style.MIGRATE_HEADING("Attempting to get Reddit API access token..."))
        client_auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
        post_data = {
            "grant_type": "password",
            "username": REDDIT_USERNAME,
            "password": REDDIT_PASSWORD
        }
        headers = {"User-Agent": f"python:AutoAggregatorApp:v1.0 (by u/{REDDIT_USERNAME}, contact: pranavjupally@gmail.com)"}
        
        try:
            response = requests.post(REDDIT_AUTH_URL, auth=client_auth, data=post_data, headers=headers, timeout=10)
            response.raise_for_status()
            self.stdout.write(self.style.SUCCESS("Successfully obtained Reddit API access token."))
            return response.json()["access_token"]
        except RequestException as e:
            self.stdout.write(self.style.ERROR(f"Failed to obtain Reddit API access token: {e}"))
            raise CommandError(f"Reddit Auth Error: {e}")


    def fetch_comments_for_post(self, access_token, subreddit, post_id, limit=50):
        """
        Fetches comments for a specific Reddit post.
        """
        headers = {
            "Authorization": f"bearer {access_token}",
            "User-Agent": f"python:AutoAggregatorApp:v1.0 (by u/{REDDIT_USERNAME}, contact: pranavjupally@gmail.com)",
            "Accept": "application/json"
        }
        comments_data = []
        
        # Reddit's comment API structure: /r/{subreddit}/comments/{article}.json
        # The 'article' is the post ID (e.g., "1iq5cz7").
        api_url = f"{REDDIT_API_BASE_URL}/r/{subreddit}/comments/{post_id}.json"
        
        self.stdout.write(f"DEBUG: Fetching comments for post {post_id} in r/{subreddit} (limit {limit})...")
        self.stdout.write(f"DEBUG: Attempting comments URL: {api_url}") # <--- ADDED DEBUG PRINT FOR URL
        try:
            response = requests.get(api_url, 
                                    headers=headers, 
                                    params={'limit': limit, 'sort': 'top'},
                                    timeout=30)
            response.raise_for_status()
            
            comments_tree = response.json()
            if len(comments_tree) > 1 and comments_tree[1] and comments_tree[1].get('data', {}).get('children'):
                for comment in comments_tree[1]['data']['children']:
                    comment_data = comment.get('data', {})
                    if comment_data.get('body') and comment_data['body'].strip() != '[deleted]' and comment_data['body'].strip() != '[removed]' and len(comment_data['body'].strip()) > 50:
                        comments_data.append({
                            'text': comment_data['body'].strip(),
                            'review_id': comment_data.get('id'),
                            'score': comment_data.get('score'),
                            'source': f'Reddit (r/{subreddit} - comment)',
                            'source_url': f"https://www.reddit.com{comment_data.get('permalink')}",
                            'author': f"u/{comment_data.get('author')}" if comment_data.get('author') else 'Anonymous',
                            'date': date.fromtimestamp(comment_data.get('created_utc')) if comment_data.get('created_utc') else None # Use post_data here? No, comment_data
                        })
            self.stdout.write(self.style.SUCCESS(f"Fetched {len(comments_data)} comments for post {post_id}."))
            return comments_data
        except HTTPError as e:
            self.stdout.write(self.style.ERROR(f"HTTP Error fetching comments for post {post_id}: {e.response.status_code} - {e.response.text}"))
            if e.response.status_code == 404 and e.response.text:
                self.stdout.write(self.style.ERROR(f"  Reddit API response: {e.response.text}"))
            return []
        except RequestException as e:
            self.stdout.write(self.style.ERROR(f"Network Error fetching comments for post {post_id}: {e}"))
            return []
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected Error fetching comments for post {post_id}: {e}"))
            return []


    def fetch_reviews_from_reddit(self, access_token, query, subreddit, limit, max_pages=1, fetch_comments=False):
        # ... (unchanged) ...
        headers = {
            "Authorization": f"bearer {access_token}",
            "User-Agent": f"python:AutoAggregatorApp:v1.0 (by u/{REDDIT_USERNAME}, contact: pranavjupally@gmail.com)",
            "Accept": "application/json"
        }
        all_reviews_data = []
        after = None # For pagination

        self.stdout.write(self.style.MIGRATE_HEADING(f"Fetching '{query}' posts from r/{subreddit} (up to {max_pages} pages)..."))

        for page_num in range(max_pages):
            params = {
                "q": query,
                "limit": limit,
                "sort": "relevance",
                "t": "year"
            }
            if after:
                params['after'] = after

            try:
                response = requests.get(f"{REDDIT_API_BASE_URL}/r/{subreddit}/search.json", headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                posts = data.get('data', {}).get('children', [])
                if not posts:
                    self.stdout.write(self.style.WARNING(f"No more posts found for '{query}' on page {page_num + 1}."))
                    break

                for post in posts:
                    post_data = post.get('data', {})
                    review_content = post_data.get('selftext') or post_data.get('title')
                    
                    if review_content and len(review_content.strip()) > 50:
                        review_content = review_content.replace('[deleted]', '').replace('[removed]', '').strip()
                        reviews_data_item = {
                            'text': review_content,
                            'review_id': post_data.get('id'), # Post ID
                            'score': post_data.get('score'),
                            'source': f'Reddit (r/{subreddit} - post)',
                            'source_url': f"https://www.reddit.com{post_data.get('permalink')}",
                            'author': f"u/{post_data.get('author')}" if post_data.get('author') else 'Anonymous',
                            'date': date.fromtimestamp(post_data.get('created_utc')) if post_data.get('created_utc') else None
                        }
                        all_reviews_data.append(reviews_data_item)
                    
                    if fetch_comments and post_data.get('num_comments', 0) > 0:
                        self.stdout.write(f"DEBUG: Found {post_data.get('num_comments', 0)} comments for post {post_data.get('id')}. Fetching...")
                        time.sleep(REDDIT_REQUEST_INTERVAL) # <--- ADDED SLEEP HERE BEFORE FETCHING COMMENTS
                        comments_for_post = self.fetch_comments_for_post(access_token, subreddit, post_data.get('id'), limit=50)
                        all_reviews_data.extend(comments_for_post)

                after = data.get('data', {}).get('after')
                if not after:
                    self.stdout.write(self.style.WARNING(f"No 'after' token found. Last page of results for '{query}'."))
                    break

                if page_num < max_pages - 1 and after:
                    self.stdout.write(f"Sleeping for {REDDIT_REQUEST_INTERVAL} seconds to respect API rate limits between pages...")
                    time.sleep(REDDIT_REQUEST_INTERVAL)

            except HTTPError as e:
                self.stdout.write(self.style.ERROR(f"HTTP Error fetching posts for query '{query}' (Page {page_num + 1}): {e.response.status_code} - {e.response.text}"))
                return []
            except RequestException as e:
                self.stdout.write(self.style.ERROR(f"Network Error fetching posts for query '{query}' (Page {page_num + 1}): {e}"))
                return []
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Unexpected Error fetching posts for query '{query}' (Page {page_num + 1}): {e}"))
                return []
            
            self.stdout.write(self.style.SUCCESS(f"Finished fetching posts and comments for '{query}'. Total fetched: {len(all_reviews_data)}."))
            return all_reviews_data


    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting review data ingestion from Reddit API...'))

        if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
            raise CommandError("Reddit API credentials (CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD) are not fully set in ingest_reviews.py.")

        ingested_count = 0
        updated_count = 0
        skipped_count = 0
        
        target_make = options['make']
        target_model = options['model']
        target_year = options['year']
        review_limit = options['limit']
        max_pages = options['max_pages']
        subreddit = options['subreddit']
        fetch_comments_option = options['fetch_comments']

        cars_queryset = Car.objects.all()
        if target_make:
            cars_queryset = cars_queryset.filter(make__iexact=target_make)
        if target_model:
            cars_queryset = cars_queryset.filter(model__iexact=target_model)
        if target_year:
            cars_queryset = cars_queryset.filter(year=target_year)

        if not cars_queryset.exists():
            self.stdout.write(self.style.WARNING(f'No cars found matching specified filters ({target_make or "Any"} {target_model or "Any"} {target_year or "Any"}). Please ensure cars are imported first.'))
            return
        
        try:
            reddit_access_token = self.get_reddit_access_token()
        except CommandError as e:
            self.stdout.write(self.style.ERROR(f"Aborting ingestion due to Reddit authentication error: {e}"))
            return

        for car in cars_queryset:
            search_query = f"{car.year} {car.make} {car.model}"
            
            try:
                reviews_from_source = self.fetch_reviews_from_reddit(
                    reddit_access_token, search_query, subreddit, review_limit, max_pages, fetch_comments_option
                )
                
                if not reviews_from_source:
                    self.stdout.write(self.style.WARNING(f'No reviews found on Reddit for "{search_query}" in r/{subreddit}.'))
                    continue

                for review_item in reviews_from_source:
                    try:
                        review_date_obj = review_item.get('date')
                        
                        with transaction.atomic():
                            review_obj, created = Review.objects.update_or_create(
                                car=car,
                                source_name=review_item.get('source'),
                                reviewer_id=review_item.get('review_id'),
                                defaults={
                                    'content': review_item['text'],
                                    'source_url': review_item.get('source_url', ''),
                                    'reviewer_name': review_item.get('author', 'Anonymous'),
                                    'source_upvotes': review_item.get('score', 0),
                                    'review_date': review_date_obj,
                                    'retrieval_date': timezone.now()
                                }
                            )

                            if created:
                                ingested_count += 1
                                self.stdout.write(self.style.SUCCESS(f'Successfully ingested NEW review for {car} from {review_obj.source_name} (ID: {review_obj.reviewer_id}, Upvotes: {review_obj.source_upvotes})'))
                            else:
                                updated_count += 1
                                self.stdout.write(self.style.WARNING(f'Review for {car} from {review_obj.source_name} (ID: {review_obj.reviewer_id}) already exists, UPDATED. Upvotes: {review_obj.source_upvotes}'))
                                
                    except Car.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"Error: Car {car.make} {car.model} {car.year} not found for review. Skipping review ingestion."))
                        skipped_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'An unexpected error occurred ingesting review for {car} (ID: {review_item.get("review_id", "N/A")}): {e}'))
                        skipped_count += 1

            except RequestException as e:
                self.stdout.write(self.style.ERROR(f"API request failed for {search_query} from Reddit: {e}"))
                skipped_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'An unexpected error occurred during Reddit fetch or processing for "{search_query}": {e}'))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS('--- Review ingestion process finished ---'))
        self.stdout.write(self.style.SUCCESS(f'Total Reviews Newly Ingested: {ingested_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total Reviews Updated: {updated_count}'))
        self.stdout.write(self.style.WARNING(f'Total Skipped/Errors: {skipped_count}'))