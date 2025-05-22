import ffmpeg
import os
import requests
import time
from io import BytesIO
from PIL import Image
from config.http import AppMetadata

def create_image(input_path: str, output_path: str, meta: AppMetadata):
    "Cria uma thumbnail e gera uma thumbnail"
    thumb_q = meta.quality
    
    if(not media_exists(input_path)):
        return None
        
    if(not os.path.exists(os.path.dirname(output_path))):
        _path = os.path.dirname(output_path)
        mkdir_recursive(_path)
    
    response = requests.get(input_path)
    img = Image.open(BytesIO(response.content))
    temp_path = f"{time.time()}-temp_img." + input_path.split('.')[-1]
    img.save(temp_path)
    video_w, video_h = scale_aspect_ratio(temp_path, meta)
    
    if meta.resize and not meta.keep_aspect:
        ffmpeg.input(temp_path).filter('scale', video_w, video_h).filter('crop', meta.width, meta.height).output(output_path, **{'qscale:v': thumb_q}, vframes=1, loglevel="quiet").run()
    else:
        ffmpeg.input(temp_path).filter('scale', video_w, video_h).output(output_path, **{'qscale:v': thumb_q}, vframes=1, loglevel="quiet").run()
    
    os.chmod(output_path, 0o755)
    os.remove(temp_path)
    return output_path

def scale_aspect_ratio(input_path: str, meta: AppMetadata):
    video_w = video_h = 0
    with Image.open(input_path) as img:
        video_w = img.width
        video_h = img.height
    video_ratio = video_w / video_h
    
    new_w = meta.width if meta.resize else video_w   
    new_h = meta.height if meta.resize else video_h
    
    # faz o cálculo de height (novo / antigo)
    ratio_x = new_w / video_w
    ratio_y = new_h / video_h
    multiplier = ratio_y
    
    # pega o maior caso não precise manter o aspect ratio
    if not meta.keep_aspect and ratio_x > ratio_y:
        multiplier = ratio_x
    
    # pega o menor caso precise manter o aspect ratio
    if meta.keep_aspect and ratio_x < ratio_y:
        multiplier = ratio_x
        
    return video_w * multiplier, video_h * multiplier

def mkdir_recursive(full_path: str, mode: int = 0o755, relative_path: str = './'):
    dirs = full_path.split('/')
    
    if len(dirs) == 0 or dirs[0] == '':
        return True
    
    next_dir = dirs.pop(0)
    dir_to_create = os.path.join(relative_path, next_dir)
    
    if not os.path.isdir(dir_to_create):
        os.mkdir(dir_to_create)
        os.chmod(dir_to_create, mode)
        
    return mkdir_recursive(str.join('/', dirs), mode, dir_to_create)

def media_exists(media_path: str):
    from config.app import file_mode
    import requests
    
    if file_mode == 'local':
        return os.path.isfile(media_path)
    elif file_mode == 'remote':
        return requests.get(media_path)