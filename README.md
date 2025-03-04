# Python Image Optimizer - PyIO

Este projeto foi criado com o intuito de **melhorar a performance** dos sites cuidando da **otimização dos arquivos de imagens**, permitindo que os mesmo sejam **convertidos para webp** (formato de arquivo + recomendado devido a sua alta compactação) e **redimensionamento** de tamanho, além de permitir **alterar a qualidade** da imagem.

**Obs:** por padrão, todas as imagens serão automaticamente convertidas para webp.

## Tecnologias

Tecnologias utilizadas para o desenvolvimento:

- Python
- Docker
- Ffmpeg
- uWSGI

# Como utilizar

Vamos imaginar que temos um site com o domímio `pyio.com`. Podemos adicionar este micro-serviço em um subdomínio (ex. `img.pyio.com`) e, a partir do site principal, começar a buscar as imagens do subdomínio.

Então caso o site pyio.com tivesse a imagem `https://pyio.com/media/images/abc.jpg`, nós precisamos alterar o link para `https://img.pyio.com/media/images/abc.jpg`.

Só de fazer isso o site já terá um ganho de performance absurdo, pois todas as imagens serão convertidas automaticamente para `webp`.

Porém podemos fazer mais, podemos também redimensionar a imagem para encaixar exatamente onde queremos e otimizar ainda mais o site. Inclusive responsivamente, por exemplo:

Desktop: `https://img.pyio.com/media/images/abc.jpg/s:400x400`
mobile: `https://img.pyio.com/media/images/abc.jpg/s:200x200`.

É tão simples que você precisa de JS para fazer estas alterações, basta apenas utilizar uma tag \<picture> no lugar da \<img> e o próprio HTML cuidará da escolha para você.

*Você pode ver mais em API de Referência, ao término deste README.*

# Instalar projeto

Caso você queria utilizar o projeto em modo de desenvolvimento, você deverá:

1. criar um ambiente virtual python
2. executar o `pip install -r requirements.txt` para instalar os pacotes

Você também pode utilizar o docker em modo de desenvolvimento:

1. Clone o projeto em um local de preferência.
2. Abra a pasta da raiz do projeto no console.
3. Copie e cole o `.env.example` e modifique o `REMOTE_BASE_URI` para a URL do site que será otimizado (ex. http://localhost:8080)
4. Execute o comando: docker run --name pyio -p 5000:5000 -v \`pwd\`/:/app pyio uwsgi --ini /app/uwsgi.ini --py-autoreload=1 --touch-reload=app.py

## Executar Produção

Há uma imagem docker que você pode utilizar diretamente, sem ter de clonar o repositório do Github. Você pode utilizá-la com o comando:

`docker run --name pyio -p 5000:5000 --restart unless-stopped -d REMOTE_BASE_URI={url_site} diogo2550/pyio`

Onde `url_site` é a base do site que terá as imagens otimizadas (ex. http://localhost:8080).

# Deploy

O projeto foi testado apenas em sites pequenos, por isso, para casos mais avançados pode ser necessário modificar os valores em no arquivo uwsgi.ini, principalmente o:

- processes
- socket
- http

O sistema também não foi programado para funcionar com paralelismo, então não sei dizer o quão impactante será a mudança na quantidade de processos.

# API Reference

Para modificar uma imagem, é necessário enviar uma requisição para `{schema}://{host}/{caminho_imagem}/{parametros}`, tendo `parametros` o formato `parametro:valor`, sendo os modelos abaixo. 

Params:
[Size] s: {width}|{width}x{height} -> width|height sendo inteiros
Recomendado: a depender de sua aplicação

[Quality] q:{quality} -> 1 <= quality <= 100 (entre 1 e 100)
Faixa de valores recomendados: 70-80  
**O valor padrão é 80**

[Proportion] p: -> sua existência habilita a necessidade de mantera a proporção da imagem
Recomendado: ativar

## Exemplos

Redimensionar imagem para 400x400: http://localhost:5000/images/imagem1.jpg/s:400x400

Redimensionar imagem para 400x400 mantendo a proporção: http://localhost:5000/images/imagem1.jpg/s:400x400/p:

Altera a qualidade da imagem (quanto menor a qualidade, menor o tamanho): http://localhost:5000/images/imagem1.jpg/q:70

Você também pode juntar todas as opções ao mesmo tempo e rendimensionar enquanto altera a qualidade.