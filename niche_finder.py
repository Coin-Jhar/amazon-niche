import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

# --- Step 1: Define Your Niche Finding Criteria ---
# These are the filters for your ideal product.
MIN_PRICE = 300
MAX_PRICE = 800
MAX_BSR = 20000
MAX_REVIEWS = 400

def get_product_links(search_url, driver):
    """Gets all the product links from a search results page."""
    print(f"Getting product links from: {search_url}")
    driver.get(search_url)
    time.sleep(2) # Allow page to load
    
    # Find all product link elements on the page
    link_elements = driver.find_elements(By.CSS_SELECTOR, 'a.a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal')
    
    product_links = [elem.get_attribute('href') for elem in link_elements]
    print(f"Found {len(product_links)} product links.")
    return product_links

def scrape_product_details(url, driver):
    """Scrapes the details from a single product page."""
    print(f"-> Scraping details for: {url.split('?')[0]}...")

    CONFIG = {
        'cookie_accept_selector': '#sp-cc-accept',
        'title_selector': '#productTitle',
        'price_selector': 'span.a-price-whole',
        'reviews_selector': '#acrCustomerReviewText',
        # This selector is more complex as BSR can be in different places
        'bsr_selector': '#detailBullets_feature_div .a-list-item, #productDetails_detailBullets_sections1 .a-list-item'
    }

    try:
        driver.get(url)
        
        # Handle cookie banner if it appears
        try:
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, CONFIG['cookie_accept_selector']))).click()
            time.sleep(1)
        except:
            pass # Ignore if no cookie banner

        # Wait for the title to ensure the main content is loaded
        title_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, CONFIG['title_selector'])))
        title = title_element.text.strip()
        
        # Extract Price
        price_text = driver.find_element(By.CSS_SELECTOR, CONFIG['price_selector']).text
        price = float(price_text.replace(',', '').replace(' ', ''))

        # Extract Review Count
        try:
            reviews_text = driver.find_element(By.CSS_SELECTOR, CONFIG['reviews_selector']).text
            reviews = int(reviews_text.replace(',', '').split()[0])
        except:
            reviews = 0 # If no reviews, set to 0

        # Extract Best Sellers Rank (BSR)
        bsr = None
        try:
            # Find all potential BSR list items
            bsr_elements = driver.find_elements(By.CSS_SELECTOR, CONFIG['bsr_selector'])
            for elem in bsr_elements:
                if "Best Sellers Rank" in elem.text:
                    # Use regex to find the first number in the string
                    match = re.search(r'#([\d,]+)', elem.text)
                    if match:
                        bsr = int(match.group(1).replace(',', ''))
                        break
        except:
            bsr = None # If no BSR found

        return {
            'Title': title, 'Price': price, 'Reviews': reviews, 'BSR': bsr, 'URL': url
        }

    except Exception as e:
        print(f"   - Could not scrape details. Error: {e}")
        return None

def main():
    """Main function to find product niches."""
    # --- Step 2: Enter the Amazon search URL for the niche you want to analyze ---
    search_urls = [
        "https://www.amazon.co.za/s?k=portable+gas+braai",
        # You can add more search URLs here to analyze multiple niches at once
        # "https://www.amazon.co.za/s?k=digital+meat+thermometer",
    ]

    all_products = []

    print("Starting Amazon Niche Finder...")
    service = ChromeService(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
    
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)

    for search_url in search_urls:
        links = get_product_links(search_url, driver)
        for link in links:
            details = scrape_product_details(link, driver)
            if details:
                all_products.append(details)
            time.sleep(1) # Be respectful

    driver.quit()

    if not all_products:
        print("\nProcess complete. No product data was collected.")
        return

    # --- Step 3: Analyze the Data ---
    df = pd.DataFrame(all_products)
    
    # Apply filters to see which products meet our criteria
    df['Meets Criteria'] = (
        (df['Price'] >= MIN_PRICE) &
        (df['Price'] <= MAX_PRICE) &
        (df['BSR'] <= MAX_BSR) &
        (df['Reviews'] <= MAX_REVIEWS) &
        (df['BSR'].notna()) # Ensure BSR exists
    )
    
    # Calculate a simple Opportunity Score (lower is better)
    # We want low BSR and low reviews.
    df['Opportunity Score'] = df['BSR'] + (df['Reviews'] * 50) # Weight reviews higher
    
    # Sort by score to bring the best opportunities to the top
    df = df.sort_values(by='Opportunity Score', ascending=True)

    # --- Step 4: Save to Excel ---
    output_filename = "amazon_niche_analysis.xlsx"
    print(f"\nAnalysis complete. Saving results to '{output_filename}'...")
    df.to_excel(output_filename, index=False)
    print(f"Success! Open '{output_filename}' to see the best opportunities.")

if __name__ == "__main__":
    main()
