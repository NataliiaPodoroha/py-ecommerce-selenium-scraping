from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import csv
import time


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES = {
    "home": f"{HOME_URL}",
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)


def accept_cookies() -> None:
    try:
        cookies_button = WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable(
                (By.ID, "closeCookieBanner")
            )
        )
        cookies_button.click()
    except Exception as e:
        print(e)


def load_all_products_on_page(expected_count: int) -> None:
    while True:
        try:
            page_soup = BeautifulSoup(driver.page_source, "html.parser")
            product_count = len(page_soup.select(".thumbnail"))

            if product_count >= expected_count:
                break

            more_button = WebDriverWait(driver, 10).until(
                ec.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
            )

            try:
                more_button.click()
                time.sleep(1)
            except ElementClickInterceptedException:
                accept_cookies()
                time.sleep(1)

        except TimeoutException:
            break


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    reviews_tag = product_soup.select_one(".review-count")
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon.ws-icon-star")),
        num_of_reviews=int(reviews_tag.text.split()[0]) if reviews_tag else 0,
    )


def save_to_csv(products: [Product], filename: str) -> None:
    with open(filename, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_single_page_products(url: str, expected_count: int) -> [Product]:
    driver.get(url)
    accept_cookies()

    load_all_products_on_page(expected_count)

    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    product_soups = page_soup.select(".thumbnail")

    products = []
    for product_soup in product_soups:
        product = parse_single_product(product_soup)
        products.append(product)

    return products


def get_all_products() -> None:
    pages = {
        "home": (PAGES["home"], 3),
        "computers": (PAGES["computers"], 3),
        "laptops": (PAGES["laptops"], 117),
        "tablets": (PAGES["tablets"], 21),
        "phones": (PAGES["phones"], 3),
        "touch": (PAGES["touch"], 9),
    }

    for page_name, (page_url, expected_count) in pages.items():
        products = get_single_page_products(page_url, expected_count)
        save_to_csv(products, f"{page_name}.csv")
        print(f"Saved {len(products)} products to {page_name}.csv")


if __name__ == "__main__":
    get_all_products()
    driver.quit()
