import os
from urllib.parse import urlparse

class AppMetadata():
	
	default_thumbsize = 320
	full_uri: str
	width: int
	height: int
	
	def __init__(self, uri: str) -> None:
		self.full_uri = uri
		self.width = self.default_thumbsize
		self.height = self.default_thumbsize
		
		self._extract_uri_properties()
		
	def _extract_uri_properties(self):
		params = self.uri_app_params()
		
		for prop in params: 
			if prop.startswith('is:'):
				scale = prop.replace('is:', '')
				scale_data = scale.split('-')
				self.width = int(scale_data[0]) if len(scale_data) > 0 else self.default_thumbsize
				self.height = int(scale_data[1]) if len(scale_data) > 1 else self.width
				
	def uri_without_app_params(self):
		extension_index = self.full_uri.rfind('.')
		extension_size = self.full_uri.find('/', extension_index) - extension_index
		
		uri = self.full_uri[0:extension_index + extension_size]
		return uri
		
	def uri_app_params(self):
		data = self.full_uri[self.full_uri.rfind('.'):].split('/')
		data.pop(0)
		return data
	
	def generate_thumb_name(self, out_file_fullname):
		return f"{out_file_fullname[0:str(out_file_fullname).rfind('.')]}-{self.width}x{self.height}.webp"

def path_from_uri(uri: str):
	return urlparse(uri).path
def domain_from_uri(uri: str):
	return urlparse(uri).hostname
def origin_from_uri(uri: str):
	return urlparse(uri).hostname
def schema_from_uri(uri: str):
	return urlparse(uri).scheme
def filename_from_uri(uri: str):
	return os.path.basename(uri)
def filedir_from_uri(uri: str):
	return path_from_uri(uri).replace(filename_from_uri(uri), '')

def configure(environ):
	from config.app import remote_base_uri, file_mode
	global uri, origin, domain, path, filename, filedir, app_metadata
	
	if file_mode == 'local':
		uri = f"{environ['REQUEST_SCHEME']}://{environ['HTTP_HOST']}{environ['REQUEST_URI'].replace('ithumb', '')}"
	elif file_mode == 'remote':
		uri = f"{remote_base_uri}{environ['REQUEST_URI'].replace('ithumb', '')}"
	
	app_metadata = AppMetadata(uri)
	uri = app_metadata.uri_without_app_params()
	
	origin = origin_from_uri(uri)
	domain = domain_from_uri(uri)
	path = path_from_uri(uri)
	filename = filename_from_uri(uri)
	filedir = filedir_from_uri(uri)