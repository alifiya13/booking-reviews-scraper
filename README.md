# Booking.com Reviews Scraper

A Python tool for scraping guest reviews from Booking.com property pages.

## Features

- Extracts detailed review information including:
  - Reviewer name and country
  - Stay dates and duration
  - Room type
  - Traveler type (family, business, etc.)
  - Review title, rating, and full text

## Requirements

- Python 3.6+
- Required packages (see requirements.txt)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/booking-reviews-scraper.git
   cd booking-reviews-scraper
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Web Interface

Run the Flask app:
```
python app.py
```

### API

Make a POST request to `/api/booking` with a JSON payload:
```json
{
  "url": "https://www.booking.com/hotel/us/miami-marriott-dadeland.html",
  "max_reviews": 100  // Optional
}
```

## Output

The scraper saves results as CSV files with the following format:
- id
- reviewer_name
- reviewer_country
- stay_date
- review_type
- review_date
- room_type
- nights_stayed
- rating
- review_title
- review_text
