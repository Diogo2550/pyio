import os

import config.app as appconf

from iffmpeg import create_video_thumbnail

def main(environ, start_response):
	import config.http as httpconf
	httpconf.configure(environ)
	
	# declara variáveis
	server_videos_dir = appconf.videos_dir
	file_url_path = httpconf.path.strip('/')
	out_dir = 'medias'

	in_file_fullname = os.path.join(server_videos_dir, httpconf.domain, file_url_path)
	out_file_fullname = os.path.join(out_dir, httpconf.domain, file_url_path)
	out_thumb_file_fullname = httpconf.app_metadata.generate_thumb_name(out_file_fullname)

	print('input: ' + in_file_fullname)
	print('output: ' + out_thumb_file_fullname)

	# recebe a requisição do nginx

	# verifica se o arquivo existe
	in_exists = os.path.isfile(in_file_fullname)
	out_exists = os.path.isfile(out_thumb_file_fullname)
	if(out_exists):
		start_response('200 OK', [('Content-Type', 'image/webp')])
		return open(out_thumb_file_fullname, 'rb').read()
		
	if(not in_exists):
		start_response('404 Not Found', [('Content-Type', 'text/plain')])
		return ['Vídeo não encontrado!'.encode('utf-8')]
	
	# cria o arquivo, caso não exista
	thumb_fullname = create_video_thumbnail(in_file_fullname, out_thumb_file_fullname, httpconf.app_metadata.width, httpconf.app_metadata.height)
	if(not thumb_fullname):
		start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
		return ['Não foi possível gerar o vídeo.'.encode('utf-8')]
	
	# retorna o arquivo para o nginx
	start_response('200 OK', [('Content-Type', 'image/webp')])
	return open(out_thumb_file_fullname, 'rb').read()
