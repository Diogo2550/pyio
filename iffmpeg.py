import contextlib
import fcntl
import ffmpeg
import json
import os
import requests
import time
from io import BytesIO
from PIL import Image, ImageFile
from config.http import AppMetadata
import pillow_avif

ImageFile.LOAD_TRUNCATED_IMAGES = True

GET_TIMEOUT_SECONDS = 15
HEAD_TIMEOUT_SECONDS = 5

@contextlib.contextmanager
def _generation_lock(output_path: str):
    "Serializa geração/regeneração do mesmo output_path entre processos (uwsgi roda vários workers)"
    lock_path = output_path + '.lock'
    lock_file = open(lock_path, 'w')
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()

def create_image(input_path: str, output_path: str, meta: AppMetadata):
    "Cria ou regenera uma thumbnail de forma atômica e seguro para concorrência"
    thumb_q = meta.quality

    if(not media_exists(input_path)):
        return None

    out_dir_path = os.path.dirname(output_path)
    if(not os.path.exists(out_dir_path)):
        mkdir_recursive(out_dir_path)

    existed_before = os.path.isfile(output_path)

    with _generation_lock(output_path):
        # se o arquivo não existia e passou a existir enquanto esperávamos o lock,
        # outro worker já gerou pra gente: evita trabalho duplicado (cache stampede)
        if not existed_before and os.path.isfile(output_path):
            return output_path

        try:
            response = requests.get(input_path, timeout=GET_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[create_image] falha ao baixar '{input_path}': {e}")
            return None

        extension = input_path.split('.')[-1]
        temp_path = f"{time.time()}-{os.getpid()}-temp_img."
        try:
            img = Image.open(BytesIO(response.content))
            if(extension == 'avif'):
                temp_path += 'jpg'
                img.convert('RGB').save(temp_path)
            else:
                temp_path += extension
                img.save(temp_path)

            video_w, video_h = scale_aspect_ratio(temp_path, meta)

            # gera num arquivo temporário no mesmo diretório e só então troca
            # atomicamente pro nome final, pra quem já está lendo o arquivo
            # existente nunca ver um webp pela metade. Mantém a extensão original
            # no final do nome pro ffmpeg conseguir inferir o formato de saída.
            out_base_name = os.path.basename(output_path)
            tmp_output_path = os.path.join(out_dir_path, f".tmp-{os.getpid()}-{time.time()}-{out_base_name}")
            try:
                if meta.resize and not meta.keep_aspect:
                    ffmpeg.input(temp_path).filter('scale', video_w, video_h).filter('crop', meta.width, meta.height).output(tmp_output_path, **{'qscale:v': thumb_q}, vframes=1, loglevel="quiet").run(overwrite_output=True)
                else:
                    ffmpeg.input(temp_path).filter('scale', video_w, video_h).output(tmp_output_path, **{'qscale:v': thumb_q}, vframes=1, loglevel="quiet").run(overwrite_output=True)
            except ffmpeg.Error as e:
                print(f"[create_image] falha no ffmpeg para '{output_path}': {e}")
                if os.path.exists(tmp_output_path):
                    os.remove(tmp_output_path)
                return None

            os.chmod(tmp_output_path, 0o755)
            os.replace(tmp_output_path, output_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        _write_origin_meta(output_path, response.headers)
        return output_path

def _meta_path(output_path: str):
    return output_path + '.meta.json'

def _write_origin_meta(output_path: str, headers, checked_at: float = None):
    meta = {
        'etag': headers.get('ETag'),
        'last_modified': headers.get('Last-Modified'),
        'content_length': headers.get('Content-Length'),
        'checked_at': checked_at if checked_at is not None else time.time(),
    }
    with open(_meta_path(output_path), 'w') as f:
        json.dump(meta, f)

def _read_origin_meta(output_path: str):
    try:
        with open(_meta_path(output_path), 'r') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None

def touch_origin_meta(output_path: str):
    "Reseta o relógio de revalidação sem baixar/reprocessar a imagem"
    meta = _read_origin_meta(output_path)
    if meta is not None:
        meta['checked_at'] = time.time()
        with open(_meta_path(output_path), 'w') as f:
            json.dump(meta, f)

def is_cache_stale(output_path: str, revalidate_seconds: int):
    "True se o cache não tem metadados ainda ou passou da janela de revalidação"
    meta = _read_origin_meta(output_path)
    if meta is None:
        return True
    return (time.time() - meta.get('checked_at', 0)) >= revalidate_seconds

def origin_has_changed(input_path: str, output_path: str):
    """Checagem leve (HEAD) contra a origem.
    Retorna True (mudou), False (igual) ou None (não deu pra confirmar)."""
    meta = _read_origin_meta(output_path)
    if meta is None or (meta.get('etag') is None and meta.get('last_modified') is None):
        return None
    try:
        response = requests.head(input_path, timeout=HEAD_TIMEOUT_SECONDS)
    except requests.RequestException:
        return None
    if response.status_code >= 400:
        return None
    if meta.get('etag') and response.headers.get('ETag'):
        return response.headers['ETag'] != meta['etag']
    if meta.get('last_modified') and response.headers.get('Last-Modified'):
        return response.headers['Last-Modified'] != meta['last_modified']
    return None

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
        try:
            os.mkdir(dir_to_create)
            os.chmod(dir_to_create, mode)
        except FileExistsError:
            pass  # outro worker criou o mesmo diretório entre o check e o mkdir

    return mkdir_recursive(str.join('/', dirs), mode, dir_to_create)

def media_exists(media_path: str):
    from config.app import file_mode

    if file_mode == 'local':
        return os.path.isfile(media_path)
    elif file_mode == 'remote':
        try:
            return requests.head(media_path, timeout=HEAD_TIMEOUT_SECONDS, allow_redirects=True)
        except requests.RequestException as e:
            print(f"[media_exists] falha ao checar '{media_path}': {e}")
            return False
