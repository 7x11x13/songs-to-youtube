# songs-to-youtube

Convert audio files to videos and upload them to YouTube automatically.

## Features
- Extract album covers from audio files
- Extract other metadata which can be used in template strings for the video title/description etc.
- Concatenate songs to upload an album as a single video
- Drag and drop support for audio files and album covers

## Requirements

- Install required Python modules with `py -m pip install -r requirements.txt`
- [FFmpeg](https://ffmpeg.org/download.html) binary is required to convert the songs into videos
- [Firefox](https://www.mozilla.org/firefox/new/) and [geckodriver](https://github.com/mozilla/geckodriver/releases) binaries are required to upload to YouTube
- Make sure FFmpeg and geckodriver are both in your PATH environment variable

## Usage

Download the source code and run `py main.py`

## Notes
You must login once on the first upload. This is far from finished; there are probably a lot of bugs, and many features to be implemented. This application works best when all your songs have been properly tagged.

### Template strings
Write `~{key}` in any text field and it will be replaced with an appropriate value. For now there is no way to see what keys are available for each item, but here are some useful ones:
#### Song metadata
- `~{song_dir}` - directory of the input audio file
- `~{song_file}` - file name of the input audio
- `~{tags.album}` - name of the song's album
- `~{tags.artist}` - name of the song's artist
- `~{tags.title}` - name of the song
#### Album metadata
- `~{album_dir}` - directory of the album
- `~{timestamps}` - special key that generates timestamps based on song lengths
- `~{song.tags.artist}` - name of the album's artist (usually)

The first song of an album can have its keys accessed by the album by prefixing the key with `song.`
