import argparse
import chromedriver_binary
import json
import os
import requests
import socket
import threading
import time
from datetime import datetime
from flask import Flask, send_from_directory
from selenium import webdriver
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class Citations(Flask):
    scholar_url = "https://scholar.google.com/citations?user=DdhlAfgAAAAJ&hl=en"
    kakao_auth_url = "https://kauth.kakao.com/oauth/authorize"
    kakao_token_url = "https://kauth.kakao.com/oauth/token"
    kakao_redirect_url = "https://example.com/oauth"
    kakao_msg_url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

    def __init__(self,
            kakao_rest_api_key: str,
            kakao_id: str,
            kakao_pw: str,
            check_interval: int=300,
            sc_path: str="./screenshots",
            domain: str="",
            http_port: str="8080"
        ):
        super().__init__(__name__)

        self.sc_path: str = os.path.abspath(sc_path)        # The absoulute path of screenshots directory
        self.domain: str = domain                           # Domain name of the server, it will be used for the url of screenshot
        self.http_port: str = http_port                     # The port of http server

        # If the domain is not specified, use the local IP address instead
        if not self.domain or len(self.domain) <= 0:
            self.domain = socket.gethostbyname(socket.gethostname())

        if not kakao_rest_api_key or len(kakao_rest_api_key) <= 0:
            raise ValueError("kakao_rest_api_key must be set")
        
        if not kakao_id or len(kakao_id) <= 0:
            raise ValueError("kakao_id must be set")

        if not kakao_pw or len(kakao_pw) <= 0:
            raise ValueError("kakao_pw must be set")

        self.kakao_rest_api_key: str = kakao_rest_api_key   # The rest api key of kakao app
        self.kakao_id: str = kakao_id                       # User ID of app owner
        self.kakao_pw: str = kakao_pw                       # User password of app owner
        self.kakao_auth_code: str = None                    # The authorization code obtained from kakao_auth_url
        self.kakao_refresh_token: str = None                # The refresh token obtained from kakao_token_url
        self.kakao_refresh_token_expire: int = None         # The expired time of refresh token
        self.kakao_access_token: str = None                 # The access token obtained from kakao_token_url
        self.kakao_access_token_expire: int = None          # The expired time of access token

        self.check_interval: int = check_interval
        self.check_thread: threading.Timer = None

        self.last_citations: int = None
        self.last_screenshot: str = None

        try:
            if not os.path.exists(self.sc_path):
                os.makedirs(self.sc_path)
        except:
            raise RuntimeError("Failed to create dir: " + self.sc_path)

        self.screenshots_uri = "/citations/screenshots"
        self.add_url_rule(self.screenshots_uri + "/<path:name>", view_func=self.send_screenshot)

    def update_citations(self) -> bool:
        ''' update_citations updates the number of citations.
        The latest number of citations will be stored in self.last_citations,
        and the filename of the screenshot will be stored in self.last_screenshot.

        Returns: Returns True if updated
        '''
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--window-size=3840,2160")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(Citations.scholar_url)

        # Parse html elements to get citations
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table#gsc_rsb_st td.gsc_rsb_std")))
        citations_tds = driver.find_elements(by=By.CSS_SELECTOR, value="table#gsc_rsb_st td.gsc_rsb_std")
        current_citations = int(citations_tds[0].text)

        # Check the number of citations is updated or not
        if self.last_citations and self.last_citations == current_citations:
            return False

        # The number of citations is updated
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.last_citations = current_citations
        self.last_screenshot = "%s_%d.png" %(current_time, self.last_citations)

        # Get screenshot of the page
        driver.set_window_size(3840, 2160)
        driver.save_screenshot("%s/%s" %(self.sc_path, self.last_screenshot))
        driver.quit()

        print("citations updated: %d" %(self.last_citations))

        return True

    def kakao_auth(self):
        ''' kakao_auth updates authorization code, refresh token and access token.
        If the refresh token wasn't obtained or expired, this function should be called to refresh tokens.
        '''
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("%s?client_id=%s&redirect_uri=%s&response_type=code&scope=talk_message"
            %(Citations.kakao_auth_url, self.kakao_rest_api_key, Citations.kakao_redirect_url))

        # Put user ID and password into the login form
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "form#login-form")))
        id_input = driver.find_element(by=By.CSS_SELECTOR, value="input#id_email_2")
        pw_input = driver.find_element(by=By.CSS_SELECTOR, value="input#id_password_3")
        login_button = driver.find_element(by=By.CSS_SELECTOR, value="form#login-form button.btn_confirm")

        # Do login
        id_input.send_keys(self.kakao_id)
        pw_input.send_keys(self.kakao_pw)
        login_button.click()

        # Wait for redirection to kakao_redirect_url or agreement page
        WebDriverWait(driver, 20).until(lambda driver: Citations.kakao_redirect_url in driver.current_url or
            driver.find_element(by=By.CSS_SELECTOR, value="input#agreeAll"))

        if Citations.kakao_redirect_url not in driver.current_url:
            # If the page landed to the agreement page, agree sending messages by app
            agree_all_button = driver.find_element(by=By.CSS_SELECTOR, value="input#agreeAll")
            accept_button = driver.find_element(by=By.CSS_SELECTOR, value="button#acceptButton")
            driver.execute_script("arguments[0].click();", agree_all_button)
            accept_button.click()
            WebDriverWait(driver, 20).until(EC.url_contains(Citations.kakao_redirect_url))

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

        print("===== kakao auth updated =====")
        print("kakao auth code: %s" %(self.kakao_auth_code))
        print("kakao refresh code: %s" %(self.kakao_refresh_token))
        print("kakao access code: %s" %(self.kakao_access_token))

    def kakao_refresh_access_token(self):
        ''' kakao_refresh_access_token refreshes the access token.
        If the refresh token is expired, it will call `kakao_auth` function.
        '''
        if self.kakao_access_token_expire > time.time():
            # We don't have to refresh access token
            return

        if self.kakao_refresh_token_expire <= time.time():
            # The refresh token is expired,
            # we have to refresh both refresh token and access token
            self.kakao_auth()
            return

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

        print("===== kakao access code updated =====")
        print("kakao access code: %s" %(self.kakao_access_token))

    def kakao_send_msg(self, msg: str):
        ''' kakao_send_msg sends message to the app user.
        The access token should be obtained, before call this function.
        '''
        header = {'Authorization': 'Bearer ' + self.kakao_access_token}
        post = {
            'object_type': 'text',
            'text': msg,
            'link': {
                'web_url': 'https://developers.kakao.com',
                'mobile_web_url': 'https://developers.kakao.com'
            }
        }
        data = {'template_object': json.dumps(post)}

        requests.post(Citations.kakao_msg_url, headers=header, data=data)

    def send_screenshot(self, name):
        return send_from_directory(self.sc_path, name)

    def refresh_kakao_auth(self):
        if not self.kakao_auth_code:
            self.kakao_auth()
        self.kakao_refresh_access_token()

    def repeat_checking_citations(self):
        if self.update_citations():
            self.refresh_kakao_auth()
            self.kakao_send_msg("Citations: %d\nScreenshot: http://%s:%s/%s/%s"
                %(self.last_citations, self.domain, self.http_port, self.screenshots_uri, self.last_screenshot))
        self.check_thread = threading.Timer(self.check_interval, self.repeat_checking_citations)
        self.check_thread.start()

    def run(self):
        self.repeat_checking_citations()
        super().run(host="0.0.0.0", port=self.http_port)
        if self.check_thread:
            self.check_thread.cancel()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sc_path', default="./screenshots", type=str)
    parser.add_argument('--kakao_rest_api_key', default=None, type=str)
    parser.add_argument('--kakao_id', default=None, type=str)
    parser.add_argument('--kakao_pw', default=None, type=str)
    parser.add_argument('--check_interval', default=300, type=int)
    parser.add_argument('--domain', default="", type=str)
    parser.add_argument('--http_port', default="8080", type=str)
    args = parser.parse_args()

    c = Citations(
        kakao_rest_api_key=args.kakao_rest_api_key,
        kakao_id=args.kakao_id,
        kakao_pw=args.kakao_pw,
        check_interval=args.check_interval,
        sc_path=args.sc_path,
        domain=args.domain,
        http_port=args.http_port
    )
    c.run()
