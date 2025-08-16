# AutoAggregator/cars/nlp_utils.py

import nltk
import os
import sys
import re

from nltk.sentiment.vader import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

# --- Expanded & Refined Keyword Lists for ABSA ---
ASPECT_KEYWORDS = {
    "engine": ["engine", "motor", "power", "horsepower", "acceleration", "performance", "torque", "drivetrain", "speed", "pickup", "hp", "engine_power", "motor_power"],
    "infotainment": ["infotainment", "screen", "display", "system", "tech", "technology", "connectivity", "interface", "navigation", "android auto", "apple carplay", "touchscreen", "software", "ui", "apps", "user_interface"],
    "interior": ["interior", "cabin", "seats", "materials", "space", "comfort", "legroom", "headroom", "design", "quality", "dashboard", "trim", "luxury", "finish", "ergonomics", "seating"],
    "exterior": ["exterior", "design", "looks", "styling", "appearance", "body", "paint", "shape", "lines", "aerodynamics", "curb appeal", "headlights", "taillights", "wheels", "chrome"],
    "handling": ["handling", "steering", "ride", "suspension", "brakes", "cornering", "road feel", "driving", "agility", "stability", "maneuverability", "braking", "control", "responsive"], # Added responsive
    "fuel_economy": ["fuel economy", "mpg", "gas mileage", "efficiency", "consumption", "fuel efficiency", "electric range", "charging", "battery", "range", "fuel"],
    "reliability": ["reliability", "dependable", "breakdown", "issues", "problems", "maintenance", "trustworthy", "durable", "longevity", "faults", "repair"],
    "safety": ["safety", "crash", "airbags", "driver assistance", "ncap", "safety features", "adas", "driver-assist", "collision", "blind spot", "lane keeping", "autopilot", "braking_assist", "warnings"],
    "cargo_space": ["cargo", "trunk", "boot", "storage", "space", "capacity", "rear storage", "hatchback", "compartment"],
    "price": ["price", "cost", "expensive", "affordable", "value", "deal", "cheap", "mrp", "sticker", "pricing"], # Added pricing
    "noise": ["noise", "loud", "quiet", "road noise", "wind noise", "engine noise", "cabin noise", "vibration", "sound"], # Added sound
    "transmission": ["transmission", "gearbox", "shifting", "cvt", "automatic", "manual", "gears", "shifter"] # Added shifter
}

# General sentiment words (expanded and ordered by strength, for better description picking)
POSITIVE_WORDS = [
    "excellent", "superb", "outstanding", "fantastic", "impressive", "amazing", "great", "powerful",
    "responsive", "smooth", "intuitive", "efficient", "reliable", "safe", "dependable", "quick", "fast", "exhilarating",
    "comfortable", "spacious", "luxurious", "stylish", "beautiful", "high-quality", "well-built", "premium", "sleek", "opulent", "refined",
    "good", "ample", "solid", "decent", "nice", "love", "user-friendly", "convenient", "quiet", "easy", "firm", "sporty", "crisp", "clear", "bright", "seamless"
]
NEGATIVE_WORDS = [
    "terrible", "horrible", "frustrating", "unreliable", "clunky", "poor", "bad", "noisy", "disappointing",
    "slow", "weak", "underpowered", "rough", "jerky", "unresponsive", "inefficient", "flimsy", "awkward", "buggy", "limited", "tight",
    "cramped", "cheap", "plain", "dated", "subpar", "lackluster", "problematic", "annoying", "overpriced", "harsh", "distracting", "confusing", "uncomfortable"
]

