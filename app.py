## app.py
from flask import Flask, render_template, request, jsonify
import os
from scrapers.booking_scraper import scrape_booking_reviews
from scrapers.utils import validate_booking_url, extract_property_info
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    result = None
    
    if request.method == 'POST':
        url = request.form.get('url')
        max_reviews = request.form.get('max_reviews')
        
        # Validate URL
        if not validate_booking_url(url):
            message = "Invalid Booking.com URL. Please use a URL in the format: https://www.booking.com/hotel/country_code/property_name.html"
            return render_template('index.html', message=message)
        
        # Convert max_reviews to int if provided, otherwise set to None
        max_reviews = int(max_reviews) if max_reviews and max_reviews.isdigit() else None
        
        try:
            # Get property info for file naming
            property_type, country_code, property_name = extract_property_info(url)
            
            # Call the scraper
            df = scrape_booking_reviews(url, max_reviews)
            
            if not df.empty:
                # Get the filename that was used to save the CSV
                csv_filename = f"booking_reviews_{property_name}.csv"
                message = f"Successfully scraped {len(df)} reviews for {property_name}. Check {csv_filename}"
                result = {
                    'total_reviews': len(df),
                    'filename': csv_filename,
                    'property_name': property_name
                }
            else:
                message = "No reviews were found or an error occurred during scraping."
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            message = f"An error occurred: {str(e)}"
    
    return render_template('index.html', message=message, result=result)

@app.route('/api/booking', methods=['POST'])
def api_booking():
    """
    API endpoint for Booking.com scraper.
    Accepts JSON input in the form:
    {
      "url": "https://www.booking.com/hotel/gb/london-visitors.html",
      "max_reviews": 100  # Optional
    }
    Returns JSON with the scraped reviews or an error.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON payload provided."}), 400
        
        url = data.get('url')
        max_reviews = data.get('max_reviews')  # Optional
        
        if not url:
            return jsonify({"error": "Booking.com URL is required."}), 400
        
        # Validate URL
        if not validate_booking_url(url):
            return jsonify({"error": "Invalid Booking.com URL format."}), 400
        
        # Call the scraper
        df = scrape_booking_reviews(url, max_reviews)
        
        if df.empty:
            return jsonify({"error": "No reviews found or an error occurred."}), 200
        
        # Get property info for response
        property_type, country_code, property_name = extract_property_info(url)
        
        # Convert DataFrame to list of dictionaries
        reviews_list = df.to_dict(orient='records')
        
        return jsonify({
            "success": True,
            "url": url,
            "property_name": property_name,
            "max_reviews_requested": max_reviews,
            "reviews_returned": len(reviews_list),
            "reviews": reviews_list
        }), 200
    
    except Exception as e:
        logger.error(f"[ERROR] /api/booking -> {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)