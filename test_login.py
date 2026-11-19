import os
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://the-internet.herokuapp.com"
VALID_USER = "tomsmith"
VALID_PASSWORD = "SuperSecretPassword!"
HEADLESS = os.getenv("HEADLESS", "0") == "1"
SHOT_DIR = "screenshots"


def make_driver(browser):
    """Створює драйвер потрібного браузера (за потреби в headless-режимі)."""
    if browser == "chrome":
        opts = webdriver.ChromeOptions()
        if HEADLESS:
            opts.add_argument("--headless=new")
        return webdriver.Chrome(options=opts)
    if browser == "firefox":
        opts = webdriver.FirefoxOptions()
        if HEADLESS:
            opts.add_argument("-headless")
        return webdriver.Firefox(options=opts)
    raise ValueError(f"Невідомий браузер: {browser}")


class LoginTests:
    """Спільні тести. Конкретний браузер задається у дочірніх класах."""
    browser = None

    def setUp(self):
        os.makedirs(SHOT_DIR, exist_ok=True)
        self.driver = make_driver(self.browser)
        self.driver.set_window_size(1280, 900)
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.get(f"{BASE_URL}/login")

    def tearDown(self):
        try:
            self.driver.save_screenshot(f"{SHOT_DIR}/{self.id()}.png")
        finally:
            self.driver.quit()

    # ── допоміжні методи ──
    def login(self, username, password):
        self.wait.until(EC.presence_of_element_located((By.ID, "username")))
        self.driver.find_element(By.ID, "username").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button.radius").click()

    def flash_text(self):
        flash = self.wait.until(
            EC.visibility_of_element_located((By.ID, "flash")))
        return flash.text

    # ── тести ──
    def test_login_success(self):
        """Вхід з правильними даними показує повідомлення про успіх."""
        self.login(VALID_USER, VALID_PASSWORD)
        self.assertIn("You logged into a secure area!", self.flash_text())
        self.assertTrue(self.driver.current_url.endswith("/secure"))

    def test_login_wrong_password(self):
        """Неправильний пароль дає повідомлення про помилку."""
        self.login(VALID_USER, "wrong-password")
        self.assertIn("Your password is invalid!", self.flash_text())
        self.assertTrue(self.driver.current_url.endswith("/login"))

    def test_login_wrong_username(self):
        """Неіснуючий користувач дає повідомлення про помилку."""
        self.login("no_such_user", VALID_PASSWORD)
        self.assertIn("Your username is invalid!", self.flash_text())

    def test_login_empty_fields(self):
        """Порожня форма не дозволяє увійти."""
        self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.radius"))).click()
        self.assertIn("Your username is invalid!", self.flash_text())

    def test_logout(self):
        """Після виходу користувач повертається на сторінку входу."""
        self.login(VALID_USER, VALID_PASSWORD)
        self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "a[href='/logout']"))).click()
        self.assertIn("You logged out of the secure area!", self.flash_text())
        self.assertTrue(self.driver.current_url.endswith("/login"))

    def test_secure_page_requires_login(self):
        """Без входу захищена сторінка недоступна."""
        self.driver.get(f"{BASE_URL}/secure")
        self.assertIn("You must login to view the secure area!",
                      self.flash_text())
        self.assertTrue(self.driver.current_url.endswith("/login"))


class TestLoginChrome(LoginTests, unittest.TestCase):
    browser = "chrome"


class TestLoginFirefox(LoginTests, unittest.TestCase):
    browser = "firefox"


if __name__ == "__main__":
    unittest.main(verbosity=2)