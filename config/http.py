import os
from urllib.parse import urlparse

class AppMetadata():
    
    default_thumbsize = 320
    full_uri: str
    width: int
    height: int
    quality: int = 80
    keep_aspect: bool
    
    def __init__(self, uri: str) -> None:
        self.full_uri = uri
        self.width = self.default_thumbsize
        self.height = self.default_thumbsize
        
        self._extract_uri_properties()
        
    def _extract_uri_properties(self):
        params = self.uri_app_params()
        
        for prop in params: 
            if prop.startswith('s:'):
                scale = prop.replace('s:', '')
                scale_data = scale.split('-')
                self.width = int(scale_data[0]) if len(scale_data) > 0 else self.default_thumbsize
                self.height = int(scale_data[1]) if len(scale_data) > 1 else self.width
            if prop.startswith('q:'):
                quality = prop.replace('q:', '')
                self.quality = int(quality)
            # TODO: implementar
            #if prop.startswith('p:'):
            #    self.keep_aspect = True
            #if prop.startswith('w:'):
            #    self.width = prop.replace('w:', '')
            #if prop.startswith('h:'):
            #    self.height = prop.replace('h:', '')
        
        self.width = max(1, min(self.width, 2048))
        self.height = max(1, min(self.height, 2048))
        self.quality = max(1, min(self.quality, 100))
                
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
        base = f"{out_file_fullname[0:str(out_file_fullname).rfind('.')]}"
        size = f"{self.width}x{self.height}"
        quality = f"q{self.quality}"
        
        return f"{base}-{size}-{quality}.webp"

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
        uri = f"{environ['wsgi.url_scheme']}://{environ['HTTP_HOST']}{environ['REQUEST_URI'].replace('thumb', '')}"
    elif file_mode == 'remote':
        uri = f"{remote_base_uri}{environ['REQUEST_URI'].replace('thumb', '')}"
    
    app_metadata = AppMetadata(uri)
    uri = app_metadata.uri_without_app_params()
    
    origin = origin_from_uri(uri)
    domain = domain_from_uri(uri)
    path = path_from_uri(uri)
    filename = filename_from_uri(uri)
    filedir = filedir_from_uri(uri)