# scrapers/booking_scraper.py
import time
import pandas as pd
import re
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging
from scrapers.utils import extract_property_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Create log filename with timestamp
log_filename = os.path.join(log_dir, f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()  # This will continue to print to console as well
    ]
)
logger = logging.getLogger(__name__)

def setup_driver():
    """Set up and return a configured Chrome WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # Add user-agent to avoid detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_review_count(driver, url):
    """Extract the total number of reviews from the hotel page."""
    try:
        # Navigate to the reviews tab
        if '#tab-reviews' not in url:
            reviews_url = f"{url}#tab-reviews"
        else:
            reviews_url = url
            
        driver.get(reviews_url)
        time.sleep(5)  # Allow page to load
        
        # Try to find elements that contain review counts
        count_elements = driver.find_elements(By.XPATH, 
                                             "//*[contains(text(), 'reviews') or contains(text(), 'Reviews')]")
        
        for element in count_elements:
            text = element.text
            match = re.search(r'(\d[\d,\.]+)\s*reviews', text, re.IGNORECASE)
            if match:
                count = match.group(1).replace(',', '').replace('.', '')
                return int(count)
        
        # If the above didn't work, try another approach
        heading_element = driver.find_element(By.XPATH, "//h2[contains(text(), 'Guest reviews')]")
        if heading_element:
            heading_text = heading_element.text
            match = re.search(r'(\d[\d,\.]+)', heading_text)
            if match:
                count = match.group(1).replace(',', '').replace('.', '')
                return int(count)
                
        return 0
        
    except Exception as e:
        logger.error(f"Error getting review count: {e}")
        return 0

def scrape_reviews_from_page(driver):
    """Extract all reviews from the current page with targeted element extraction."""
    reviews = []
    
    try:
        # Wait for reviews to load
        time.sleep(5)
        
        # The main review containers on Booking.com
        review_containers = driver.find_elements(By.CSS_SELECTOR, "[data-testid='review-card']")
        
        logger.info(f"Found {len(review_containers)} review containers")
        
        for idx, container in enumerate(review_containers):
            try:
                review_data = {}
                
                # Get reviewer name
                try:
                    name_element = container.find_element(By.CSS_SELECTOR, ".a3332d346a.e6208ee469")
                    review_data['reviewer_name'] = name_element.text.strip()
                except:
                    review_data['reviewer_name'] = "Anonymous"
                
                # Get reviewer country
                try:
                    country_element = container.find_element(By.CSS_SELECTOR, ".afac1f68d9.a1ad95c055")
                    review_data['reviewer_country'] = country_element.text.strip()
                except:
                    review_data['reviewer_country'] = ""
                
                # Get review date
                try:
                    date_element = container.find_element(By.CSS_SELECTOR, "[data-testid='review-date']")
                    date_text = date_element.text.strip()
                    if "Reviewed:" in date_text:
                        review_data['review_date'] = date_text.replace("Reviewed:", "").strip()
                    else:
                        review_data['review_date'] = date_text
                except:
                    review_data['review_date'] = ""
                
                # Get rating score
                try:
                    rating_element = container.find_element(By.CSS_SELECTOR, ".a3b8729ab1 div + div")
                    review_data['rating'] = rating_element.text.strip()
                except:
                    try:
                        # Alternative selector
                        rating_element = container.find_element(By.CSS_SELECTOR, ".a3b8729ab1")
                        review_data['rating'] = rating_element.text.replace("Scored", "").strip()
                    except:
                        review_data['rating'] = ""
                
                # Get review title
                try:
                    title_element = container.find_element(By.CSS_SELECTOR, "[data-testid='review-title']")
                    review_data['review_title'] = title_element.text.strip()
                except:
                    try:
                        # Alternative class-based selector
                        title_element = container.find_element(By.CSS_SELECTOR, ".f6431b446c.c5811cad6b.ee8547574e")
                        review_data['review_title'] = title_element.text.strip()
                    except:
                        review_data['review_title'] = ""
                
                # Get room type
                try:
                    room_element = container.find_element(By.CSS_SELECTOR, "[data-testid='review-room-name']")
                    review_data['room_type'] = room_element.text.strip()
                except:
                    try:
                        # Alternative selector based on the structure
                        room_element = container.find_element(By.CSS_SELECTOR, ".abf093bdfe:not(.d88f1120c1):not(.f45d8e4c32):not(.a1ad95c055)")
                        if "Double" in room_element.text or "King" in room_element.text or "Room" in room_element.text:
                            review_data['room_type'] = room_element.text.strip()
                        else:
                            review_data['room_type'] = ""
                    except:
                        review_data['room_type'] = ""
                
                # Get nights stayed
                try:
                    nights_element = container.find_element(By.CSS_SELECTOR, "[data-testid='review-num-nights']")
                    nights_text = nights_element.text.strip()
                    if "nights" in nights_text or "night" in nights_text:
                        nights_match = re.search(r'(\d+)\s*night', nights_text)
                        if nights_match:
                            review_data['nights_stayed'] = nights_match.group(1)
                        else:
                            review_data['nights_stayed'] = nights_text
                    else:
                        review_data['nights_stayed'] = nights_text
                except:
                    # Fall back to regex on container text
                    try:
                        container_text = container.text
                        nights_match = re.search(r'(\d+)\s*nights?', container_text)
                        if nights_match:
                            review_data['nights_stayed'] = nights_match.group(1)
                        else:
                            review_data['nights_stayed'] = ""
                    except:
                        review_data['nights_stayed'] = ""
                
                # Get stay date
                try:
                    date_element = container.find_element(By.CSS_SELECTOR, "[data-testid='review-stay-date']")
                    review_data['stay_date'] = date_element.text.strip()
                except:
                    # Try to find with class
                    try:
                        date_element = container.find_element(By.CSS_SELECTOR, ".d88f1120c1")
                        review_data['stay_date'] = date_element.text.strip()
                    except:
                        review_data['stay_date'] = ""
                
                # Get traveler type
                try:
                    traveler_element = container.find_element(By.CSS_SELECTOR, "[data-testid='review-traveler-type']")
                    review_data['review_type'] = traveler_element.text.strip()
                except:
                    # Try common traveler types via text search
                    container_text = container.text
                    traveler_types = ["Family", "Solo traveler", "Solo traveller", "Couple", "Business", "Group", "Friends"]
                    for t_type in traveler_types:
                        if t_type in container_text:
                            review_data['review_type'] = t_type
                            break
                    else:
                        review_data['review_type'] = ""
                
                # Get positive review text
                try:
                    pos_element = container.find_element(By.CSS_SELECTOR, "[data-testid='review-positive-text'] .a53cbfa6de")
                    review_data['review_pros'] = pos_element.text.strip()
                except:
                    # Try alternative selector
                    try:
                        pos_element = container.find_element(By.CSS_SELECTOR, ".c402354066 .a53cbfa6de")
                        if pos_element:
                            review_data['review_pros'] = pos_element.text.strip()
                        else:
                            review_data['review_pros'] = ""
                    except:
                        review_data['review_pros'] = ""
                
                # Get negative review text
                try:
                    neg_element = container.find_element(By.CSS_SELECTOR, "[data-testid='review-negative-text'] .a53cbfa6de")
                    review_data['review_cons'] = neg_element.text.strip()
                except:
                    # Try alternative selector based on the positive then next sibling
                    try:
                        neg_elements = container.find_elements(By.CSS_SELECTOR, ".c402354066 .a53cbfa6de")
                        if len(neg_elements) > 1:
                            review_data['review_cons'] = neg_elements[1].text.strip()
                        else:
                            review_data['review_cons'] = ""
                    except:
                        review_data['review_cons'] = ""
                
                # Combine pros and cons for full review text
                if review_data['review_pros'] or review_data['review_cons']:
                    review_text = ""
                    if review_data['review_pros']:
                        review_text += f"Pros: {review_data['review_pros']}\n"
                    if review_data['review_cons']:
                        review_text += f"Cons: {review_data['review_cons']}"
                    review_data['review_text'] = review_text.strip()
                else:
                    review_data['review_text'] = ""
                
                reviews.append(review_data)
                
            except Exception as e:
                logger.error(f"Error extracting review {idx}: {str(e)}")
                continue
    
    except Exception as e:
        logger.error(f"Error scraping reviews from page: {str(e)}")
    
    return reviews

def go_to_next_page(driver):
    """Navigate to the next page of reviews if available."""
    try:
        # Look for next page button
        next_buttons = driver.find_elements(By.XPATH, 
                                          "//button[contains(@aria-label, 'Next') or contains(text(), 'Next')] | //a[contains(@class, 'next') or contains(@aria-label, 'Next')]")
        
        for button in next_buttons:
            if button.is_displayed() and button.is_enabled():
                # Scroll to the button to make it clickable
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(1)
                
                # Click using JavaScript to avoid element intercept issues
                driver.execute_script("arguments[0].click();", button)
                time.sleep(3)  # Wait for the page to load
                return True
        
        # If no dedicated next button found, try pagination by numbers
        current_page = None
        
        # Find the active/current page number
        page_indicators = driver.find_elements(By.CSS_SELECTOR, 
                                             "li.bui-pagination__item--active, span.current")
        for indicator in page_indicators:
            try:
                current_page = int(indicator.text.strip())
                break
            except:
                pass
        
        if current_page:
            next_page = current_page + 1
            # Look for a link with the next page number
            next_page_links = driver.find_elements(By.XPATH, 
                                                 f"//a[contains(@class, 'bui-pagination__link') and text()='{next_page}'] | //a[contains(@class, 'page_link') and text()='{next_page}']")
            
            for link in next_page_links:
                if link.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView(true);", link)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", link)
                    time.sleep(3)
                    return True
        
        logger.info("No next page button found or reached the last page")
        return False
        
    except Exception as e:
        logger.error(f"Error navigating to next page: {e}")
        return False

def scrape_booking_reviews(url, max_reviews=None):
    """
    Main function to scrape all reviews from a Booking.com property.
    
    Args:
        url (str): URL of the Booking.com property
        max_reviews (int, optional): Maximum number of reviews to scrape. 
                                    If None, scrape all reviews.
    
    Returns:
        DataFrame: Pandas DataFrame containing all scraped reviews
    """
    all_reviews = []
    driver = None
    
    try:
        # Set up the WebDriver
        driver = setup_driver()
        
        # Navigate to the reviews tab
        if '#tab-reviews' not in url:
            reviews_url = f"{url}#tab-reviews"
        else:
            reviews_url = url
            
        driver.get(reviews_url)
        time.sleep(10)  # Allow page to load
        
        # Try to handle cookie consent if present
        try:
            cookie_buttons = driver.find_elements(By.XPATH, 
                                                "//button[contains(text(), 'Accept') or contains(@id, 'accept')]")
            for button in cookie_buttons:
                if button.is_displayed():
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
                    break
        except:
            pass
        
        # Ensure we're in the reviews tab
        try:
            review_tabs = driver.find_elements(By.XPATH, 
                                             "//a[contains(@href, '#tab-reviews')] | //button[contains(text(), 'Reviews')]")
            for tab in review_tabs:
                if tab.is_displayed():
                    driver.execute_script("arguments[0].click();", tab)
                    time.sleep(5)
                    break
        except:
            pass
        
        # Get the review count
        total_reviews = get_review_count(driver, url)
        logger.info(f"Found {total_reviews} total reviews")
        
        # Determine how many reviews to scrape
        reviews_to_scrape = min(total_reviews, max_reviews) if max_reviews else total_reviews
        logger.info(f"Will scrape up to {reviews_to_scrape} reviews")
        
        # Scrape all pages until we have enough reviews or reach the end
        page_num = 1
        
        while len(all_reviews) < reviews_to_scrape:
            logger.info(f"Scraping page {page_num}...")
            
            # Scrape reviews from current page
            page_reviews = scrape_reviews_from_page(driver)
            all_reviews.extend(page_reviews)
            
            logger.info(f"Scraped {len(page_reviews)} reviews from page {page_num}")
            logger.info(f"Total reviews scraped so far: {len(all_reviews)}")
            
            # Check if we need more reviews
            if len(all_reviews) >= reviews_to_scrape:
                logger.info(f"Reached target of {reviews_to_scrape} reviews")
                break
                
            # Try to go to next page
            if not go_to_next_page(driver):
                logger.info("No more pages available")
                break
                
            page_num += 1
            
        # Create DataFrame from collected reviews
        if all_reviews:
            df = pd.DataFrame(all_reviews)
            
            # Add ID column
            df.insert(0, 'id', range(1, len(df) + 1))
            
            # Select and order columns as requested - removing pros and cons columns
            columns = [
                'id', 'reviewer_name', 'reviewer_country', 'stay_date', 'review_type', 
                'review_date', 'room_type', 'nights_stayed', 'rating', 'review_title',
                'review_text'
            ]
            
            # Make sure all required columns exist
            for col in columns:
                if col not in df.columns and col != 'id':
                    df[col] = ""
            
            df = df[columns]
            
            # Save to CSV
            property_name = url.split('/')[-1].split('.')[0]
            csv_filename = f"booking_reviews_{property_name}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            
            logger.info(f"Saved {len(df)} reviews to {csv_filename}")
            return df
            
        else:
            logger.warning("No reviews were scraped")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error in scrape_booking_reviews: {e}")
        return pd.DataFrame()
        
    finally:
        # Clean up
        if driver:
            driver.quit()