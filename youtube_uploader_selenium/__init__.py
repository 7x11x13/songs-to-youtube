"""This module implements uploading videos on YouTube via Selenium

    Based on https://github.com/linouk23/youtube_uploader_selenium"""

from selenium_firefox.firefox import Firefox, By, Keys
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from typing import Optional
import time
import os
import re
from .Constant import *
from pathlib import Path
import shutil
import logging
import sys

from PySide6.QtCore import QStandardPaths

logging.basicConfig()


class YouTubeLogin:

    """Let user login to YouTube and save the cookies"""
    def __init__(self):
        self.browser = Firefox(full_screen=False)
        self.logger = logging.getLogger()

    @staticmethod
    def get_cookie_path_from_username(username):
        appdata_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        general_cookies_folder_path = os.path.join(appdata_path, 'cookies')
        os.makedirs(general_cookies_folder_path, exist_ok=True)
        return os.path.join(general_cookies_folder_path, username)

    @staticmethod
    def get_all_usernames():
        appdata_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        general_cookies_folder_path = os.path.join(appdata_path, 'cookies')
        os.makedirs(general_cookies_folder_path, exist_ok=True)
        return next(os.walk(general_cookies_folder_path))[1]

    @staticmethod
    def remove_user_cookies(username):
        cookie_folder = YouTubeLogin.get_cookie_path_from_username(username)
        shutil.rmtree(cookie_folder)

    def get_login(self):

        self.browser.get(Constant.YOUTUBE_URL)
        time.sleep(Constant.USER_WAITING_TIME)
        while (avatar := self.browser.find(By.XPATH, Constant.USER_AVATAR_XPATH)) is None:
            time.sleep(1)
        avatar.click()
        username_div = self.browser.find(By.ID, Constant.USERNAME_ID, timeout=30)
        username = username_div.text
        logging.info("Logged in as {}".format(username))
        self.browser.get(Constant.YOUTUBE_URL)
        time.sleep(Constant.USER_WAITING_TIME)

        self.browser.cookies_folder_path = self.get_cookie_path_from_username(username)
        os.makedirs(self.browser.cookies_folder_path, exist_ok=True)
        self.browser.save_cookies()
        self.browser.driver.quit()

        return username

