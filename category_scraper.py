import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

def scrape_categories_from_directory(url, driver):
    """
    Scrapes all categories from the Amazon site directory page.

    Args:
        url (str): The URL of the Amazon site directory page.
        driver: An active Selenium WebDriver instance.

    Returns:
        list: A list of dictionaries, each containing a category name and URL.
    """
    print(f"Scraping categories from directory: {url}")
    
    # This selector targets the links within the department columns on the site directory page.
    CATEGORY_LINK_SELECTOR = 'div.fsdDeptCol a'
    
    categories_data = []

    try:
        driver.get(url)
        
        # Wait for the category links to be present on the page
        category_links = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, CATEGORY_LINK_SELECTOR))
        )
        
        print(f"Found {len(category_links)} category links.")

        for link_element in category_links:
            try:
                category_name = link_element.text.strip()
                category_url = link_element.get_attribute('href')
                
                # Ensure the link is valid and not empty
                if category_name and category_url:
                    categories_data.append({
                        'Category': category_name,
                        'URL': category_url
                    })
                    print(f"  - Found: {category_name}")

            except Exception as e:
                print(f"  - Could not process a category link. Error: {e}")
        
        return categories_data

    except Exception as e:
        print(f"  - An error occurred while trying to scrape the directory page. Error: {e}")
        driver.save_screenshot('debug_directory_error.png')
        print("  - Saved a screenshot of the error to 'debug_directory_error.png'")
        return []

def main():
    """Main function to run the category scraper."""
    # This URL points to Amazon South Africa's main department directory.
    AMAZON_DIRECTORY_URL = "https://www.amazon.co.za/gp/site-directory"

    print("Starting Amazon Category Scraper...")
    
    # --- Selenium Setup ---
    service = ChromeService(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # You can run in headless mode again now that the strategy is more stable
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
    
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)

    # --- Scrape and Save ---
    categories = scrape_categories_from_directory(AMAZON_DIRECTORY_URL, driver)
    
    driver.quit()

    if not categories:
        print("\nProcess complete. No categories were found. Amazon's layout may have changed.")
        return

    # --- Save to Excel ---
    df = pd.DataFrame(categories)
    output_filename = "amazon_categories.xlsx"
    print(f"\nScraping complete. Saving {len(categories)} categories to '{output_filename}'...")
    df.to_excel(output_filename, index=False)
    print(f"Success! Open '{output_filename}' to see the list of categories.")

if __name__ == "__main__":
    main()
