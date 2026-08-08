import os

import config.app as appconf

from iffmpeg import create_image, media_exists, is_cache_stale, origin_has_changed, touch_origin_meta

def _parse_range(range_header, file_size):
    "Retorna (start, end) | None (sem range) | False (range inválido)"
    if not range_header:
        return None
    if not range_header.startswith('bytes='):
        return False
    try:
        range_spec = range_header[len('bytes='):].split(',')[0].strip()
        start_str, end_str = range_spec.split('-', 1)
        if start_str == '':
            suffix_len = int(end_str)
            start = max(file_size - suffix_len, 0)
            end = file_size - 1
        else:
            start = int(start_str)
            end = int(end_str) if end_str != '' else file_size - 1
        end = min(end, file_size - 1)
        if start < 0 or start > end:
            return False
        return (start, end)
    except (ValueError, IndexError):
        return False

def _image_response(start_response, environ, file_path, httpconf, is_canonical):
    stat = os.stat(file_path)
    file_size = stat.st_size
    etag = f'"{int(stat.st_mtime)}-{file_size:x}"'
    cache_control = f'public, max-age={appconf.cache_revalidate_seconds}, must-revalidate'

    if environ.get('HTTP_IF_NONE_MATCH') == etag:
        start_response('304 Not Modified', [('Cache-Control', cache_control), ('ETag', etag)])
        return [b'']

    range_header = environ.get('HTTP_RANGE')
    byte_range = _parse_range(range_header, file_size)
    if byte_range is False:
        start_response('416 Range Not Satisfiable', [('Content-Range', f'bytes */{file_size}')])
        return [b'']

    name_without_ext = os.path.splitext(httpconf.filename)[0]
    safe_name = name_without_ext.replace('"', '').replace('\r', '').replace('\n', '')
    disposition_filename = f"{safe_name}.webp"

    headers = [
        ('Content-Type', 'image/webp'),
        ('Cache-Control', cache_control),
        ('ETag', etag),
        ('Accept-Ranges', 'bytes'),
        ('Content-Disposition', f'inline; filename="{disposition_filename}"'),
    ]

    if not is_canonical:
        canonical_url = f"{environ['wsgi.url_scheme']}://{environ['HTTP_HOST']}{httpconf.path}"
        headers.append(('Link', f'<{canonical_url}>; rel="canonical"'))

    with open(file_path, 'rb') as f:
        if byte_range:
            start, end = byte_range
            f.seek(start)
            body = f.read(end - start + 1)
            headers.append(('Content-Range', f'bytes {start}-{end}/{file_size}'))
            headers.append(('Content-Length', str(len(body))))
            start_response('206 Partial Content', headers)
        else:
            body = f.read()
            headers.append(('Content-Length', str(len(body))))
            start_response('200 OK', headers)

    return [body]

def main(environ, start_response):
    print("\n")
    import config.http as httpconf
    httpconf.configure(environ)

    if httpconf.path == '':
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return ['O pintinho diz: Pyio!'.encode('utf-8')]

    # declara variáveis
    server_videos_dir = appconf.videos_dir
    file_url_path = httpconf.path.strip('/')
    out_dir = 'medias'

    if appconf.ignore_prefix_dir != None:
        file_url_path = file_url_path.removeprefix(appconf.ignore_prefix_dir)

    if appconf.file_mode == 'remote':
        input_file_fullname = f"{httpconf.sender_origin.strip('/')}{httpconf.path}"
    elif appconf.file_mode == 'local':
        if appconf.local_base_dir != None:
            input_file_fullname = os.path.join(appconf.local_base_dir, file_url_path)
        else:
            input_file_fullname = os.path.join(server_videos_dir, httpconf.domain, file_url_path)

    out_file_fullname = os.path.join(out_dir, httpconf.domain, file_url_path)
    out_thumb_file_fullname = httpconf.app_metadata.generate_thumb_name(out_file_fullname)

    print('input: ' + input_file_fullname)
    print('output: ' + out_thumb_file_fullname)

    is_canonical = len(httpconf.app_metadata.uri_app_params()) == 0

    # verifica se o arquivo existe
    out_exists = os.path.isfile(out_thumb_file_fullname)
    if(out_exists):
        if is_cache_stale(out_thumb_file_fullname, appconf.cache_revalidate_seconds):
            changed = origin_has_changed(input_file_fullname, out_thumb_file_fullname)
            if changed:
                regenerated = create_image(input_file_fullname, out_thumb_file_fullname, httpconf.app_metadata)
                # se a origem sumiu/falhou, mantém servindo a versão em cache em vez de quebrar a URL
                if not regenerated:
                    touch_origin_meta(out_thumb_file_fullname)
            elif changed is False:
                touch_origin_meta(out_thumb_file_fullname)
            # changed is None (origem não respondeu): serve o cache sem tocar o relógio, tenta de novo na próxima
        return _image_response(start_response, environ, out_thumb_file_fullname, httpconf, is_canonical)

    if not media_exists(input_file_fullname):
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return ['Media não encontrado!'.encode('utf-8')]

    # cria o arquivo, caso não exista
    thumb_fullname = create_image(input_file_fullname, out_thumb_file_fullname, httpconf.app_metadata)
    if(not thumb_fullname):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return ['Não foi possível gerar o vídeo.'.encode('utf-8')]

    # retorna o arquivo para o nginx
    return _image_response(start_response, environ, out_thumb_file_fullname, httpconf, is_canonical)
