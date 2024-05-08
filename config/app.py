from dotenv import dotenv_values

config = dotenv_values('.env')

videos_dir = config['VIDEOS_DIR'] or '/var/videos'