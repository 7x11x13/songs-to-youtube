ffmpeg -loglevel error -progress pipe:1 -y -f concat -safe 0 -i "{input_file_list}" -c copy "{fileOutputPath}"
