"""This module implements uploading videos on YouTube via Selenium

    Based on https://github.com/linouk23/youtube_uploader_selenium"""

import atexit
import datetime
import glob
import json
import logging
import os
import pickle
import posixpath
import re
import shutil
import sys
import time
import traceback
from pathlib import Path

from PySide6.QtCore import *
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

from .Constant import *


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

    def __init__(self, username, jobs, headless, cookies_path="") -> None:
        super().__init__()
        self.headless = headless
        self.cookies_paths = []
        # Optional cookies path to override username
        # for debugging purposes
        if cookies_path == "":
            # find cookie files
            dir = YouTubeLogin.get_cookie_path_from_username(username)
            self.cookies_paths += glob.glob(posixpath.join(dir, "*youtube*.pkl"))
            if len(self.cookies_paths) == 0:
                self.cookies_paths += glob.glob(posixpath.join(dir, "*youtube*.json"))
            if len(self.cookies_paths) == 0:
                raise FileNotFoundError(
                    f"No cookie files matching *youtube*.pkl or *youtube*.json found in {dir}"
                )
        else:
            self.cookies_paths.append(cookies_path)
        self.username = username
        self.jobs = jobs
        options = Options()
        options.headless = headless
        self.browser = webdriver.Firefox(
            firefox_options=options, service_log_path=os.devnull
        )
        atexit.register(self.quit)
        self.browser.implicitly_wait(30)
        self.cancelled = False

    def __validate_inputs(self, video_path, metadata_dict):
        if Constant.NOTIFY_SUBS not in metadata_dict:
            metadata_dict[Constant.NOTIFY_SUBS] = True
        if Constant.VIDEO_TITLE not in metadata_dict:
            self.log_message.emit(
                "The video title was not found in metadata", logging.WARNING
            )
            metadata_dict[Constant.VIDEO_TITLE] = Path(video_path).stem
            self.log_message.emit(
                "The video title was set to {}".format(Path(video_path).stem),
                logging.WARNING,
            )
        for key in (Constant.VIDEO_DESCRIPTION, Constant.TAGS):
            if key not in metadata_dict:
                metadata_dict[key] = ""

        if Constant.PLAYLIST not in metadata_dict:
            metadata_dict[Constant.PLAYLIST] = []

        title = metadata_dict[Constant.VIDEO_TITLE]
        if len(title) > Constant.MAX_TITLE_LENGTH:
            self.log_message.emit(
                "Truncating title to {} characters".format(Constant.MAX_TITLE_LENGTH),
                logging.WARNING,
            )
            metadata_dict[Constant.VIDEO_TITLE] = title[: Constant.MAX_TITLE_LENGTH]

        description = metadata_dict[Constant.VIDEO_DESCRIPTION]
        if len(description) > Constant.MAX_DESCRIPTION_LENGTH:
            self.log_message.emit(
                "Truncating description to {} characters".format(
                    Constant.MAX_DESCRIPTION_LENGTH
                ),
                logging.WARNING,
            )
            metadata_dict[Constant.VIDEO_DESCRIPTION] = description[
                : Constant.MAX_DESCRIPTION_LENGTH
            ]

        tags = metadata_dict[Constant.TAGS]
        if len(tags) > Constant.MAX_TAGS_LENGTH:
            self.log_message.emit(
                "Truncating tags to {} characters".format(Constant.MAX_TAGS_LENGTH),
                logging.WARNING,
            )
            metadata_dict[Constant.TAGS] = tags[: Constant.MAX_TAGS_LENGTH]

        # youtube does not allow < and > symbols in title/description/playlists
        # replace with fullwidth version
        metadata_dict[Constant.VIDEO_TITLE] = (
            metadata_dict[Constant.VIDEO_TITLE].replace("<", "＜").replace(">", "＞")
        )
        metadata_dict[Constant.VIDEO_DESCRIPTION] = (
            metadata_dict[Constant.VIDEO_DESCRIPTION]
            .replace("<", "＜")
            .replace(">", "＞")
        )
        metadata_dict[Constant.PLAYLIST] = [
            name.replace("<", "＜").replace(">", "＞")
            for name in metadata_dict[Constant.PLAYLIST]
        ]

        metadata_dict[Constant.PLAYLIST] = set(metadata_dict[Constant.PLAYLIST])
        metadata_dict[Constant.PLAYLIST].discard("")

    def upload_all(self):
        try:
            for job in self.jobs:
                file = job["file_path"]

                try:
                    self.log_message.emit(f"Starting upload of {file}", logging.INFO)
                    self.on_progress.emit(file, 0)
                    success = self.upload(file, job)
                    self.upload_finished.emit(file, success)
                    continue
                except Exception:
                    self.log_message.emit(traceback.format_exc(), logging.ERROR)
                
                # retry
                self.log_message.emit(f"Retrying upload of {file}", logging.INFO)
                self.on_progress.emit(file, 0)
                success = self.upload(file, job)
                self.upload_finished.emit(file, success)
                
            self.__quit()
        except:
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
                self.__quit()

    def upload(self, video_path, metadata):
        self.__validate_inputs(video_path, metadata)

        self.log_message.emit(f"Validated inputs successfully", logging.INFO)
        self.on_progress.emit(video_path, 5)

        self.__login()

        self.log_message.emit(f"Logged in as {self.username}", logging.INFO)
        self.on_progress.emit(video_path, 10)

        return self.__upload(video_path, metadata)

    def __login(self):
        self.browser.get(Constant.YOUTUBE_URL)

        try:
            self.browser.implicitly_wait(5)
            self.browser.find_element_by_xpath(Constant.USER_AVATAR_XPATH)
            self.browser.implicitly_wait(30)
            return  # already logged in
        except:
            pass

        self.__wait()
        for cookie_path in self.cookies_paths:
            self.log_message.emit(f"Loading cookies from {cookie_path}", logging.DEBUG)
            with open(cookie_path, "rb") as f:
                if cookie_path.endswith("json"):
                    cookies = json.load(f)
                elif cookie_path.endswith("pkl"):
                    cookies = pickle.load(f)
                else:
                    raise TypeError(f"File {cookie_path} is not a json or pkl file")
            for cookie in cookies:
                self.browser.add_cookie(cookie)

        self.browser.get(Constant.YOUTUBE_URL)

    def __find_playlist_checkbox_no_search(self, name):
        labels = self.browser.find_elements_by_xpath(Constant.PLAYLIST_LABEL)
        if not labels:
            return None
        for element in labels:
            name_element = element.find_element_by_xpath(
                ".//span/span[@class='label label-text style-scope ytcp-checkbox-group']"
            )
            # if playlist has zero width space, this will not find the checkbox
            # might also need to replace u200c
            if name_element.text == name.replace("\u200b", ""):
                return element.find_element_by_xpath(".//ytcp-checkbox-lit")
        return None

    def __find_playlist_checkbox(self, name):
        try:
            checkbox = self.__find_playlist_checkbox_no_search(name)

            if not checkbox:
                # sometimes a newly created playlist will not show up in the list of playlists
                # we can search for it to update the list
                search = self.__find(By.XPATH, Constant.PLAYLIST_SEARCH)

                if not search:
                    # we do not have a search bar, meaning all the playlists are loaded
                    return None

                # search behaves weird with opening brackets / parentheses,
                # possibly other characters as well
                # need to investigate this further:
                # Uncaught SyntaxError: unterminated character class
                # Uncaught SyntaxError: unterminated parenthetical
                phrases = re.split(r"[\[(]", name)
                phrases.sort(key=lambda p: len(p))
                search.click()
                self.__wait()
                search.clear()
                self.__wait()
                search.send_keys(phrases[-1])
                checkbox = self.__find_playlist_checkbox_no_search(name)
            return checkbox

        except Exception as e:
            return None

    def __find(self, by, constant, parent=None):
        if parent is None:
            try:
                element = self.browser.find_element(by, constant)
            except NoSuchElementException:
                element = None
        else:
            try:
                element = parent.find_element(by, constant)
            except NoSuchElementException:
                element = None
        if not element:
            raise Exception(f"Could not find {Constant.lookup(constant)}")
        return element

    def __wait(self):
        time.sleep(Constant.USER_WAITING_TIME)

    def __upload(self, video_path, metadata_dict):
        self.browser.get(Constant.YOUTUBE_URL)
        self.__wait()
        self.browser.get(Constant.YOUTUBE_UPLOAD_URL)
        self.__wait()
        absolute_video_path = str(Path.cwd() / video_path)
        self.__find(By.XPATH, Constant.INPUT_FILE_VIDEO).send_keys(absolute_video_path)

        self.log_message.emit(f"Uploaded video file", logging.INFO)
        self.on_progress.emit(video_path, 15)

        self.__wait()
        title_field = self.__find(By.ID, Constant.TEXTBOX)
        title_field.click()
        self.__wait()
        if sys.platform == "darwin":
            title_field.send_keys(Keys.COMMAND + "a")
        else:
            title_field.send_keys(Keys.CONTROL + "a")
        self.__wait()
        title_field.send_keys(metadata_dict[Constant.VIDEO_TITLE])

        self.log_message.emit(
            f"Set video title to {metadata_dict[Constant.VIDEO_TITLE]}", logging.INFO
        )
        self.on_progress.emit(video_path, 20)

        video_description = metadata_dict[Constant.VIDEO_DESCRIPTION]
        tags = metadata_dict[Constant.TAGS]
        playlists = metadata_dict[Constant.PLAYLIST]
        notify_subs = metadata_dict[Constant.NOTIFY_SUBS]

        if video_description:
            description_container = self.__find(
                By.XPATH, Constant.DESCRIPTION_CONTAINER
            )
            description_field = self.__find(
                By.ID, Constant.TEXTBOX, parent=description_container
            )
            description_field.click()
            self.__wait()
            description_field.clear()
            self.__wait()
            description_field.send_keys(video_description)

            self.log_message.emit(
                f"Set video description to {video_description}", logging.INFO
            )

        self.on_progress.emit(video_path, 25)

        if playlists:
            for i, playlist in enumerate(playlists):
                self.__find(By.XPATH, Constant.PLAYLIST_CONTAINER).click()
                self.__wait()
                checkbox = self.__find_playlist_checkbox(playlist)
                if checkbox is None:
                    self.log_message.emit(
                        "Could not find playlist checkbox, attempting to create new playlist",
                        logging.INFO,
                    )
                    # clear search so we can create new playlist
                    try:
                        self.__wait()
                        self.__find(
                            By.XPATH, Constant.PLAYLIST_SEARCH_CLEAR_BUTTON
                        ).click()
                    except:
                        # we don't have a search bar for playlists, so just ignore
                        pass
                    self.__wait()
                    playlist_new_button = self.__find(
                        By.XPATH, Constant.PLAYLIST_NEW_BUTTON
                    )
                    self.__wait()
                    playlist_new_button.click()
                    self.__wait()
                    playlist_new_button_create = self.__find(
                        By.XPATH, Constant.PLAYLIST_NEW_BUTTON_CREATE
                    )
                    playlist_new_button_create.click()
                    self.__wait()
                    playlist_title = self.__find(By.XPATH, Constant.PLAYLIST_NEW_TITLE)
                    playlist_title.click()
                    self.__wait()
                    playlist_title.send_keys(playlist)
                    self.__wait()

                    # Set playlist visibility
                    self.__find(By.XPATH, Constant.PLAYLIST_VISIBILITY_DROPDOWN).click()
                    self.__wait()
                    playlist_visibility = self.browser.find_element_by_xpath(
                        '//*[@test-id="{}"]'.format(metadata_dict["visibility"])
                    )
                    if playlist_visibility is None:
                        raise Exception(
                            f"Could not find playlist visibility option {metadata_dict['visibility']}"
                        )
                    playlist_visibility.click()
                    self.__wait()

                    self.__find(By.XPATH, Constant.PLAYLIST_CREATE_BUTTON).click()

                    self.log_message.emit(
                        f"Created new playlist {playlist}", logging.INFO
                    )

                    self.__wait()
                    checkbox = self.__find_playlist_checkbox(playlist)

                self.on_progress.emit(
                    video_path, 25 + (35 - 25) / (2 * len(playlists)) * (2 * i + 1)
                )

                if checkbox is None:
                    raise Exception(f"Could not find playlist: {playlist}")
                else:
                    checkbox.click()
                    self.__wait()
                    self.__find(By.XPATH, Constant.PLAYLIST_DONE_BUTTON).click()

                    self.log_message.emit(f"Selected playlist {playlist}", logging.INFO)
                    self.on_progress.emit(
                        video_path, 25 + (35 - 25) / (2 * len(playlists)) * (2 * i + 2)
                    )

                    self.__wait()

        # hide tooltips which can obscure buttons
        tooltips = self.browser.find_elements_by_xpath(Constant.TOOLTIP)
        if tooltips is not None:
            for element in tooltips:
                try:
                    self.browser.execute_script(
                        "arguments[0].style.display = 'none'", element
                    )
                except:
                    pass

        if tags or not notify_subs:
            self.log_message.emit(f"Setting extra options", logging.INFO)
            self.__find(By.XPATH, Constant.MORE_OPTIONS_CONTAINER).click()
            self.__wait()
            if tags:
                self.__find(By.XPATH, Constant.TAGS_TEXT_INPUT).send_keys(tags)
                self.__wait()

                self.log_message.emit(f"Set tags playlist {tags}", logging.INFO)

            self.on_progress.emit(video_path, 40)

            if not notify_subs:
                self.__find(By.XPATH, Constant.NOTIFY_SUBSCRIBERS_CHECKBOX).click()
                self.__wait()

                self.log_message.emit(
                    f"Disabled subscriber notifications", logging.INFO
                )

            self.on_progress.emit(video_path, 45)

        self.__wait()

        kids_section = self.__find(By.XPATH, Constant.NOT_MADE_FOR_KIDS)

        self.browser.execute_script(
            'arguments[0].scrollIntoView({block: "center", inline: "center"});',
            kids_section,
        )
        self.__wait()
        self.__find(By.ID, Constant.RADIO_LABEL, kids_section).click()

        self.log_message.emit(f"Selected not made for kids label", logging.INFO)
        self.on_progress.emit(video_path, 50)
        self.__wait()

        self.__find(By.ID, Constant.NEXT_BUTTON).click()

        self.log_message.emit(f"Clicked next", logging.INFO)
        self.on_progress.emit(video_path, 55)
        self.__wait()

        # Video elements
        self.__find(By.ID, Constant.NEXT_BUTTON).click()

        self.log_message.emit(f"Clicked next", logging.INFO)
        self.on_progress.emit(video_path, 60)
        self.__wait()

        # Checks
        self.__find(By.ID, Constant.NEXT_BUTTON).click()

        self.log_message.emit(f"Clicked next", logging.INFO)
        self.on_progress.emit(video_path, 65)
        self.__wait()

        visibility_button = self.browser.find_element(
            By.NAME, metadata_dict["visibility"]
        )
        visibility_button.find_element(By.ID, Constant.RADIO_LABEL).click()

        self.log_message.emit(
            f"Made the video {metadata_dict['visibility']}", logging.INFO
        )
        self.on_progress.emit(video_path, 70)
        self.__wait()

        while True:
            status_container = self.browser.find_element_by_xpath(
                Constant.STATUS_CONTAINER
            )
            self.log_message.emit(
                f"Upload status: {status_container.text}", logging.INFO
            )
            progress = status_container.text
            in_process = progress.find(Constant.UPLOADED) != -1
            if in_process:
                match = Constant.PROGRESS_REGEX.match(progress)
                if match:
                    percent = match.group("progress")
                    if not percent:
                        self.log_message.emit(
                            f"Could not find progress in string {progress}",
                            logging.WARNING,
                        )
                    else:
                        self.on_progress.emit(
                            video_path, 70 + int((95 - 70) * int(percent) / 100)
                        )
                self.__wait()
            else:
                break

        self.log_message.emit(f"Video fully uploaded", logging.INFO)
        self.on_progress.emit(video_path, 95)

        done_button = self.__find(By.ID, Constant.DONE_BUTTON)

        # Catch such error as
        # "File is a duplicate of a video you have already uploaded"
        if done_button.get_attribute("aria-disabled") == "true":
            error_message = self.__find(By.XPATH, Constant.ERROR_CONTAINER).text
            self.log_message(error_message, logging.ERROR)
            return False

        done_button.click()
        self.log_message.emit(f"Uploaded video {video_path}", logging.SUCCESS)
        # wait for youtube to save the video info
        while self.__find(By.XPATH, Constant.VIDEO_PUBLISHED_DIALOG) is None:
            self.__wait()

        self.on_progress.emit(video_path, 100)

        return True

    def __quit(self):
        self.browser.quit()

    def quit(self):
        self.__quit()
