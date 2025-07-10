import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth # Import the stealth library

def get_product_details(url, driver):
    """
    Fetches a single Amazon product page using Selenium and scrapes its details.

    Args:
        url (str): The URL of the Amazon product page.
        driver: An active Selenium WebDriver instance.

    Returns:
        dict: A dictionary containing the product's title, price, and review count,
              or None if scraping fails.
    """
    print(f"Scraping: {url}")

    # CSS selectors for the product page.
    CONFIG = {
        'cookie_accept_selector': '#sp-cc-accept', # Selector for the cookie accept button
        'title_selector': '#productTitle',
        'price_selector': 'span.a-price-whole',
        'reviews_selector': '#acrCustomerReviewText'
    }

    try:
        # Navigate to the URL
        driver.get(url)

        # --- Step 1: Handle the Cookie Consent Banner ---
        try:
            # Wait up to 5 seconds for the cookie button to be clickable, then click it.
            cookie_accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, CONFIG['cookie_accept_selector']))
            )
            cookie_accept_button.click()
            print("  - Clicked the cookie consent button.")
            # Wait a moment for the banner to disappear
            time.sleep(1)
        except Exception:
            # If the button isn't found after 5 seconds, assume it's not there and continue.
            print("  - Cookie consent button not found, continuing...")
            pass

        # --- Step 2: Wait for the main product content to load ---
        wait = WebDriverWait(driver, 15)
        title_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, CONFIG['title_selector'])))
        
        # --- Step 3: Extract Data ---
        title = title_element.text.strip()
        
        price_text = driver.find_element(By.CSS_SELECTOR, CONFIG['price_selector']).text
        # CORRECTED: Remove both commas and spaces before converting to a float
        price = float(price_text.replace(',', '').replace(' ', '')) if price_text else 0.0

        reviews_text = driver.find_element(By.CSS_SELECTOR, CONFIG['reviews_selector']).text
        reviews = int(reviews_text.replace(',', '').split()[0]) if reviews_text else 0

        print(f"  + Success: Found '{title}'")

        return {
            'Title': title,
            'Price': price,
            'Review Count': reviews,
            'URL': url
        }

    except Exception as e:
        print(f"  - An error occurred while scraping {url}. Amazon might be showing a CAPTCHA.")
        print(f"  - Details: {e}")
        driver.save_screenshot('debug_screenshot.png')
        print("  - Saved a screenshot to 'debug_screenshot.png' for inspection.")
        return None

def main():
    """
    Main function to orchestrate the scraping process.
    """
    urls_to_scrape = [
        # Using the cleaned version of your new URL
        "https://www.amazon.co.za/dp/B0BF5Y24FJ",
    ]

    all_product_data = []

    print("Starting Amazon product scraper with Selenium Stealth...")

    # --- Selenium Setup ---
    service = ChromeService(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
    
    # --- Apply Stealth Patches ---
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    # --- Scraping Loop ---
    for url in urls_to_scrape:
        product_details = get_product_details(url, driver)
        if product_details:
            all_product_data.append(product_details)
        time.sleep(1)

    # --- Cleanup ---
    driver.quit()

    # --- Save to Excel ---
    if not all_product_data:
        print("\nScraping complete, but no data was collected.")
        return

    output_filename = "amazon_product_data.xlsx"
    print(f"\nScraping complete. Saving data to '{output_filename}'...")

    df = pd.DataFrame(all_product_data)
    df.to_excel(output_filename, index=False)
    print(f"Success! Your data has been saved to '{output_filename}'.")


if __name__ == "__main__":
    main()
