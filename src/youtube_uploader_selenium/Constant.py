import re
from selenium.webdriver.common.by import By

class Constant:
    YOUTUBE_URL = "https://www.youtube.com"
    YOUTUBE_STUDIO_URL = "https://studio.youtube.com"
    YOUTUBE_UPLOAD_URL = "https://www.youtube.com/upload"
    YOUTUBE_UPLOAD_LOADED = 'https://studio.youtube.com/channel'

    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_TAGS_LENGTH = 500

    INPUT_FILE_VIDEO = By.XPATH, '//input[@type="file"]'

    DESCRIPTION_CONTAINER = By.XPATH, "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-basics/div[2]/ytcp-video-description/div/ytcp-social-suggestions-textbox"
    TEXTBOX = By.ID, "textbox"
    UPLOAD_URL = By.XPATH, "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/ytcp-video-metadata-editor-sidepanel/ytcp-video-info/div/div[2]/div[1]/div[2]/span/a"
    TOOLTIP = By.XPATH, "//ytcp-paper-tooltip"

    MORE_OPTIONS_CONTAINER = By.XPATH, "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/div/ytcp-button/div"
    NOT_MADE_FOR_KIDS = By.NAME, "VIDEO_MADE_FOR_KIDS_NOT_MFK"

    NEXT_BUTTON = By.ID, "next-button"
    TAGS_TEXT_INPUT = By.XPATH, "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-advanced/div[3]/ytcp-form-input-container/div[1]/div[2]/ytcp-free-text-chip-bar/ytcp-chip-bar/div/input"
    RADIO_LABEL = By.ID, "radioLabel"

    STATUS_CONTAINER = By.XPATH, "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[1]/ytcp-video-upload-progress/span"
    DONE_BUTTON = By.ID, "done-button"
    ERROR_CONTAINER = By.XPATH, '//*[@id="error-message"]'
    VIDEO_PUBLISHED_DIALOG = By.XPATH, '//*[@id="dialog-title"]'

    CALLOUT = By.XPATH, '//*[@id="callout"]'
    CALLOUT_CLOSE = By.ID, 'close-button'

    PLAYLIST_BOX = By.XPATH, '/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-basics/div[4]/div[3]/div[1]'

    PLAYLIST_POPUP = By.CSS_SELECTOR, 'tp-yt-paper-dialog.ytcp-playlist-dialog'

    CREATE_PLAYLIST_BUTTON = By.CSS_SELECTOR, '.action-buttons > div:nth-child(1)'

    PLAYLIST_PAPER_LIST = By.XPATH, '//*[@id="paper-list"]'

    NEW_PLAYLIST = By.XPATH, '//*[@id="text-item-0"]'

    PLAYLIST_NAME = By.CSS_SELECTOR, "ytcp-playlist-metadata-editor.style-scope > div:nth-child(1) > div:nth-child(1) > ytcp-social-suggestions-textbox:nth-child(1) > ytcp-form-input-container:nth-child(1) > div:nth-child(1) > div:nth-child(3)"

    PLAYLIST_VISIBILITY_BUTTON = By.CSS_SELECTOR, "#menu-button > ytcp-dropdown-trigger:nth-child(1) > div:nth-child(2)"
    PLAYLIST_VISIBILITY_MENU = By.CSS_SELECTOR, '#visibility-menu > tp-yt-paper-dialog:nth-child(1) > tp-yt-paper-listbox:nth-child(2)'

    PLAYLIST_VISIBILITY_TYPE = By.XPATH, '//*[@id="text-item-{0}"]'
    
    PLAYLIST_CREATE_BUTTON = By.XPATH, '//*[@id="create-button"]'

    PLAYLIST_LIST = By.ID, 'items'
    PLAYLIST_DONE = By.XPATH, '/html/body/ytcp-playlist-dialog/tp-yt-paper-dialog/div[2]/ytcp-button[2]'


    PLAYLIST_ITEM_TEXT = By.ID, 'checkbox-label-{0}'
    PLAYLIST_ITEM_CHECKBOX = By.ID, 'checkbox-{0}'

    NOTIFY_SUBS = By.ID, 'notify-subscribers'
    TAGS_CONTAINER = By.ID, 'tags-container'

    SHOW_MORE = By.XPATH, '//*[@id="toggle-button"]'
    PRIVACY_RADIOS = By.ID, 'privacy-radios'

    ERR = By.CSS_SELECTOR, '.error-short'

    PLAYLIST_DROPDOWN_TRIGGER = By.XPATH, '/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-basics/div[6]/div[3]/div[1]/ytcp-video-metadata-playlists/ytcp-text-dropdown-trigger/ytcp-dropdown-trigger/div'