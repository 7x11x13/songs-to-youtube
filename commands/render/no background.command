ffmpeg -loglevel error -progress pipe:1 -y -r 1 -i "{coverArt}" -i "{song_path}" -r 24 -lavfi "setpts={songDuration}/TB" -acodec copy -vcodec libvpx-vp9 -lossless 1 "{fileOutput}"
