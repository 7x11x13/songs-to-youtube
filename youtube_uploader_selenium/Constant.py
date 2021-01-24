class Constant:
    """A class for storing constants for YoutubeUploader class"""
    YOUTUBE_URL = 'https://www.youtube.com'
    YOUTUBE_STUDIO_URL = 'https://studio.youtube.com'
    YOUTUBE_UPLOAD_URL = 'https://www.youtube.com/upload'
    USER_WAITING_TIME = 1
    USER_AVATAR_XPATH = '//img[@id="img"][@alt="Avatar image"]'
    VIDEO_TITLE = 'title'
    VIDEO_DESCRIPTION = 'description'
    PLAYLIST = 'playlist'
    TAGS = 'tags'
    DESCRIPTION_CONTAINER = '/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/' \
                            'ytcp-uploads-details/div/ytcp-uploads-basics/ytcp-mention-textbox[2]'
    MORE_OPTIONS_CONTAINER = '/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/' \
                             'ytcp-uploads-details/div/div/ytcp-button/div'
    PLAYLIST_CONTAINER = '/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/' \
                         'ytcp-uploads-details/div/ytcp-uploads-basics/ytcp-video-metadata-playlists/' \
                         'ytcp-text-dropdown-trigger/ytcp-dropdown-trigger/div'
    PLAYLIST_SEARCH = '//*[@id="search-input"]'
    PLAYLIST_SEARCH_CLEAR_BUTTON = '/html/body/ytcp-playlist-dialog/paper-dialog/div[1]/ytcp-icon-button'
    PLAYLIST_NEW_BUTTON = '/html/body/ytcp-playlist-dialog/paper-dialog/div[2]/ytcp-button[1]/div'
    PLAYLIST_NEW_TITLE = '/html/body/ytcp-playlist-dialog/paper-dialog/div[2]/div[1]/ytcp-form-textarea/div/textarea'
    PLAYLIST_DONE_BUTTON = '/html/body/ytcp-playlist-dialog/paper-dialog/div[2]/ytcp-button[3]/div'
    PLAYLIST_CREATE_BUTTON = '/html/body/ytcp-playlist-dialog/paper-dialog/div[3]/ytcp-button[2]/div'
    PLAYLIST_VISIBILITY_DROPDOWN = '/html/body/ytcp-playlist-dialog/paper-dialog/div[2]/div[2]/ytcp-text-dropdown-trigger'
    PLAYLIST_LABEL = "//label[./span/span[@class='label label-text style-scope ytcp-checkbox-group']]"
    TOOLTIP = '//ytcp-paper-tooltip'
    TAGS_TEXT_INPUT = '/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-details/div/' \
                       'ytcp-uploads-advanced/ytcp-form-input-container/div[1]/div[2]/ytcp-free-text-chip-bar/ytcp-chip-bar/div/input'
    TEXTBOX = 'textbox'
    TEXT_INPUT = 'text-input'
    RADIO_LABEL = 'radioLabel'
    STATUS_CONTAINER = '/html/body/ytcp-uploads-dialog/paper-dialog/div/ytcp-animatable[2]/' \
                       'div/div[1]/ytcp-video-upload-progress/span'
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

    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_TAGS_LENGTH = 500
