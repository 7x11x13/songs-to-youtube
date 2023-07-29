"""This module implements uploading videos on YouTube via Selenium

    Based on https://github.com/linouk23/youtube_uploader_selenium"""

import atexit
import re
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

from PySide6.QtCore import *
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.action_chains import ActionChains

from .Constant import Constant

lerp = lambda p0, p1, t: p0 + ((p1 - p0) * t)
const_fstr = lambda byval, *strargs: (byval[0], byval[1].format(*strargs))


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


def await_element(parent, locator, condition='present', ret=True, timeout=30.0, s=0):
    try:
        WebDriverWait(parent, timeout).until(
            {
                'present': expected_conditions.presence_of_element_located,
                'clickable': expected_conditions.element_to_be_clickable,
                'stale': expected_conditions.staleness_of,
                'visible': expected_conditions.visibility_of_element_located,
                'invisible': expected_conditions.invisibility_of_element_located
            }[condition](locator)
        )
    except TimeoutException:
        raise NoSuchElementException(locator) from None
    if ret:
        return parent.__getattribute__('find_element' + ('', 's')[s])(*locator)

def poll(n_polls):
    if n_polls == -1:
        while 1:
            time.sleep(1)
            yield
    else:
        for _ in range(n_polls):
            time.sleep(1)
            yield


