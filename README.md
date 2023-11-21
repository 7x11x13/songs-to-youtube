<img align="left" width="100" height="100" src="https://raw.githubusercontent.com/7x11x13/songs-to-youtube/master/songs_to_youtube/image/icon.ico" alt="icon">

# songs-to-youtube

Convert audio files to videos and upload them to YouTube automatically.

![Example](https://github.com/7x11x13/songs-to-youtube/blob/master/docs/example.png?raw=true)

## Features
- Extracts album covers from audio files
- Extracts other metadata which can be used in template strings for the video title/description etc.
- Can concatenate songs to upload an album as a single video
- Can upload an album as a playlist of multiple videos
- Does not use official YouTube API; can upload up to 50-100 videos per day
- Does not re-encode audio before uploading

## Pre-installation
- [FFmpeg](https://ffmpeg.org/download.html) is required to convert songs into videos
- [Firefox](https://www.mozilla.org/firefox/new/) and [geckodriver](https://github.com/mozilla/geckodriver/releases) (or Chrome and Chromedriver) are required to upload to YouTube
- Make sure FFmpeg and geckodriver/chromedriver are both in your PATH environment variable
- If you have a package manager you can install through that instead. e.g. with [Scoop](https://scoop.sh/):
```
scoop install ffmpeg
scoop install geckodriver
```

## Installation

### PyInstaller binary

Download the latest release for your platform [here](https://github.com/7x11x13/songs-to-youtube/releases), unzip the archive, and run the songs-to-youtube executable.

### Install from PyPI

```bash
$ pip install songs-to-youtube
$ songs-to-youtube
```

### Run from source

1. Have Python version 3.8-3.12 installed, and [poetry](https://python-poetry.org/)
2. Download the source code
3. Install required Python modules with `poetry install`
4. Run the program with `poetry run songs-to-youtube`

## Notes
- New versions of FFmpeg might cause problems, version 4.4 is confirmed to work
- Before you upload any videos, you must sign in to a YouTube account (File > Settings > Add new user)
- You can drag and drop songs on the main window to add them to the queue. The order in which they are uploaded goes from top to bottom
- You can also drag and drop images onto a song's current album art to change it
- Make sure the output file extension stays as .mkv
- The characters < and > will be replaced with fullwidth versions in titles and descriptions, as YouTube does not allow these symbols
- Video titles and descriptions longer than YouTube allows will be truncated (100, and 5000 characters respectively)

### Template strings
Write `~{key}` in any text field and it will be replaced with an appropriate value. If no value exists for that key, it will not be replaced. To see the available keys, right click on an album or song and select "View metadata."
Here are some useful values:
#### Song metadata
- `~{song_dir}` - directory of the input audio file
- `~{song_file}` - file name of the input audio
- `~{album}`
- `~{artist}`
- `~{title}`
- `~{date}`
- `~{comment}`
- `~{description}`
#### Album metadata
- `~{album_dir}` - directory of the album
- `~{timestamps}` - special key that generates timestamps based on song lengths. they will only be generated when concatenating songs into a single video
- `~{song.albumartist}` - name of the album's artist (usually)
The first song of an album can have its keys accessed by the album by prefixing the key with `song.`
#### Operators
##### Optional keys / preference ordering
A template string of the form `~{a|b|c}` will be replaced with the value of `a` if it exists, otherwise the value of `b` if it exists, and so on. Keys may not contain the character `|`
##### String literals
A template string of the form `~{a|"hello"}` will be replaced with the value for `a` if it exists, otherwise it will be replaced with `hello`. String literals may not contain the character `|`. They may contain `"` though, e.g. `~{""hello""}` will be replaced with `"hello"`
##### Safe filenames
Any key can be surrounded by `<` and `>` and the value of that key will be made safe to use as a filename. e.g. `~{<song.album>}.mkv` where `song.album` is `~{:¬Þ}` will be replaced with `____Þ_.mkv`
