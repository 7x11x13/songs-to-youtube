import re


class Constant:
    """A class for storing constants for YoutubeUploader class"""

    YOUTUBE_URL = "https://www.youtube.com"
    YOUTUBE_STUDIO_URL = "https://studio.youtube.com"
    YOUTUBE_UPLOAD_URL = "https://www.youtube.com/upload"
    USER_WAITING_TIME = 1
    USER_AVATAR_XPATH = "/html/body/ytd-app/div/div/ytd-masthead/div[3]/div[3]/div[2]/ytd-topbar-menu-button-renderer[3]/button/yt-img-shadow/img"
    VIDEO_TITLE = "title"
    VIDEO_DESCRIPTION = "description"
    PLAYLIST = "playlist"
    TAGS = "tags"
    NOTIFY_SUBS = "notify_subs"
    DESCRIPTION_CONTAINER = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-basics/div[2]/ytcp-video-description/div/ytcp-social-suggestions-textbox"
    MORE_OPTIONS_CONTAINER = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/div/ytcp-button/div"
    PLAYLIST_CONTAINER = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-basics/div[4]/div[3]/div[1]/ytcp-video-metadata-playlists/ytcp-text-dropdown-trigger/ytcp-dropdown-trigger/div/div[2]/span"
    PLAYLIST_SEARCH = "/html/body/ytcp-playlist-dialog/tp-yt-paper-dialog/div[1]/input"
    PLAYLIST_SEARCH_CLEAR_BUTTON = "/html/body/ytcp-playlist-dialog/tp-yt-paper-dialog/div[1]/ytcp-icon-button/tp-yt-iron-icon"
    PLAYLIST_NEW_BUTTON = (
        "/html/body/ytcp-playlist-dialog/tp-yt-paper-dialog/div[2]/div/ytcp-button"
    )
    PLAYLIST_NEW_BUTTON_CREATE = "/html/body/ytcp-playlist-dialog/tp-yt-paper-dialog/div[2]/div/ytcp-text-menu/tp-yt-paper-dialog/tp-yt-paper-listbox/tp-yt-paper-item[1]"
    PLAYLIST_NEW_TITLE = "/html/body/ytcp-playlist-creation-dialog/ytcp-dialog/tp-yt-paper-dialog/div[2]/div/ytcp-playlist-metadata-editor/div/div[1]/ytcp-social-suggestions-textbox/ytcp-form-input-container/div[1]/div[2]/div/ytcp-social-suggestion-input/div"
    PLAYLIST_DONE_BUTTON = '/html/body/ytcp-playlist-dialog/tp-yt-paper-dialog/div[2]/ytcp-button[2]/div'
    PLAYLIST_CREATE_BUTTON = (
        "/html/body/ytcp-playlist-creation-dialog/ytcp-dialog/tp-yt-paper-dialog/div[3]/div/ytcp-button[2]"
    )
    PLAYLIST_VISIBILITY_DROPDOWN = (
        "/html/body/ytcp-playlist-creation-dialog/ytcp-dialog/tp-yt-paper-dialog/div[2]/div/ytcp-playlist-metadata-editor/div/ytcp-playlist-metadata-visibility/div/ytcp-text-dropdown-trigger"
    )
    PLAYLIST_LABEL = "//label[./span/span[@class='label label-text style-scope ytcp-checkbox-group']]"
    TOOLTIP = "//ytcp-paper-tooltip"
    TAGS_TEXT_INPUT = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-advanced/div[3]/ytcp-form-input-container/div[1]/div[2]/ytcp-free-text-chip-bar/ytcp-chip-bar/div/input"
    NOTIFY_SUBSCRIBERS_CHECKBOX = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-advanced/div[7]/div[4]/ytcp-checkbox-lit"
    TEXTBOX = "textbox"
    TEXT_INPUT = "text-input"
    RADIO_LABEL = "radioLabel"
    STATUS_CONTAINER = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[1]/ytcp-video-upload-progress/span"
    NOT_MADE_FOR_KIDS = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-basics/div[5]/ytkc-made-for-kids-select/div[4]/tp-yt-paper-radio-group/tp-yt-paper-radio-button[2]"
    NEXT_BUTTON = "next-button"
    VIDEO_URL_CONTAINER = (
        "//span[@class='video-url-fadeable style-scope ytcp-video-info']"
    )
    VIDEO_URL_ELEMENT = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-uploads-review/div[3]/ytcp-video-info/div/div[2]/div[1]/div[2]/span/a"
    UPLOADED = "Uploading"
    ERROR_CONTAINER = '//*[@id="error-message"]'
    DONE_BUTTON = "done-button"
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
