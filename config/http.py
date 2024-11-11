import os
from urllib.parse import urlparse

class AppMetadata():
    
    resize: bool = False
    full_uri: str
    width: int
    height: int
    quality: int = 80
    keep_aspect: bool
    
    sender = {
        'host': ''
    }
    
    def __init__(self, uri: str) -> None:
        self.full_uri = uri        
        self._extract_uri_properties()
        
    def _extract_uri_properties(self):
        params = self.uri_app_params()
        
        for prop in params: 
            if prop.startswith('s:'):
                scale = prop.replace('s:', '')
                scale_data = scale.split('x')
                self.width = int(scale_data[0]) if len(scale_data) > 0 else -1
                self.height = int(scale_data[1]) if len(scale_data) > 1 else self.width
                self.resize = True
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
        
        if self.resize:
            self.width = max(1, min(self.width, 2048))
            self.height = max(1, min(self.height, 2048))
        self.quality = max(1, min(self.quality, 100))
                
    def uri_without_app_params(self):
        extension_index = self.full_uri.rfind('.')
        extension_size = self.full_uri.find('/', extension_index) - extension_index
        
        if extension_size < 0:
            return self.full_uri
        return self.full_uri[0:extension_index + extension_size]
        
    def uri_app_params(self):
        data = self.full_uri[self.full_uri.rfind('.'):].split('/')
        data.pop(0)
        return data
    
    def generate_thumb_name(self, out_file_fullname):
        base = f"{out_file_fullname[0:str(out_file_fullname).rfind('.')]}"
        size = f"{self.width}x{self.height}" if self.resize else 'original'
        quality = f"q{self.quality}"
        
        return f"{base}-{size}-{quality}.webp"

def path_from_uri(uri: str):
    return urlparse(uri).path
def filename_from_uri(uri: str):
    return os.path.basename(uri)
def filedir_from_uri(uri: str):
    return path_from_uri(uri).replace(filename_from_uri(uri), '')	

def configure(environ):
    from config.app import remote_base_uri, file_mode
    global schema, uri, domain, path, filename, filedir, app_metadata, sender_origin
    
    if remote_base_uri:
        sender_origin = remote_base_uri
    else:
        sender_origin = environ['HTTP_REFERER']
    
    if file_mode == 'local':
        #uri = f"{environ['wsgi.url_scheme']}://{environ['HTTP_HOST']}{environ['REQUEST_URI'].replace('thumb', '')}"
        uri = f"{environ['wsgi.url_scheme']}://{environ['HTTP_HOST']}{environ['REQUEST_URI']}"
    elif file_mode == 'remote':
        #uri = f"{sender_origin.strip('/')}{environ['REQUEST_URI'].replace('thumb', '')}"
        uri = f"{sender_origin.strip('/')}{environ['REQUEST_URI']}"
    
    app_metadata = AppMetadata(uri)
    uri = app_metadata.uri_without_app_params()
    
    path = path_from_uri(uri)
    filename = filename_from_uri(uri)
    filedir = filedir_from_uri(uri)
    schema = environ['wsgi.url_scheme']
    domain = environ['HTTP_HOST'].split(':')[0]