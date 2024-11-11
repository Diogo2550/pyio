import ffmpeg
import os
from config.http import AppMetadata

def create_video_thumbnail(video_path: str, video_output_path: str, meta: AppMetadata):
    "Cria uma thumbnail e gera uma thumbnail"
    thumb_q = meta.quality
    
    output_file_path = video_output_path
    if(not media_exists(video_path)):
        return None
        
    if(not os.path.exists(os.path.dirname(output_file_path))):
        _path = os.path.dirname(output_file_path)
        mkdir_recursive(_path)
    
    video_w, video_h = scale_aspect_ratio(video_path, meta)
    
    if meta.resize:
        ffmpeg.input(video_path).filter('scale', video_w, video_h).filter('crop', meta.width, meta.height).output(output_file_path, **{'qscale:v': thumb_q}, vframes=1, loglevel="quiet").run()
    else:
        ffmpeg.input(video_path).filter('scale', video_w, video_h).output(output_file_path, **{'qscale:v': thumb_q}, vframes=1, loglevel="quiet").run()
    
    os.chmod(output_file_path, 0o755)
    return output_file_path

def scale_aspect_ratio(video_path: str, meta: AppMetadata):
    probe = ffmpeg.probe(video_path)
    video_w = int(probe['streams'][0]['width'])
    video_h = int(probe['streams'][0]['height'])
    video_ratio = video_w / video_h
    
    new_w = meta.width if meta.resize else video_w   
    new_h = meta.width if meta.resize else video_h
    
    # faz o cálculo de height (novo / antigo) e pega o maior
    ratio_x = new_w / video_w
    ratio_y = new_h / video_h
    multiplier = ratio_y
    
    if ratio_x > ratio_y:
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
    
    if file_mode == 'local':
        return os.path.isfile(media_path)
    elif file_mode == 'remote':
        return True