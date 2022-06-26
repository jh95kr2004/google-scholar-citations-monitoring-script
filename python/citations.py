import argparse
import chromedriver_binary
import json
import logging
import os
import socket
import threading
from datetime import datetime
from flask import Flask, send_from_directory
from logging.handlers import TimedRotatingFileHandler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .gmail import Gmail
from .kakao import Kakao
from .sender import Sender, SenderType

class Citations(Flask):
    scholar_url = "https://scholar.google.com/citations?user=DdhlAfgAAAAJ&hl=en"

    def __init__(self,
            kakao_rest_api_key: str,
            kakao_id: str,
            kakao_pw: str,
            gmail_id: str,
            gmail_pw: str,
            check_interval: int=300,
            sc_path: str="./screenshots",
            log_path: str="./log",
            log_file: str="log.txt",
            log_level: int=logging.DEBUG,
            domain: str="",
            http_port: str="8080",
            sender_type: SenderType="gmail"
        ):
        super().__init__(__name__)

        self.sc_path: str = os.path.abspath(sc_path)        # The absolute path of screenshots directory
        self.log_path: str = os.path.abspath(log_path)      # The absolute path of log directory
        self.log_file: str = log_file                       # The name of log file
        self.log_level: int = log_level                     # The level of log
        self.domain: str = domain                           # Domain name of the server, it will be used for the url of screenshot
        self.http_port: str = http_port                     # The port of http server

        try:
            if not os.path.exists(self.sc_path):
                os.makedirs(self.sc_path)
        except:
            raise RuntimeError("Failed to create dir: " + self.sc_path)

        try:
            if not os.path.exists(self.log_path):
                os.makedirs(self.log_path)
        except:
            raise RuntimeError("Failed to create dir: " + self.log_path)

        # Initialize logging
        self.logger = logging.getLogger("Citations")
        self.logger.setLevel(self.log_level)

        f = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
        h = logging.StreamHandler()
        h.setLevel(self.log_level)
        h.setFormatter(f)
        self.logger.addHandler(h)

        h = TimedRotatingFileHandler(filename=os.path.join(self.log_path, self.log_file), when="midnight", backupCount=3)
        h.setLevel(self.log_level)
        h.setFormatter(f)
        self.logger.addHandler(h)

        # If the domain is not specified, use the local IP address instead
        if not self.domain or len(self.domain) <= 0:
            self.domain = socket.gethostbyname(socket.gethostname())

        if sender_type == SenderType.KAKAO.value:
            self.sender: Sender = Kakao(kakao_rest_api_key, kakao_id, kakao_pw, self.logger)
        elif sender_type == SenderType.GMAIL.value:
            self.sender: Sender = Gmail(gmail_id, gmail_pw, self.logger)
        else:
            raise ValueError("invalid sender type: %s" %(sender_type))

        self.check_interval: int = check_interval
        self.check_thread: threading.Timer = None

        self.last_citations: int = None
        self.last_screenshot: str = None

        self.screenshots_uri = "/citations/screenshots"
        self.update_uri = "/citations/update"
        self.latest_uri = "/citations/latest"
        self.add_url_rule(self.screenshots_uri + "/<path:name>", view_func=self.api_send_screenshot)
        self.add_url_rule(self.update_uri, view_func=self.api_update_citations)
        self.add_url_rule(self.latest_uri, view_func=self.api_latest_citations)

        self.load_token()

    def update_citations(self, force: bool=False) -> bool:
        ''' update_citations updates the number of citations.
        The latest number of citations will be stored in self.last_citations,
        and the filename of the screenshot will be stored in self.last_screenshot.

        Returns: Returns True if updated
        '''
        self.logger.info("Start updating citations")

        try:
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
            if not force and self.last_citations and self.last_citations == current_citations:
                self.logger.info("Citations is not updated")
                return False

            # The number of citations is updated
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.last_citations = current_citations
            self.last_screenshot = "%s_%d.png" %(current_time, self.last_citations)

            # Get screenshot of the page
            driver.set_window_size(3840, 2160)
            driver.save_screenshot(os.path.join(self.sc_path, self.last_screenshot))
            driver.quit()

            self.logger.info("Citations updated: %d (force: %s)", self.last_citations, str(force))

            return True
        except Exception as e:
            self.logger.error("Failed to update citations: %s", str(e))
            return False

    def repeat_checking_citations(self):
        if self.update_citations():
            with open(os.path.join(self.sc_path, self.last_screenshot), "rb") as fp:
                self.sender.send(
                    subject="Hanseung Lee Citations: %d" %(self.last_citations),
                    content="Current citations: %d\nScreenshot URL: %s\nUpdate: %s\nLatest: %s"
                        %(self.last_citations, self.create_image_uri(), self.create_update_uri(), self.create_latest_uri()),
                    attachments=[(self.last_screenshot, "image", "png", fp)],
                    receiver=self.sender.id
                )
            self.store_token()
        self.check_thread = threading.Timer(self.check_interval, self.repeat_checking_citations)
        self.check_thread.start()

    def create_image_uri(self):
        return "http://%s:%s%s/%s" %(self.domain, self.http_port, self.screenshots_uri, self.last_screenshot)

    def create_update_uri(self):
        return "http://%s:%s%s" %(self.domain, self.http_port, self.update_uri)

    def create_latest_uri(self):
        return "http://%s:%s%s" %(self.domain, self.http_port, self.latest_uri)

    def run(self):
        self.repeat_checking_citations()
        super().run(host="0.0.0.0", port=self.http_port)
        if self.check_thread:
            self.check_thread.cancel()

    def api_send_screenshot(self, name):
        return send_from_directory(self.sc_path, name)

    def api_update_citations(self):
        self.update_citations(True)
        self.store_token()
        return self.api_latest_citations()

    def api_latest_citations(self):
        image_uri = self.create_image_uri()
        return "Citations: %d<br>Screenshot: <a href=\"%s\">%s</a>" \
            %(self.last_citations, image_uri, image_uri)

    def store_token(self):
        with open(os.path.join(self.log_path, "token.json"), "w") as fp:
            token = {
                "last_citations": self.last_citations,
                "last_screenshot": self.last_screenshot
            }

            if self.sender.sender_type == SenderType.KAKAO:
                token["kakao"] = self.sender.get_token()

            json.dump(token, fp=fp, indent=4)

    def load_token(self):
        token_path = os.path.join(self.log_path, "token.json")
        if not os.path.exists(token_path):
            self.logger.debug("Failed to open token file, maybe the first time of running")
            return

        with open(token_path, "r") as fp:
            token = json.load(fp=fp)
            self.last_citations = token["last_citations"]
            self.last_screenshot = token["last_screenshot"]

            if self.sender.sender_type == SenderType.KAKAO and "kakao" in token:
                self.sender.set_token(token["kakao"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sc_path', default="./screenshots", type=str)
    parser.add_argument('--kakao_rest_api_key', default=None, type=str)
    parser.add_argument('--kakao_id', default=None, type=str)
    parser.add_argument('--kakao_pw', default=None, type=str)
    parser.add_argument('--gmail_id', default=None, type=str)
    parser.add_argument('--gmail_pw', default=None, type=str)
    parser.add_argument('--check_interval', default=300, type=int)
    parser.add_argument('--domain', default="", type=str)
    parser.add_argument('--http_port', default="8080", type=str)
    parser.add_argument('--log_path', default="./log", type=str)
    parser.add_argument('--log_file', default="log.txt", type=str)
    parser.add_argument('--log_level', default="debug", type=str)
    parser.add_argument('--sender_type', default="gmail", type=str)
    args = parser.parse_args()

    print("args:", args.__dict__)

    c = Citations(
        kakao_rest_api_key=args.kakao_rest_api_key,
        kakao_id=args.kakao_id,
        kakao_pw=args.kakao_pw,
        gmail_id=args.gmail_id,
        gmail_pw=args.gmail_pw,
        check_interval=args.check_interval,
        sc_path=args.sc_path,
        log_path=args.log_path,
        log_file=args.log_file,
        log_level=getattr(logging, args.log_level.upper()),
        domain=args.domain,
        http_port=args.http_port,
        sender_type=args.sender_type
    )
    c.run()