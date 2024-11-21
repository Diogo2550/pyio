import os

import config.app as appconf

from iffmpeg import create_video_thumbnail, media_exists

#https://api.identify.app.br/storage/creatives/video/2024/8/20/1724112040-fac-167610.mp4/is:280-280/ithumb

def main(environ, start_response):
    print("\n")
    import config.http as httpconf
    httpconf.configure(environ)
    
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

    # verifica se o arquivo existe
    out_exists = os.path.isfile(out_thumb_file_fullname)
    if(out_exists):
        start_response('200 OK', [('Content-Type', 'image/webp'), ('Cache-Control', 'public, max-age=86400')])
        return open(out_thumb_file_fullname, 'rb').read()
        
    if not media_exists(input_file_fullname):
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return ['Vídeo não encontrado!'.encode('utf-8')]
    
    # cria o arquivo, caso não exista
    thumb_fullname = create_video_thumbnail(input_file_fullname, out_thumb_file_fullname, httpconf.app_metadata)
    if(not thumb_fullname):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return ['Não foi possível gerar o vídeo.'.encode('utf-8')]
    
    # retorna o arquivo para o nginx
    start_response('200 OK', [('Content-Type', 'image/webp'), ('Cache-Control', 'public, max-age=86400')])
    return open(out_thumb_file_fullname, 'rb').read()
    
