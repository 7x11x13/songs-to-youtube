"""This module implements uploading videos on YouTube via Selenium

    Based on https://github.com/linouk23/youtube_uploader_selenium"""

import atexit
import datetime
import glob
import json
import logging
import os
import posixpath
import shutil
import sys
import time
import traceback
import math

from PySide6.QtCore import *
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.service import Service

from .Constant import Constant


class YouTubeLogin:
    @staticmethod
    def get_cookie_path_from_username(username):
        appdata_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        general_cookies_folder_path = posixpath.join(appdata_path, "cookies")
        os.makedirs(general_cookies_folder_path, exist_ok=True)
        return posixpath.join(general_cookies_folder_path, username)

    @staticmethod
    def get_all_usernames():
        appdata_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        general_cookies_folder_path = posixpath.join(appdata_path, "cookies")
        os.makedirs(general_cookies_folder_path, exist_ok=True)
        return next(os.walk(general_cookies_folder_path))[1]

    @staticmethod
    def remove_user_cookies(username):
        cookie_folder = YouTubeLogin.get_cookie_path_from_username(username)
        shutil.rmtree(cookie_folder)


class YouTubeUploader(QObject):

    upload_finished = Signal(str, bool)  # file path, success
    log_message = Signal(str, int)  # message, loglevel
    on_progress = Signal(str, int)  # job filename, percent done

    def __init__(self, username, jobs, headless):
        super().__init__()
        self.username = username
        self.jobs = jobs
        self.headless = headless
        self.cancelled = False

        options = Options()
        options.headless = headless

        service = Service()
        service.log_path = os.devnull
        self.browser = webdriver.Firefox(
            options, service
        )
        atexit.register(self.browser.quit)

        self.browser.get(Constant.YOUTUBE_URL)

        try:
            cookies_path = next(iter(glob.glob(posixpath.join(YouTubeLogin.get_cookie_path_from_username(username), "*youtube*.json"))))
        except StopIteration:
            raise FileNotFoundError(
                f'No cookie files matching *youtube*.json found in {YouTubeLogin.get_cookie_path_from_username(username)}'
            )

        self.log_message.emit(f'Loading cookies from {cookies_path}', logging.DEBUG)
        list(map(self.browser.add_cookie, json.load(open(cookies_path, 'rb'))))

        self.browser.get(Constant.YOUTUBE_UPLOAD_URL)

        try:
            WebDriverWait(self.browser, 30.0).until(
                expected_conditions.presence_of_element_located(Constant.INPUT_FILE_VIDEO)
            )
        except TimeoutException:
            raise ValueError(f'The given cookies were either expired or invalid: {cookies_path}') from None
        
        self.log_message.emit(f"Logged in as {self.username}", logging.INFO)

    def upload_all(self):
        try:
            for job in self.jobs:
                try:
                    self.log_message.emit(f'Starting upload of {job["file_path"]}', logging.INFO)
                    self.on_progress.emit(job['file_path'], 0)
                    success = self.upload(job)
                    self.upload_finished.emit(job['file_path'], success)
                except Exception:
                    self.log_message.emit(traceback.format_exc(), logging.ERROR)
                    self.log_message.emit(f'Retrying upload of {job["file_path"]}', logging.INFO)
                    self.on_progress.emit(job['file_path'], 0)
                    success = self.upload(job)
                    self.upload_finished.emit(job['file_path'], success)
        except Exception:
            self.log_message.emit(traceback.format_exc(), logging.ERROR)
            if self.headless:
                # take screenshot and quit
                appdata_path = QStandardPaths.writableLocation(
                    QStandardPaths.AppDataLocation
                )
                screenshot_dir = posixpath.join(appdata_path, "screenshots")
                os.makedirs(screenshot_dir, exist_ok=True)
                path = posixpath.join(
                    screenshot_dir,
                    datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S.png"),
                )
                self.browser.save_screenshot(path)
                self.log_message.emit(f"Screenshot saved to {path}", logging.ERROR)
        self.browser.quit()
    
    def await_element(self, locator, condition='present', ret=True, timeout=30.0, s=0, parent=None):
        try:
            WebDriverWait([self.browser, parent][bool(parent)], timeout).until(
                {
                    'present': expected_conditions.presence_of_element_located,
                    'clickable': expected_conditions.element_to_be_clickable,
                    'stale': expected_conditions.staleness_of,
                    'visible': expected_conditions.visibility_of_element_located,
                }[condition](locator)
            )
        except TimeoutException:
            NoSuchElementException(f'Could not find {next(k for k,v in Constant.__dict__.items() if v == locator)}')
        if ret:
            return [self.browser, parent][bool(parent)].__getattribute__('find_element' + ['', 's'][s])(*locator)


    def upload(self, metadata):
        ltgt = lambda x: x.replace("<", "＜").replace(">", "＞")
        metadata['title'] = ltgt(metadata['title'][:Constant.MAX_TITLE_LENGTH])
        metadata['description'] = ltgt(metadata['description'][:Constant.MAX_DESCRIPTION_LENGTH])
        metadata['tags'] = metadata['tags'][:Constant.MAX_TAGS_LENGTH]
        metadata['playlist'] = list(map(ltgt, metadata['playlist']))
        self.log_message.emit(f"Validated inputs successfully", logging.INFO)
        self.on_progress.emit(metadata['file_path'], 10)

        if not self.browser.current_url == Constant.YOUTUBE_UPLOAD_URL:
            self.browser.get(Constant.YOUTUBE_UPLOAD_URL)

        # upload the video
        input = self.await_element(Constant.INPUT_FILE_VIDEO)
        input.send_keys(os.path.abspath(metadata['file_path']))

        self.log_message.emit(f"Uploaded video file", logging.INFO)
        self.on_progress.emit(metadata['file_path'], 15)

        self.await_element(input, 'stale', ret=False)

        # clear and fill the title field
        title = self.await_element(Constant.TEXTBOX, 'visible')
        time.sleep(0.1)
        title.click()
        title.send_keys([Keys.CONTROL, Keys.COMMAND][sys.platform == 'darwin'] + 'a')
        title.send_keys(metadata['title'])

        self.log_message.emit(
            f"Set video title to {metadata['title']}", logging.INFO
        )
        self.on_progress.emit(metadata['file_path'], 20)

        # if there is a description fill the field
        if metadata['description']:
            self.browser.switch_to.active_element.send_keys(Keys.TAB)  # focus on ? in desc
            self.browser.switch_to.active_element.send_keys(Keys.TAB)  # focus on desc
            self.browser.switch_to.active_element.send_keys(metadata['description'])

            self.log_message.emit(
                f"Set video description to {metadata['description']}", logging.INFO
            )

        self.on_progress.emit(metadata['file_path'], 25)

        # if metadata['playlist'] in ([], ['']):
            # raise NotImplementedError('playlists')

        # hide tooltips which can obscure buttons
        tooltips = self.await_element(Constant.TOOLTIP, s=1)
        if tooltips is not None:
            for element in tooltips:
                try:
                    self.browser.execute_script(
                        "arguments[0].style.display = 'none'", element
                    )
                except:
                    pass
        
        # "scroll" down
        for _ in range(15):
            ActionChains(self.browser).send_keys(Keys.TAB).perform()
        self.await_element(Constant.RADIO_LABEL, parent=self.await_element(Constant.NOT_MADE_FOR_KIDS)).click()
        self.log_message.emit(f"Selected not made for kids label", logging.INFO)
        self.on_progress.emit(metadata['file_path'], 50)

        # Video elements
        self.await_element(Constant.NEXT_BUTTON).click()
        self.log_message.emit(f"Clicked next", logging.INFO)
        self.on_progress.emit(metadata['file_path'], 55)

        self.await_element(Constant.NEXT_BUTTON).click()
        self.log_message.emit(f"Clicked next", logging.INFO)
        self.on_progress.emit(metadata['file_path'], 60)

        # Checks
        self.await_element(Constant.NEXT_BUTTON).click()
        self.log_message.emit(f"Clicked next", logging.INFO)
        self.on_progress.emit(metadata['file_path'], 65)

        self.await_element(Constant.RADIO_LABEL, parent=self.await_element((By.NAME, metadata['visibility']))).click()
        self.log_message.emit(
            f"Made the video {metadata['visibility']}", logging.INFO
        )
        self.on_progress.emit(metadata['file_path'], 70)

        # poll the upload % until not uploading
        while 'Uploading' in self.await_element(Constant.STATUS_CONTAINER).text:
            time.sleep(1)

        self.log_message.emit(f"Video fully uploaded", logging.INFO)
        self.on_progress.emit(metadata['file_path'], 95)

        done = self.await_element(Constant.DONE_BUTTON, 'clickable')
        #poll until done button is clickable (is blue)
        while done.value_of_css_property('background-color') != 'rgb(62, 166, 255)':
            time.sleep(1)
        done.click()

        self.log_message.emit(f"Uploaded video {metadata['file_path']}", logging.SUCCESS)

        # wait for youtube to save the video info
        self.await_element(Constant.VIDEO_PUBLISHED_DIALOG, timeout=180, ret=False)

        self.on_progress.emit(metadata['file_path'], 100)
        return True
