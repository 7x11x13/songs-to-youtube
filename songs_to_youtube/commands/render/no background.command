ffmpeg -loglevel error -progress pipe:1 -y -r 1 -i "{coverArt}" -i "{song_path}" -r 24 -vf "setpts={songDuration}/TB" -acodec {audioCodec} -vcodec libvpx-vp9 -lossless 1 "{fileOutput}"
