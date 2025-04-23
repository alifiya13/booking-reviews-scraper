# scrapers/utils.py
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_booking_url(url):
    """Validate that the URL is a proper Booking.com hotel URL."""
    if not url:
        return False
        
    pattern = r'https?://www\.booking\.com/hotel/[a-z]{2}/[^/]+\.html'
    if re.match(pattern, url):
        return True
    return False

def extract_property_info(url):
    """Extract property type, country code, and property name from URL."""
    match = re.match(r'https?://www\.booking\.com/([^/]+)/([^/]+)/([^.]+)\.html', url)
    if match:
        property_type = match.group(1)  # hotel
        country_code = match.group(2)   # gb
        property_name = match.group(3)  # london-visitors
        return property_type, country_code, property_name
    return None, None, None