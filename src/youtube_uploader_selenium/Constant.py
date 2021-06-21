import re

class Constant:
    """A class for storing constants for YoutubeUploader class"""
    YOUTUBE_URL = 'https://www.youtube.com'
    YOUTUBE_STUDIO_URL = 'https://studio.youtube.com'
    YOUTUBE_UPLOAD_URL = 'https://www.youtube.com/upload'
    USER_WAITING_TIME = 1
    USER_AVATAR_XPATH = '//button[@id="avatar-btn"]/yt-img-shadow/img[@id="img"][@alt="Avatar image"]'
    VIDEO_TITLE = 'title'
    VIDEO_DESCRIPTION = 'description'
    PLAYLIST = 'playlist'
    TAGS = 'tags'
    NOTIFY_SUBS = 'notify_subs'
    DESCRIPTION_CONTAINER = '//*[@label="Description"]'
    MORE_OPTIONS_CONTAINER = '//*[text() = "Show more"]'
    PLAYLIST_CONTAINER = '//span[@class="dropdown-trigger-text style-scope ytcp-text-dropdown-trigger"][text()[contains(.,"Select")]]'
    PLAYLIST_SEARCH = '//*[@id="search-input"]'
    PLAYLIST_SEARCH_CLEAR_BUTTON = '//*[@class="style-scope ytcp-playlist-dialog"]/tp-yt-iron-icon[@class="remove-defaults style-scope ytcp-icon-button"]'
    PLAYLIST_NEW_BUTTON = '/html/body/ytcp-playlist-dialog/tp-yt-paper-dialog/div[2]/ytcp-button[1]/div'
    PLAYLIST_NEW_TITLE = '//div[@id="create-playlist-form"]/div/ytcp-form-textarea/div/textarea'
    PLAYLIST_DONE_BUTTON = '//*[@class="done-button action-button style-scope ytcp-playlist-dialog"]/*[text() = "Done"]'
    PLAYLIST_CREATE_BUTTON = '//*[@class="create-playlist-button action-button style-scope ytcp-playlist-dialog"][@label="Create"]'
    PLAYLIST_VISIBILITY_DROPDOWN = '//*[@class="input-container visibility style-scope ytcp-playlist-dialog"]'
    PLAYLIST_LABEL = "//label[./span/span[@class='label label-text style-scope ytcp-checkbox-group']]"
    TOOLTIP = '//ytcp-paper-tooltip'
    TAGS_TEXT_INPUT = '//input[@aria-label="Tags"]'
    NOTIFY_SUBSCRIBERS_CHECKBOX = '//ytcp-checkbox-lit[@id="notify-subscribers"]/div'
    TEXTBOX = 'textbox'
    TEXT_INPUT = 'text-input'
    RADIO_LABEL = 'radioLabel'
    STATUS_CONTAINER = '/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[1]/ytcp-video-upload-progress/span'
    NOT_MADE_FOR_KIDS_LABEL = 'NOT_MADE_FOR_KIDS'
    NEXT_BUTTON = 'next-button'
    VIDEO_URL_CONTAINER = "//span[@class='video-url-fadeable style-scope ytcp-video-info']"
    VIDEO_URL_ELEMENT = "//a[@class='style-scope ytcp-video-info']"
    HREF = 'href'
    UPLOADED = 'Uploading'
    ERROR_CONTAINER = '//*[@id="error-message"]'
    VIDEO_NOT_FOUND_ERROR = 'Could not find video_id'
    DONE_BUTTON = 'done-button'
    INPUT_FILE_VIDEO = "//input[@type='file']"
    USERNAME_ID = "account-name"
    VIDEO_PUBLISHED_DIALOG = '//*[@id="dialog-title"]'
    
    PROGRESS_REGEX = re.compile(r"Uploading (?P<progress>\d+)%.*")

    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_TAGS_LENGTH = 500

    @staticmethod
    def lookup(s):
        for name, value in vars(Constant).items():
            if s == value:
                return name
        return value
