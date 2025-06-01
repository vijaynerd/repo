from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def get_movie_showtimes_chennai(date_str="2025-06-01"):
    # Setup Chrome options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(options=options)

    try:
        # Navigate to BookMyShow Chennai
        url = "https://in.bookmyshow.com/explore/movies-chennai"
        driver.get(url)

        wait = WebDriverWait(driver, 15)

        # Wait for movies to load
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "__movie-name")))

        # Click on the date picker if needed
        print(f"Browsing movies in Chennai for {date_str}...\n")

        # Get movie links
        movie_elements = driver.find_elements(By.CSS_SELECTOR, 'a.__movie-card')
        movie_links = [elem.get_attribute("href") for elem in movie_elements]

        movie_data = {}

        for link in movie_links:
            driver.get(link)

            try:
                # Wait for showtimes to load
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "__venue-name")))
                movie_title = driver.find_element(By.CLASS_NAME, "__event-name").text.strip()

                theatres = driver.find_elements(By.CLASS_NAME, "__venue-name")
                showtimes_sections = driver.find_elements(By.CLASS_NAME, "__showtime-link")

                showtimes_by_theatre = {}

                for theatre in theatres:
                    theatre_name = theatre.text.strip()
                    showtimes = theatre.find_elements(By.XPATH, "../following-sibling::div//a[contains(@class, '__showtime-link')]")
                    times = [s.text.strip() for s in showtimes if s.text.strip()]
                    if times:
                        showtimes_by_theatre[theatre_name] = times

                if showtimes_by_theatre:
                    movie_data[movie_title] = showtimes_by_theatre

            except Exception as e:
                print(f"Error parsing movie: {link}\n{e}")
                continue

        return movie_data

    finally:
        driver.quit()

# Example usage
if __name__ == "__main__":
    data = get_movie_showtimes_chennai("2025-06-01")
    for movie, theatres in data.items():
        print(f"\n🎬 {movie}")
        for theatre, times in theatres.items():
            print(f"  📍 {theatre}: {', '.join(times)}")