class YouTubeUploader:
    """A class for uploading videos on YouTube via Selenium using metadata dict"""

    def __init__(self, username, cookies_path="") -> None:
        # Optional cookies_path to override username
        # for debugging purposes
        if cookies_path == "":
            cookies_path = YouTubeLogin.get_cookie_path_from_username(username)
        self.username = username
        self.browser = Firefox(full_screen=False, cookies_folder_path=cookies_path, default_find_func_timeout=10)
        self.logger = logging.getLogger()

    def __validate_inputs(self):
        if Constant.VIDEO_TITLE not in self.metadata_dict:
            self.logger.warning("The video title was not found in metadata")
            self.metadata_dict[Constant.VIDEO_TITLE] = Path(self.video_path).stem
            self.logger.warning("The video title was set to {}".format(Path(self.video_path).stem))
        for key in (Constant.VIDEO_DESCRIPTION, Constant.PLAYLIST, Constant.TAGS):
            if key not in self.metadata_dict:
                self.metadata_dict[key] = ""

        title = self.metadata_dict[Constant.VIDEO_TITLE]
        if len(title) > Constant.MAX_TITLE_LENGTH:
            self.logger.warning("Truncating title to {} characters".format(Constant.MAX_TITLE_LENGTH))
            self.metadata_dict[Constant.VIDEO_TITLE] = title[:Constant.MAX_TITLE_LENGTH]

        description = self.metadata_dict[Constant.VIDEO_DESCRIPTION]
        if len(description) > Constant.MAX_DESCRIPTION_LENGTH:
            self.logger.warning("Truncating description to {} characters".format(Constant.MAX_DESCRIPTION_LENGTH))
            self.metadata_dict[Constant.VIDEO_DESCRIPTION] = description[:Constant.MAX_DESCRIPTION_LENGTH]

        tags = self.metadata_dict[Constant.TAGS]
        if len(tags) > Constant.MAX_TAGS_LENGTH:
            self.logger.warning("Truncating tags to {} characters".format(Constant.MAX_TAGS_LENGTH))
            self.metadata_dict[Constant.TAGS] = tags[:Constant.MAX_TAGS_LENGTH]

    def upload(self, video_path, metadata) -> (bool, Optional[str]):
        try:
            self.video_path = video_path
            self.metadata_dict = metadata
            self.__validate_inputs()
            self.__login()
            return self.__upload()
        except Exception as e:
            self.__quit()
            raise


    def __login(self):
        self.browser.get(Constant.YOUTUBE_URL)
        time.sleep(Constant.USER_WAITING_TIME)

        if self.browser.find(By.XPATH, Constant.USER_AVATAR_XPATH, timeout=5) is not None:
            # already logged in
            return

        if self.browser.has_cookies_for_current_website():
            self.browser.load_cookies()
            time.sleep(Constant.USER_WAITING_TIME)
            self.browser.refresh()
        else:
            raise Exception("Could not find cookies at path {}".format(self.browser.cookies_folder_path))

    def __find_playlist_checkbox_no_search(self, name):
        for element in self.browser.find_all(By.XPATH, Constant.PLAYLIST_LABEL):
            name_element = element.find_element_by_xpath(".//span/span[@class='label label-text style-scope ytcp-checkbox-group']")
            if name_element.text == name:
                return element.find_element_by_xpath(".//ytcp-checkbox-lit")
        return None

    def __find_playlist_checkbox(self, name):
        try:
            checkbox = self.__find_playlist_checkbox_no_search(name)

            if not checkbox:
                # sometimes a newly created playlist will not show up in the list of playlists
                # we can search for it to update the list
                search = self.browser.find(By.XPATH, Constant.PLAYLIST_SEARCH)

                # search behaves weird with opening brackets / parentheses,
                # possibly other characters as well
                # need to investigate this further:
                # Uncaught SyntaxError: unterminated character class
                # Uncaught SyntaxError: unterminated parenthetical
                phrases = re.split(r"[\[(]", name)
                phrases.sort(key=lambda p: len(p))
                search.click()
                time.sleep(Constant.USER_WAITING_TIME)
                search.clear()
                time.sleep(Constant.USER_WAITING_TIME)
                search.send_keys(phrases[-1])
                checkbox = self.__find_playlist_checkbox_no_search(name)
                # clear search so we can create new playlist
                self.browser.find(By.XPATH, Constant.PLAYLIST_SEARCH_CLEAR_BUTTON).click()


            return checkbox

        except Exception as e:
            logging.error(e)
            return None


    def __upload(self) -> (bool, Optional[str]):
        self.browser.get(Constant.YOUTUBE_URL)
        time.sleep(Constant.USER_WAITING_TIME)
        self.browser.get(Constant.YOUTUBE_UPLOAD_URL)
        time.sleep(Constant.USER_WAITING_TIME)
        absolute_video_path = str(Path.cwd() / self.video_path)
        self.browser.find(By.XPATH, Constant.INPUT_FILE_VIDEO).send_keys(absolute_video_path)
        self.logger.debug('Attached video {}'.format(self.video_path))
        time.sleep(Constant.USER_WAITING_TIME)
        if (title_field := self.browser.find(By.ID, Constant.TEXTBOX, timeout=30)) is None:
            self.logger.error('Could not find title field')
            return False, None
        title_field.click()
        time.sleep(Constant.USER_WAITING_TIME)
        title_field.clear()
        time.sleep(Constant.USER_WAITING_TIME)
        if sys.platform == 'darwin':
            title_field.send_keys(Keys.COMMAND + 'a')
        else:
            title_field.send_keys(Keys.CONTROL + 'a')
        time.sleep(Constant.USER_WAITING_TIME)
        title_field.send_keys(self.metadata_dict[Constant.VIDEO_TITLE])
        self.logger.debug('The video title was set to \"{}\"'.format(self.metadata_dict[Constant.VIDEO_TITLE]))

        video_description = self.metadata_dict[Constant.VIDEO_DESCRIPTION]
        tags = self.metadata_dict[Constant.TAGS]
        playlist = self.metadata_dict[Constant.PLAYLIST]
        if video_description:
            description_container = self.browser.find(By.XPATH,
                                                      Constant.DESCRIPTION_CONTAINER)
            description_field = self.browser.find(By.ID, Constant.TEXTBOX, element=description_container)
            description_field.click()
            time.sleep(Constant.USER_WAITING_TIME)
            description_field.clear()
            time.sleep(Constant.USER_WAITING_TIME)
            description_field.send_keys(video_description)
            self.logger.debug(
                'The video description was set to \"{}\"'.format(video_description))
        if playlist:
            self.browser.find(By.XPATH, Constant.PLAYLIST_CONTAINER).click()
            time.sleep(Constant.USER_WAITING_TIME)
            checkbox = self.__find_playlist_checkbox(playlist)
            if checkbox is None:
                self.logger.info("Could not find playlist checkbox, attempting to create new playlist")
                playlist_new_button = self.browser.find(By.XPATH, Constant.PLAYLIST_NEW_BUTTON)
                self.browser.move_to_element(playlist_new_button)
                time.sleep(Constant.USER_WAITING_TIME)
                playlist_new_button.click()
                time.sleep(Constant.USER_WAITING_TIME)
                playlist_title = self.browser.find(By.XPATH, Constant.PLAYLIST_NEW_TITLE)
                if playlist_title is None:
                    logging.error("Could not find playlist title field")
                    return False, None
                playlist_title.click()
                time.sleep(Constant.USER_WAITING_TIME)
                playlist_title.send_keys(playlist)
                time.sleep(Constant.USER_WAITING_TIME)

                # Set playlist visibility
                self.browser.find(By.XPATH, Constant.PLAYLIST_VISIBILITY_DROPDOWN).click()
                time.sleep(Constant.USER_WAITING_TIME)
                playlist_visibility = self.browser.find(By.XPATH, '//*[@test-id="{}"]'.format(self.metadata_dict['visibility']))
                if playlist_visibility is None:
                    logging.error("Could not find playlist visibility option {}".format(self.metadata_dict['visibility']))
                    return False, None
                playlist_visibility.click()
                time.sleep(Constant.USER_WAITING_TIME)

                self.browser.find(By.XPATH, Constant.PLAYLIST_CREATE_BUTTON).click()
                time.sleep(Constant.USER_WAITING_TIME)
                checkbox = self.__find_playlist_checkbox(playlist)
            if checkbox is None:
                logging.error("Could not find playlist: {}".format(playlist))
                return False, None
            else:
                checkbox.click()
                time.sleep(Constant.USER_WAITING_TIME)
                self.browser.find(By.XPATH, Constant.PLAYLIST_DONE_BUTTON).click()
                time.sleep(Constant.USER_WAITING_TIME)

        # hide tooltips which can obscure buttons
        tooltips = self.browser.find_all(By.XPATH, Constant.TOOLTIP)
        if tooltips is not None:
            for element in tooltips:
                self.browser.execute_script_on_element("arguments[0].style.display = 'none'", element)

        if tags:
            self.browser.find(By.XPATH, Constant.MORE_OPTIONS_CONTAINER).click()
            time.sleep(Constant.USER_WAITING_TIME)
            self.browser.find(By.XPATH, Constant.TAGS_TEXT_INPUT).send_keys(tags)
            time.sleep(Constant.USER_WAITING_TIME)

        time.sleep(Constant.USER_WAITING_TIME)
        kids_section = self.browser.find(By.NAME, Constant.NOT_MADE_FOR_KIDS_LABEL)
        self.browser.scroll_to_element(kids_section)
        time.sleep(Constant.USER_WAITING_TIME)
        self.browser.find(By.ID, Constant.RADIO_LABEL, kids_section).click()
        self.logger.debug('Selected \"{}\"'.format(Constant.NOT_MADE_FOR_KIDS_LABEL))

        self.browser.find(By.ID, Constant.NEXT_BUTTON).click()
        self.logger.debug('Clicked {}'.format(Constant.NEXT_BUTTON))

        self.browser.find(By.ID, Constant.NEXT_BUTTON).click()
        self.logger.debug('Clicked another {}'.format(Constant.NEXT_BUTTON))

        visibility_button = self.browser.find(By.NAME, self.metadata_dict['visibility'])
        self.browser.find(By.ID, Constant.RADIO_LABEL, visibility_button).click()
        self.logger.debug('Made the video {}'.format(self.metadata_dict['visibility']))

        video_id = self.__get_video_id()

        status_container = self.browser.find(By.XPATH,
                                             Constant.STATUS_CONTAINER)
        while True:
            in_process = status_container.text.find(Constant.UPLOADED) != -1
            if in_process:
                time.sleep(Constant.USER_WAITING_TIME)
            else:
                break

        done_button = self.browser.find(By.ID, Constant.DONE_BUTTON)

        # Catch such error as
        # "File is a duplicate of a video you have already uploaded"
        if done_button.get_attribute('aria-disabled') == 'true':
            error_message = self.browser.find(By.XPATH,
                                              Constant.ERROR_CONTAINER).text
            self.logger.error(error_message)
            return False, None

        done_button.click()
        self.logger.debug("Published the video with video_id = {}".format(video_id))
        return True, video_id

    def __get_video_id(self) -> Optional[str]:
        video_id = None
        try:
            video_url_container = self.browser.find(By.XPATH, Constant.VIDEO_URL_CONTAINER)
            video_url_element = self.browser.find(By.XPATH, Constant.VIDEO_URL_ELEMENT,
                                                  element=video_url_container)
            video_id = video_url_element.get_attribute(Constant.HREF).split('/')[-1]
        except:
            self.logger.warning(Constant.VIDEO_NOT_FOUND_ERROR)
            pass
        return video_id

    def __quit(self):
        self.browser.driver.quit()

    def quit(self):
        self.__quit()
