from dotenv import dotenv_values, load_dotenv
import os

load_dotenv()
config = dotenv_values('.env')

def env(name: str, default = None):
	try:
		return config[name]
	except:
		return default

# VARIÁVEIS DE AMBIENTE
videos_dir = os.getenv('VIDEOS_DIR', '/var/videos')
file_mode = os.getenv('FILE_MODE', 'remote')
remote_base_uri = os.getenv('REMOTE_BASE_URI')
local_base_dir = os.getenv('LOCAL_BASE_DIR')
ignore_prefix_dir = os.getenv('IGNORE_PREFIX_DIR')