class YouTubeUploader(QObject):

    upload_finished = Signal(str, bool)  # file path, success
    log_message = Signal(str, int)  # message, loglevel
    on_progress = Signal(str, int)  # job filename, percent done

    def __init__(self, username, jobs, headless):
        super().__init__()
        self.username = username
        self.jobs = jobs
        self.headless = headless
        
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
            ) from None

        self.log_message.emit(f'Loading cookies from {cookies_path}', logging.DEBUG)

        for cookie in json.load(open(cookies_path, 'rb')):
            self.browser.add_cookie(cookie)

        self.browser.get(Constant.YOUTUBE_UPLOAD_URL)

        try:
            WebDriverWait(self.browser, 30.0).until(
                lambda browser: browser.current_url.startswith(Constant.YOUTUBE_UPLOAD_LOADED)
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

    def upload(self, metadata):
        if len(metadata['title']) > Constant.MAX_TITLE_LENGTH:
            self.log_message.emit(
                f'Truncating title to {Constant.MAX_TITLE_LENGTH} characters',
                logging.WARNING
            )
        if len(metadata['description']) > Constant.MAX_DESCRIPTION_LENGTH:
            self.log_message.emit(
                f'Truncating description to {Constant.MAX_DESCRIPTION_LENGTH} characters',
                logging.WARNING
            )
        if len(metadata['tags']) > Constant.MAX_TAGS_LENGTH:
            self.log_message.emit(
                f'Truncating tags to {Constant.MAX_TAGS_LENGTH} characters',
                logging.WARNING
            )

        ltgt = lambda x: x.replace("<", "＜").replace(">", "＞")
        metadata['title'] = ltgt(metadata['title'][:Constant.MAX_TITLE_LENGTH])
        metadata['description'] = ltgt(metadata['description'][:Constant.MAX_DESCRIPTION_LENGTH])
        metadata['tags'] = metadata['tags'][:Constant.MAX_TAGS_LENGTH]
        metadata['playlist'] = set(map(ltgt, metadata['playlist']))
        metadata['playlist'].discard("")

        self.log_message.emit('Validated inputs successfully', logging.INFO)
        self.on_progress.emit(metadata['file_path'], 5)
        try:
            self.browser.get(Constant.YOUTUBE_UPLOAD_URL)

            # upload the video
            input = await_element(self.browser, Constant.INPUT_FILE_VIDEO)
            input.send_keys(os.path.abspath(metadata['file_path']))

            self.log_message.emit('Uploaded video file', logging.INFO)
            self.on_progress.emit(metadata['file_path'], 10)

            # wait until upload button is stale and title field is visible
            await_element(self.browser, input, 'stale', ret=False)
            title = await_element(self.browser, Constant.TEXTBOX, 'visible')
            time.sleep(0.1)

            try:
                title.click()
            except ElementClickInterceptedException:
                # "reuse details" pop up may obscure the title field
                if callout := self.browser.find_element(*Constant.CALLOUT):
                    callout.find_element(*Constant.CALLOUT_CLOSE).click()
                    title.click()
                else:
                    raise

            #clear field and send title
            title.send_keys([Keys.CONTROL, Keys.COMMAND][sys.platform == 'darwin'] + 'a')
            title.send_keys(metadata['title'])

            self.log_message.emit(f'Set video title to {metadata["title"]}', logging.INFO)
            self.on_progress.emit(metadata['file_path'], 20)


            # if there is a description fill the field
            if metadata['description']:
                self.browser.switch_to.active_element.send_keys(Keys.TAB)  # focus on ? in desc
                self.browser.switch_to.active_element.send_keys(Keys.TAB)  # focus on desc
                self.browser.switch_to.active_element.send_keys(metadata['description'])

                self.log_message.emit(f'Set video description to {metadata["description"]}', logging.INFO)
            self.on_progress.emit(metadata['file_path'], 30)
            
            if metadata['playlist']:
                await_element(self.browser, Constant.PLAYLIST_DROPDOWN_TRIGGER).click()
                playlist_ele = await_element(self.browser, Constant.PLAYLIST_POPUP)

                cur_playlists = []
                c = 0
                while 1:
                    try:
                        pp = self.browser.find_element(
                            *const_fstr(Constant.PLAYLIST_ITEM_TEXT, c)
                        )
                        pp_checkbox = pp.parent.find_element(
                            *const_fstr(Constant.PLAYLIST_ITEM_CHECKBOX, c)
                        )
                        cur_playlists.append({
                            'name': pp.text,
                            'checked': bool(pp_checkbox.get_attribute('checked') is not None),
                        })
                    except NoSuchElementException:
                        break
                    c += 1

                for i, playlist in enumerate(metadata['playlist']):
                    try:
                        index = [p['name'] for p in cur_playlists].index(playlist) # raise valueerror

                        assert cur_playlists[index]['checked'] == False, cur_playlists[index]['name']  # tmp

                        pclick = await_element(
                            await_element(self.browser, const_fstr(Constant.PLAYLIST_ITEM_TEXT, index)).parent,
                            const_fstr(Constant.PLAYLIST_ITEM_CHECKBOX, index)
                        )
                        assert pclick.get_attribute('checked') is None
                        pclick.click()

                        cur_playlists[index]['checked'] = True
                        self.log_message.emit(f'Selected playlist {playlist}', logging.INFO)

                    except ValueError:  # playlist does not exist
                        self.log_message.emit(
                            'Could not find playlist checkbox, attempting to create new playlist',
                            logging.INFO
                        )

                        await_element(playlist_ele, Constant.CREATE_PLAYLIST_BUTTON).click()  # new playlist
                        ActionChains(self.browser).send_keys(Keys.TAB).perform()
                        ActionChains(self.browser).send_keys(Keys.ENTER).perform()  # playlist

                        #popup 2
                        p_name = await_element(self.browser, Constant.PLAYLIST_NAME, 'clickable')
                        p_name.click()
                        time.sleep(0.1)
                        ActionChains(self.browser).send_keys(playlist).perform()

                        if metadata['visibility'] != 'PUBLIC':
                            # open visibility dropdown
                            await_element(self.browser, Constant.PLAYLIST_VISIBILITY_BUTTON).click()
                            await_element(
                                await_element(self.browser, Constant.PLAYLIST_VISIBILITY_MENU),
                                const_fstr(
                                    Constant.PLAYLIST_VISIBILITY_TYPE,
                                    ['PUBLIC', 'PRIVATE', 'UNLISTED'].index(metadata['visibility'])
                                )
                            ).click()

                        await_element(self.browser, Constant.PLAYLIST_CREATE_BUTTON).click()
                        await_element(self.browser, Constant.PLAYLIST_NAME, 'invisible', ret=False)
                        cur_playlists.insert(0, {'name': playlist, 'checked': True})

                        self.log_message.emit(f'Created new playlist {playlist}', logging.INFO)

                    self.on_progress.emit(metadata['file_path'], round(lerp(31, 39, i / len(metadata['playlist']))))

                await_element(self.browser, Constant.PLAYLIST_DONE).click()
            self.on_progress.emit(metadata['file_path'], 40)


            # hide tooltips which can obscure buttons
            tooltips = await_element(self.browser, Constant.TOOLTIP, s=1)
            if tooltips is not None:
                for element in tooltips:
                    try:
                        self.browser.execute_script(
                            "arguments[0].style.display = 'none'", element
                        )
                    except:
                        pass

            # "scroll" down
            for _ in range(5):
                ActionChains(self.browser).send_keys(Keys.TAB).perform()

            await_element(await_element(self.browser, Constant.NOT_MADE_FOR_KIDS), Constant.RADIO_LABEL).click()
            self.log_message.emit('Selected not made for kids label', logging.INFO)
            self.on_progress.emit(metadata['file_path'], 50)

            if any((not metadata['notify_subs'], metadata['tags'])):

                self.log_message.emit('Setting extra options', logging.INFO)

                await_element(self.browser, Constant.SHOW_MORE).click()

                if metadata['tags']:
                    await_element(self.browser, Constant.TAGS_CONTAINER).click()
                    ActionChains(self.browser).send_keys(metadata['tags']).perform()
                    self.log_message.emit(f"Set tags to {metadata['tags']}", logging.INFO)

                if not metadata['notify_subs']:
                    notify = await_element(self.browser, Constant.NOTIFY_SUBS)
                    assert notify.get_attribute('checked') is not None  # tmp
                    notify.click()
                    self.log_message.emit(
                        f"Disabled subscriber notifications", logging.INFO
                    )

            self.on_progress.emit(metadata['file_path'], 55)

            # Video elements (2/4)
            await_element(self.browser, Constant.NEXT_BUTTON, 'clickable').click()
            self.log_message.emit('Clicked next', logging.INFO)
            self.on_progress.emit(metadata['file_path'], 57)

            # (3/4)
            await_element(self.browser, Constant.NEXT_BUTTON, 'clickable').click()
            self.log_message.emit('Clicked next', logging.INFO)
            self.on_progress.emit(metadata['file_path'], 59)

            # Checks (4/4)
            await_element(self.browser, Constant.NEXT_BUTTON, 'clickable').click()
            self.log_message.emit('Clicked next', logging.INFO)
            self.on_progress.emit(metadata['file_path'], 61)

            # set video's visibility
            await_element(await_element(self.browser, Constant.PRIVACY_RADIOS), (By.NAME, metadata['visibility'])).click()

            self.log_message.emit(f'Made the video {metadata["visibility"]}', logging.INFO)
            self.on_progress.emit(metadata['file_path'], 62)

            # poll the upload % until not uploading
            status = await_element(self.browser, Constant.STATUS_CONTAINER)
            # the first digit in the string 1 to 3 chars long
            get_digit = re.compile('\d{1,3}')
            for _ in poll(Constant.UPLOAD_TIMEOUT_SECONDS):
                if 'Uploading' not in status.text:
                    break

                self.log_message.emit(status.text, logging.INFO)
                try:
                    self.on_progress.emit(
                        metadata['file_path'],
                        round(lerp(63, 94, float(get_digit.findall(status.text)[0]) / 100))
                    )
                except IndexError:
                    pass
            else:
                raise TimeoutException(repr(status))
            
            self.log_message.emit('Video fully uploaded', logging.INFO)
            self.on_progress.emit(metadata['file_path'], 95)

            done = await_element(self.browser, Constant.DONE_BUTTON, 'clickable', timeout=10.0)
            assert not self.browser.execute_script('return arguments[0].__data.disabled', done)
            done.click()
            self.log_message.emit(f'Uploaded video {metadata["file_path"]}', logging.INFO)

            #wait for youtube to save the video info
            await_element(self.browser, Constant.VIDEO_PUBLISHED_DIALOG, timeout=60, ret=False)
            self.on_progress.emit(metadata['file_path'], 100)
            return True
        except Exception:
            e = self.browser.find_element(*Constant.ERR)
            if e.is_displayed():
                self.log_message.emit(e.text, logging.ERROR)
                self.browser.quit()
            else:
                raise
