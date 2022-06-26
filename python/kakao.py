import chromedriver_binary
import json
import logging
import requests
import time
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from typing import BinaryIO, List, Tuple
from .sender import Sender, SenderType

class Kakao(Sender):
    kakao_auth_url = "https://kauth.kakao.com/oauth/authorize"
    kakao_token_url = "https://kauth.kakao.com/oauth/token"
    kakao_redirect_url = "https://example.com/oauth"
    kakao_msg_url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

    def __init__(self,
            kakao_rest_api_key: str,
            kakao_id: str,
            kakao_pw: str,
            logger: logging.Logger
        ):
        super().__init__(SenderType.KAKAO)

        if not kakao_rest_api_key or len(kakao_rest_api_key) <= 0:
            raise ValueError("kakao_rest_api_key must be set")
        
        if not kakao_id or len(kakao_id) <= 0:
            raise ValueError("kakao_id must be set")

        if not kakao_pw or len(kakao_pw) <= 0:
            raise ValueError("kakao_pw must be set")

        self.kakao_rest_api_key: str = kakao_rest_api_key   # The rest api key of kakao app
        self.id: str = kakao_id                       # User ID of app owner
        self.pw: str = kakao_pw                       # User password of app owner
        self.kakao_auth_code: str = None                    # The authorization code obtained from kakao_auth_url
        self.kakao_refresh_token: str = None                # The refresh token obtained from kakao_token_url
        self.kakao_refresh_token_expire: int = None         # The expired time of refresh token
        self.kakao_access_token: str = None                 # The access token obtained from kakao_token_url
        self.kakao_access_token_expire: int = None          # The expired time of access token
        self.logger = logger

    def get_auth(self):
        ''' get_auth updates authorization code, refresh token and access token.
        If the refresh token wasn't obtained or expired, this function should be called to refresh tokens.
        '''
        self.logger.info("Update kakao auth")

        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            driver = webdriver.Chrome(options=chrome_options)
            driver.get("%s?client_id=%s&redirect_uri=%s&response_type=code&scope=talk_message"
                %(Kakao.kakao_auth_url, self.kakao_rest_api_key, Kakao.kakao_redirect_url))

            # Put user ID and password into the login form
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "form#login-form")))
            id_input = driver.find_element(by=By.CSS_SELECTOR, value="input#id_email_2")
            pw_input = driver.find_element(by=By.CSS_SELECTOR, value="input#id_password_3")
            login_button = driver.find_element(by=By.CSS_SELECTOR, value="form#login-form button.btn_confirm")

            # Do login
            id_input.send_keys(self.id)
            pw_input.send_keys(self.pw)
            login_button.click()

            # Wait for redirection to kakao_redirect_url or agreement page
            WebDriverWait(driver, 20).until(lambda driver: Kakao.kakao_redirect_url in driver.current_url or
                driver.find_element(by=By.CSS_SELECTOR, value="input#agreeAll"))

            if Kakao.kakao_redirect_url not in driver.current_url:
                # If the page landed to the agreement page, agree sending messages by app
                agree_all_button = driver.find_element(by=By.CSS_SELECTOR, value="input#agreeAll")
                accept_button = driver.find_element(by=By.CSS_SELECTOR, value="button#acceptButton")
                driver.execute_script("arguments[0].click();", agree_all_button)
                accept_button.click()
                WebDriverWait(driver, 20).until(EC.url_contains(Kakao.kakao_redirect_url))

            # If code reaches here, the current url should be kakao_redirect_url
            # We can parse authorizaion code from the url
            code = urlparse(driver.current_url)
            self.kakao_auth_code = parse_qs(code.query)["code"][0]
            driver.quit()

            # Get refresh token and access token from kakao_redirect_url
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.kakao_rest_api_key,
                'redirect_uri': self.kakao_redirect_url,
                'code': self.kakao_auth_code,
            }
            response = requests.post(self.kakao_token_url, data=data)
            tokens = response.json()

            # Parse tokens and calculate expire time
            current_time = time.time()
            self.kakao_refresh_token = tokens["refresh_token"]
            self.kakao_refresh_token_expire = tokens["refresh_token_expires_in"] + current_time - (10 * 60) # give 10min margin
            self.kakao_access_token = tokens["access_token"]
            self.kakao_access_token_expire = tokens["expires_in"] + current_time - (10 * 60) # give 10min margin

            self.logger.info("Kakao auth updated")
            self.logger.debug("- Kakao auth code: %s", self.kakao_auth_code)
            self.logger.debug("- Kakao refresh code: %s", self.kakao_refresh_token)
            self.logger.debug("- Kakao access code: %s", self.kakao_access_token)
        except Exception as e:
            self.logger.error("Failed to update kakao auth: %s", str(e))

    def get_access_token(self):
        ''' get_access_token obtains the access token.
        If the refresh token is expired, it will call `get_auth` function.
        '''
        if self.kakao_access_token_expire > time.time():
            # We don't have to refresh access token
            return

        if self.kakao_refresh_token_expire <= time.time():
            # The refresh token is expired,
            # we have to refresh both refresh token and access token
            self.get_auth()
            return

        self.logger.info("Refresh kakao access token")

        try:
            # Get access token from kakao_redirect_url using refresh token
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.kakao_rest_api_key,
                'refresh_token': self.kakao_refresh_token,
            }
            response = requests.post(self.kakao_token_url, data=data)
            tokens = response.json()

            # Parse tokens and calculate expire time
            current_time = time.time()
            self.kakao_access_token = tokens["access_token"]
            self.kakao_access_token_expire = tokens["expires_in"] + current_time - (10 * 60) # give 10min margin

            self.logger.info("Kakao access code updated")
            self.logger.debug("- kakao access code: %s", self.kakao_access_token)
        except Exception as e:
            self.logger.error("Failed to refresh kakao access token: %s", str(e))

    def send(self, subject: str = "", content: str = "", attachments: List[Tuple[str, str, str, BinaryIO]] = [], receiver: List[str] = []):
        ''' kakao_send_msg sends message to the app user.
        The access token should be obtained, before call this function.
        '''
        # Before send message, refresh access token
        self.refresh_access_token()
        self.logger.info("Send kakao message: %s", content)

        try:
            header = {'Authorization': 'Bearer ' + self.kakao_access_token}
            post = {
                'object_type': 'text',
                'text': content,
                'link': {
                    'web_url': 'https://developers.kakao.com',
                    'mobile_web_url': 'https://developers.kakao.com'
                }
            }
            data = {'template_object': json.dumps(post)}

            requests.post(Kakao.kakao_msg_url, headers=header, data=data)
        except Exception as e:
            self.logger.error("Failed to send kakao message: %s", str(e))

    def refresh_access_token(self):
        if not self.kakao_auth_code:
            self.get_auth()
        self.get_access_token()

    def get_token(self) -> dict:
        return {
            "kakao_rest_api_key": self.kakao_rest_api_key,
            "kakao_auth_code": self.kakao_auth_code,
            "kakao_refresh_token": self.kakao_refresh_token,
            "kakao_refresh_token_expire": self.kakao_refresh_token_expire,
            "kakao_access_token": self.kakao_access_token,
            "kakao_access_token_expire": self.kakao_access_token_expire,
        }

    def set_token(self, token: dict):
        if token["kakao_rest_api_key"] != self.kakao_rest_api_key:
            self.logger.debug("Kakao rest api key is changed, don't use the previous token")
            return

        self.kakao_auth_code = token["kakao_auth_code"]
        self.kakao_refresh_token = token["kakao_refresh_token"]
        self.kakao_refresh_token_expire = token["kakao_refresh_token_expire"]
        self.kakao_access_token = token["kakao_access_token"]
        self.kakao_access_token_expire = token["kakao_access_token_expire"]