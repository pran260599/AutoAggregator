# AutoAggregator/cars/management/commands/import_cars.py

import requests
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from cars.models import Car
from datetime import date

CAR_API_KEY = "e0a5df54-5827-4c44-ae05-bdc57b1db2f3" # Your actual key
CAR_API_BASE_URL = "https://carapi.app/api/v1"

TARGET_YEAR = 2024 # Or 2023, ensure this matches your mock data years
TARGET_MAKES = ["Toyota", "Honda", "Ford", "Tesla", "Subaru", "Mazda"]

class Command(BaseCommand):
    help = 'Imports car data from an external API (or mock data) and updates with basic AI insights.'

    def handle(self, *args, **options):
        if not CAR_API_KEY or CAR_API_KEY == "YOUR_CAR_API_KEY_HERE":
            raise CommandError("CAR_API_KEY is not set. Please get one from carapi.app and replace 'YOUR_CAR_API_KEY_HERE' in import_cars.py")

        headers = {
            "Authorization": f"Bearer {CAR_API_KEY}",
            "Accept": "application/json"
        }

        self.stdout.write(self.style.SUCCESS('Starting car data import and AI analysis...'))
        imported_count = 0
        updated_count = 0
        skipped_count = 0

        # --- MOCK API DATA FOR DEMONSTRATION (UNCOMMENT/USE THIS BLOCK) ---
        # You can place this dictionary outside the loop, or create it dynamically.
        # Ensure the years here match your TARGET_YEAR.
        mock_data_for_import = [
            # Toyota Camry 2024 (adjust year if TARGET_YEAR is different)
            {"make_name": "Toyota", "model_name": "Camry", "model_year": TARGET_YEAR, "model_trim": "SE", "msrp_min": 28400, "msrp_max": 32000, "engine_type": "2.5L I4", "horsepower": 203, "mpg_city": 28, "mpg_highway": 39, "drivetrain": "FWD", "body_type": "Sedan", "image_url": "https://picsum.photos/400/300?random=101"},
            # Honda CR-V 2024
            {"make_name": "Honda", "model_name": "CR-V", "model_year": TARGET_YEAR, "model_trim": "EX-L", "msrp_min": 33950, "msrp_max": 36500, "engine_type": "1.5L Turbo I4", "horsepower": 190, "mpg_city": 28, "mpg_highway": 34, "drivetrain": "AWD", "body_type": "SUV", "image_url": "https://picsum.photos/400/300?random=102"},
            # Ford F-150 2024
            {"make_name": "Ford", "model_name": "F-150", "model_year": TARGET_YEAR, "model_trim": "XLT", "msrp_min": 36570, "msrp_max": 45000, "engine_type": "2.7L EcoBoost V6", "horsepower": 325, "mpg_city": 20, "mpg_highway": 26, "drivetrain": "4WD", "body_type": "Truck", "image_url": "https://picsum.photos/400/300?random=103"},
            # Tesla Model 3 2024
            {"make_name": "Tesla", "model_name": "Model 3", "model_year": TARGET_YEAR, "model_trim": "Long Range", "msrp_min": 47490, "msrp_max": 52000, "engine_type": "Electric", "horsepower": 283, "mpg_city": 132, "mpg_highway": 117, "drivetrain": "AWD", "body_type": "Sedan", "image_url": "https://picsum.photos/400/300?random=104"},
            # Subaru Outback 2024
            {"make_name": "Subaru", "model_name": "Outback", "model_year": TARGET_YEAR, "model_trim": "Limited", "msrp_min": 31000, "msrp_max": 35500, "engine_type": "2.5L H4", "horsepower": 182, "mpg_city": 26, "mpg_highway": 32, "drivetrain": "AWD", "body_type": "SUV", "image_url": "https://picsum.photos/400/300?random=105"},
             # Mazda CX-5 2024 (Added this to ensure all TARGET_MAKES get some data)
            {"make_name": "Mazda", "model_name": "CX-5", "model_year": TARGET_YEAR, "model_trim": "Grand Touring", "msrp_min": 29200, "msrp_max": 33000, "engine_type": "2.5L I4", "horsepower": 187, "mpg_city": 24, "mpg_highway": 30, "drivetrain": "AWD", "body_type": "SUV", "image_url": "https://picsum.photos/400/300?random=106"},
        ]
        # --- END MOCK API DATA ---

        for make_name in TARGET_MAKES:
            self.stdout.write(self.style.SUCCESS(f'--- Importing {make_name} cars for year {TARGET_YEAR} ---'))
            try:
                # --- COMMENT OUT / REMOVE THIS SECTION FOR NOW ---
                # response = requests.get(
                #     f"{CAR_API_BASE_URL}/vehicles?make={make_name}&year={TARGET_YEAR}&limit=50",
                #     headers=headers,
                #     timeout=30
                # )
                # response.raise_for_status()
                # api_data = response.json().get('data', [])
                # --- END COMMENT OUT ---

                # --- ASSIGN MOCK DATA HERE ---
                # Filter mock_data_for_import based on current make_name and TARGET_YEAR
                api_data = [item for item in mock_data_for_import if item['make_name'] == make_name and item['model_year'] == TARGET_YEAR]

                if not api_data:
                    self.stdout.write(self.style.WARNING(f'No mock data found for {make_name} {TARGET_YEAR}'))
                    continue

                for item in api_data:
                    self.stdout.write(f"DEBUG: Processing car from API: {item.get('make_name')} {item.get('model_name')} {item.get('model_year')} {item.get('model_trim', '')}")

                    try:
                        with transaction.atomic():
                            car, created = Car.objects.update_or_create(
                                make=item.get('make_name'),
                                model=item.get('model_name'),
                                year=item.get('model_year'),
                                trim=item.get('model_trim', None),
                                defaults={
                                    'msrp_starting': item.get('msrp_min'),
                                    'msrp_average': item.get('msrp_max'),
                                    'engine_type': item.get('engine_type'),
                                    'horsepower': item.get('horsepower'),
                                    'mpg_city': item.get('mpg_city'),
                                    'mpg_highway': item.get('mpg_highway'),
                                    'drivetrain': item.get('drivetrain'),
                                    'body_type': item.get('body_type'),
                                    'main_image_url': item.get('image_url'),
                                    'release_date': date(item.get('model_year'), 1, 1),
                                    'overall_rating': None,
                                    'ai_insight_summary': None,
                                    'top_pros': [],
                                    'top_cons': [],
                                }
                            )

                            if created:
                                imported_count += 1
                                self.stdout.write(self.style.SUCCESS(f'Successfully imported: {car}'))
                            else:
                                updated_count += 1
                                self.stdout.write(self.style.SUCCESS(f'Successfully updated: {car}'))

                    except Exception as e:
                        skipped_count += 1
                        self.stdout.write(self.style.ERROR(f'Error processing {item.get("make_name")} {item.get("model_name")} {item.get("model_year")}: {e}'))

            except Exception as e: # Catch any errors from processing make_name or mock data filtering
                self.stdout.write(self.style.ERROR(f"An unexpected error occurred during import for make {make_name} in year {TARGET_YEAR}: {e}"))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS('--- Car import process finished ---'))
        self.stdout.write(self.style.SUCCESS(f'Total Imported: {imported_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total Updated: {updated_count}'))
        self.stdout.write(self.style.WARNING(f'Total Skipped (Errors): {skipped_count}'))