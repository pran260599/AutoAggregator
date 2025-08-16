Car Review Aggregator & AI Recommendation Platform
This is a full-stack web application for aggregating car reviews and providing AI-powered insights and personalized recommendations. The platform is designed to help users make informed decisions by consolidating data from various sources and using machine learning to surface relevant information.

Table of Contents
Features

Technologies Used

Setup and Installation

API Endpoints

Project Status

Contact

Features
Comprehensive Car Search: Users can search and filter a database of cars by make, model, year, and price.

AI-Powered Insights: A backend system uses Aspect-Based Sentiment Analysis (ABSA) to summarize thousands of reviews into clear pros and cons for each car.

Personalized Recommendations: A collaborative filtering model suggests cars based on a user's viewing, saving, and searching history.

Real User Authentication: A secure user registration, login, and logout system is implemented to provide a personalized experience.

User Dashboard: A dedicated profile page where users can view their account details, saved cars, and search history.

Dynamic UI: The frontend dynamically renders content and updates in real-time based on user interaction and API responses.

Technologies Used
Backend:

Django: The core web framework.

Django REST Framework (DRF): For building the RESTful API endpoints.

Python: The main programming language.

PostgreSQL: The primary relational database.

Frontend:

HTML, CSS, JavaScript (ES6+): The foundation of the user interface.

React: (Conceptual future step or if used in your projects) For building dynamic user components.

AI/ML:

Natural Language Processing (NLP): For sentiment analysis of car reviews.

Collaborative Filtering: For the personalized recommendation engine.

Tools & Deployment:

Git & GitHub: For version control.

Render: (Used for deployment in the roadmap) A cloud platform for hosting the full-stack application.

VS Code: The development environment.

Setup and Installation
Follow these steps to get a local copy of the project up and running.

Clone the repository:

Bash

git clone https://github.com/[Your-Username]/AutoAggregator.git
cd AutoAggregator
Set up the virtual environment and install dependencies:

Bash

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
Configure the database:

Ensure your PostgreSQL database is running.

Update the database connection settings in core/settings.py.

Run migrations and create a superuser:

Bash

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
Run the development server:

Bash

python manage.py runserver
The application will be available at http://127.0.0.1:8000.

API Endpoints
The following are the main API endpoints for the application:

/api/cars/: List all cars.

/api/register/: Register a new user (POST request).

/api/login/: Log in a user (POST request).

/api/logout/: Log out the current user (POST request).

/api/cars/personalized_recommendations/: Get personalized car recommendations for the authenticated user.

/api/car-views/: Record a user's car view history.

/api/car-saves/: Record a user's saved cars.

/api/search-queries/: Record a user's search history.

Project Status
This project is currently in Phase 5: Beta Launch Preparation of its development roadmap. All core features, including AI insights and a real user authentication system, are complete and functional.

Contact
Pranav Kumar Jupally - pranavkumar2605@gmail.com

Project Link: https://github.com/[Your-Username]/AutoAggregator
