import re
from selenium.webdriver.common.by import By

class Constant:
    YOUTUBE_URL = "https://www.youtube.com"
    YOUTUBE_UPLOAD_URL = "https://www.youtube.com/upload"
    YOUTUBE_UPLOAD_LOADED = 'https://studio.youtube.com/channel'
    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_TAGS_LENGTH = 500
    INPUT_FILE_VIDEO = By.XPATH, '//input[@type="file"]'
    TEXTBOX = By.ID, "textbox"
    CALLOUT = By.XPATH, '//*[@id="callout"]'
    CALLOUT_CLOSE = By.ID, 'close-button'
    PLAYLIST_DROPDOWN_TRIGGER = By.XPATH, '/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-basics/div[6]/div[3]/div[1]/ytcp-video-metadata-playlists/ytcp-text-dropdown-trigger/ytcp-dropdown-trigger/div'
    PLAYLIST_POPUP = By.CSS_SELECTOR, 'tp-yt-paper-dialog.ytcp-playlist-dialog'
    PLAYLIST_ITEM_TEXT = By.ID, 'checkbox-label-{0}'
    PLAYLIST_ITEM_CHECKBOX = By.ID, 'checkbox-{0}'
    CREATE_PLAYLIST_BUTTON = By.CSS_SELECTOR, '.action-buttons > div:nth-child(1)'
    PLAYLIST_NAME = By.CSS_SELECTOR, "ytcp-playlist-metadata-editor.style-scope > div:nth-child(1) > div:nth-child(1) > ytcp-social-suggestions-textbox:nth-child(1) > ytcp-form-input-container:nth-child(1) > div:nth-child(1) > div:nth-child(3)"
    PLAYLIST_VISIBILITY_BUTTON = By.CSS_SELECTOR, "#menu-button > ytcp-dropdown-trigger:nth-child(1) > div:nth-child(2)"
    PLAYLIST_VISIBILITY_MENU = By.CSS_SELECTOR, '#visibility-menu > tp-yt-paper-dialog:nth-child(1) > tp-yt-paper-listbox:nth-child(2)'
    PLAYLIST_VISIBILITY_TYPE = By.XPATH, '//*[@id="text-item-{0}"]'
    PLAYLIST_CREATE_BUTTON = By.XPATH, '//*[@id="create-button"]'
    PLAYLIST_DONE = By.XPATH, '/html/body/ytcp-playlist-dialog/tp-yt-paper-dialog/div[2]/ytcp-button[2]'
    TOOLTIP = By.XPATH, "//ytcp-paper-tooltip"
    NOT_MADE_FOR_KIDS = By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MFK"
    RADIO_LABEL = By.ID, "radioLabel"
    SHOW_MORE = By.XPATH, '//*[@id="toggle-button"]'
    TAGS_CONTAINER = By.ID, 'tags-container'
    NOTIFY_SUBS = By.ID, 'notify-subscribers'
    NEXT_BUTTON = By.ID, "next-button"
    PRIVACY_RADIOS = By.ID, 'privacy-radios'
    STATUS_CONTAINER = By.XPATH, "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[1]/ytcp-video-upload-progress/span"
    DONE_BUTTON = By.ID, "done-button"
    VIDEO_PUBLISHED_DIALOG = By.XPATH, '//*[@id="dialog-title"]'
    ERR = By.CSS_SELECTOR, '.error-short'
