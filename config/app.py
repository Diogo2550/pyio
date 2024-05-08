from dotenv import dotenv_values

config = dotenv_values('.env')

def env(name: str, default = ''):
	try:
		return config[name]
	except:
		return default

# VARIÁVEIS DE AMBIENTE
videos_dir = env('VIDEOS_DIR', '/var/videos')
file_mode = env('FILE_MODE', 'local')
remote_base_uri = env('REMOTE_BASE_URI')