# Define plausibility for descriptive words with aspects to mitigate misattributions
# A word is plausible for an aspect if it appears in its POSITIVE/NEGATIVE_WORDS context
# This is a basic rule, advanced would be semantic similarity
PLAUSIBLE_DESCRIPTORS = {
    "engine": POSITIVE_WORDS + ['slow', 'weak', 'underpowered'], # Only relevant performance terms
    "infotainment": POSITIVE_WORDS + ['clunky', 'buggy', 'frustrating', 'awkward', 'confusing', 'distracting'],
    "interior": POSITIVE_WORDS + ['plain', 'cheap', 'uncomfortable', 'cramped', 'dated', 'flimsy'],
    "exterior": POSITIVE_WORDS + ['plain', 'dated'],
    "handling": POSITIVE_WORDS + ['rough', 'jerky', 'unresponsive'],
    "fuel_economy": POSITIVE_WORDS + ['inefficient', 'terrible', 'expensive', 'high'], # High could be negative for cost
    "reliability": POSITIVE_WORDS + ['unreliable', 'problematic', 'faults'],
    "safety": POSITIVE_WORDS + ['poor', 'bad'],
    "cargo_space": POSITIVE_WORDS + ['limited', 'tight'],
    "price": POSITIVE_WORDS + ['expensive', 'overpriced', 'high'], # High could be negative
    "noise": POSITIVE_WORDS + ['noisy', 'loud'], # Quiet is positive, noisy/loud are negative
    "transmission": POSITIVE_WORDS + ['clunky', 'jerky', 'rough'],
}
# Convert plausible descriptors to lowercase sets for efficient lookup
for aspect, words in PLAUSIBLE_DESCRIPTORS.items():
    PLAUSIBLE_DESCRIPTORS[aspect] = set(w.lower() for w in words)


def get_sentiment(text):
    if not text or not isinstance(text, str):
        return {"neg": 0.0, "neu": 0.0, "pos": 0.0, "compound": 0.0}
    scores = analyzer.polarity_scores(text)
    return scores

def classify_sentiment(compound_score, threshold=0.05): # Use this for overall classification
    if compound_score >= threshold:
        return "Positive"
    elif compound_score <= -threshold:
        return "Negative"
    else:
        return "Neutral"

def perform_aspect_sentiment_analysis(reviews_list):
    aspect_data = {} # Stores { "aspect": {"compound_scores": [...], "descriptive_words": set()} }

    for review_text in reviews_list:
        sentences = nltk.sent_tokenize(review_text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            sentence_scores = get_sentiment(sentence)
            compound_score = sentence_scores['compound']

            if classify_sentiment(compound_score, threshold=0.001) == "Neutral":
                continue 

            found_aspects = []
            for aspect, keywords in ASPECT_KEYWORDS.items():
                if any(re.search(r'\b' + re.escape(kw) + r'\b', sentence_lower) for kw in keywords):
                    found_aspects.append(aspect)
            
            if found_aspects:
                for aspect in found_aspects:
                    if aspect not in aspect_data:
                        aspect_data[aspect] = {'compound_scores': [], 'descriptive_words': set()}
                    
                    aspect_data[aspect]['compound_scores'].append(compound_score)
                    
                    # Collect descriptive words based on sentence sentiment alignment and plausibility
                    if compound_score > 0: # If sentence is positive
                        for pw in POSITIVE_WORDS:
                            if pw.lower() in sentence_lower and pw.lower() in PLAUSIBLE_DESCRIPTORS.get(aspect, set()): # Check plausibility
                                aspect_data[aspect]['descriptive_words'].add(pw.capitalize())
                                # break # Don't break yet, collect all plausible words
                    else: # If sentence is negative
                        for nw in NEGATIVE_WORDS:
                            if nw.lower() in sentence_lower and nw.lower() in PLAUSIBLE_DESCRIPTORS.get(aspect, set()): # Check plausibility
                                aspect_data[aspect]['descriptive_words'].add(nw.capitalize())
                                # break # Don't break yet, collect all plausible words
    
    final_pros = []
    final_cons = []

    for aspect, data in aspect_data.items():
        if not data['compound_scores']:
            continue

        avg_compound = sum(data['compound_scores']) / len(data['compound_scores'])
        
        classified_sentiment = classify_sentiment(avg_compound, threshold=0.06) 

        desc = ""
        # --- Improved description selection: Prioritize by strength/order in lists ---
        if classified_sentiment == "Positive":
            for pw in POSITIVE_WORDS: # Iterate in order of strength
                if pw.capitalize() in data['descriptive_words']:
                    desc = pw.capitalize()
                    break # Found the strongest/most specific word
            if not desc: desc = "Good" # Fallback
            final_pros.append({"aspect": aspect.replace('_', ' ').title(), "description": desc, "sentiment": "Positive"})
        elif classified_sentiment == "Negative":
            for nw in NEGATIVE_WORDS: # Iterate in order of strength
                if nw.capitalize() in data['descriptive_words']:
                    desc = nw.capitalize()
                    break # Found the strongest/most specific word
            if not desc: desc = "Poor" # Fallback
            final_cons.append({"aspect": aspect.replace('_', ' ').title(), "description": desc, "sentiment": "Negative"})
        
    return final_pros[:5], final_cons[:5] # Limit to top 5 for display