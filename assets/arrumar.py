#!/usr/bin/env python3
"""
Organizador de HTMLs para GitHub Pages + Jekyll
------------------------------------------------
PRESERVA o HTML ORIGINAL de cada pagina - nao mexe em CSS, estilo, tipografia, nada!
Apenas:
  1. Copia cada .html para pasta-propria/index.html
  2. Adiciona front matter Jekyll (title, permalink)
  3. Cria _config.yml
  4. Cria index.html raiz com navegacao
  5. Copia assets (imagens, CSS, JS) para pasta assets/
"""

import os
import re
import sys
import shutil
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Erro: BeautifulSoup nao instalado. Execute: pip install beautifulsoup4")
    sys.exit(1)


def slugify(text):
    """Converte texto em slug URL-safe."""
    text = text.lower().strip()
    text = re.sub(r'[áàâãä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[íìîï]', 'i', text)
    text = re.sub(r'[óòôõö]', 'o', text)
    text = re.sub(r'[úùûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    text = text.strip('-')
    return text or 'pagina'


def extract_title_from_html(filepath):
    """Extrai o titulo do HTML original sem modificar nada."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    title_tag = soup.find('title')
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True)
    
    h1 = soup.find('h1')
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    
    name = Path(filepath).stem
    name = name.replace('-', ' ').replace('_', ' ').title()
    return name


def main():
    PASTA_ORIGEM = os.path.abspath('.')
    PASTA_DESTINO = os.path.join(PASTA_ORIGEM, 'site-ghpages')
    TITULO_SITE = 'Paulo Leads'
    
    print('=' * 60)
    print('ORGANIZADOR - MODO PRESERVAR HTML ORIGINAL')
    print('=' * 60)
    print()
    print('Origem:  ' + PASTA_ORIGEM)
    print('Destino: ' + PASTA_DESTINO)
    print()
    
    # Remove destino se existir
    if os.path.exists(PASTA_DESTINO):
        shutil.rmtree(PASTA_DESTINO)
    
    # --- PASSO 1: Coletar todos os arquivos ---
    print('Coletando arquivos...')
    todos_arquivos = []
    for root, dirs, filenames in os.walk(PASTA_ORIGEM):
        # Pular pastas que nao interessam
        dirs[:] = [d for d in dirs if d not in ('site-ghpages', '_site', '.git', '__pycache__')]
        
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, PASTA_ORIGEM).replace('\\', '/')
            ext = os.path.splitext(filename)[1].lower()
            
            todos_arquivos.append({
                'path': full_path,
                'rel_path': rel_path,
                'ext': ext,
                'is_html': ext in ('.html', '.htm'),
                'name': filename,
                'stem': os.path.splitext(filename)[0],
                'dir': os.path.dirname(rel_path) if '/' in rel_path else ''
            })
    
    htmls = [f for f in todos_arquivos if f['is_html']]
    assets = [f for f in todos_arquivos if not f['is_html']]
    
    print('  HTMLs:  ' + str(len(htmls)))
    print('  Assets: ' + str(len(assets)))
    print()
    
    if not htmls:
        print('Nenhum arquivo HTML encontrado!')
        sys.exit(1)
    
    # --- PASSO 2: Mapear slugs ---
    print('Mapeando paginas...')
    slugs_usados = set()
    mapa_paginas = {}  # rel_path_sem_ext -> slug
    
    for f in htmls:
        caminho_limpo = re.sub(r'\.html?$', '', f['rel_path'])
        
        if f['stem'].lower() == 'index':
            if f['dir']:
                    base_slug = slugify(f['dir'].split('/')[-1])
            else:
                base_slug = 'home'
        else:
            base_slug = slugify(f['stem'])
        
        slug = base_slug
        contador = 1
        while slug in slugs_usados:
            slug = base_slug + '-' + str(contador)
            contador += 1
        
        slugs_usados.add(slug)
        mapa_paginas[caminho_limpo] = slug
    
    # --- PASSO 3: COPIAR HTMLS ORIGINAIS para pasta-propria/index.html ---
    print('Copiando HTMLs originais para estrutura de pastas...')
    paginas_processadas = []
    
    for f in htmls:
        caminho_limpo = re.sub(r'\.html?$', '', f['rel_path'])
        slug = mapa_paginas.get(caminho_limpo, slugify(f['stem']))
        
        # Le o HTML ORIGINAL completo - sem modificar nada
        with open(f['path'], 'r', encoding='utf-8', errors='replace') as fp:
            html_original = fp.read()
        
        # Extrai o titulo do HTML original
        titulo = extract_title_from_html(f['path'])
        
        # Cria a pasta da pagina
        pasta_pagina = os.path.join(PASTA_DESTINO, slug)
        os.makedirs(pasta_pagina, exist_ok=True)
        
        # Cria o front matter Jekyll
        front_matter = '---\n'
        front_matter += 'layout: default\n'
        front_matter += 'title: "' + titulo + '"\n'
        front_matter += 'permalink: /' + slug + '/\n'
        front_matter += '---\n'
        
        # Salva o HTML original INTEIRO dentro da pasta como index.html
        # mas primeiro precisamos REMOVER o <title> original se existir,
        # porque o Jekyll vai usar o do front matter? NAO - vamos manter TUDO
        # O Jekyll com layout: default vai USAR o layout padrao e IGNORAR
        # o conteudo do HTML. Entao na verdade precisamos de uma abordagem diferente...
        
        # Na verdade, se usarmos layout: default, o Jekyll vai pegar SÓ o conteudo
        # e enfiar no layout. Para PRESERVAR o HTML original, a pagina NAO pode
        # usar layout nenhum. Vamos usar layout: null.
        
        front_matter = '---\n'
        front_matter += 'layout: null\n'  # null = nao usa layout, mostra o HTML puro
        front_matter += 'title: "' + titulo + '"\n'
        front_matter += 'permalink: /' + slug + '/\n'
        front_matter += '---\n'
        
        # Salva o HTML original completo (com front matter)
        with open(os.path.join(pasta_pagina, 'index.html'), 'w', encoding='utf-8') as fp:
            fp.write(front_matter + '\n' + html_original)
        
        paginas_processadas.append({'slug': slug, 'title': titulo, 'original': f['rel_path']})
        
        rel = f['rel_path']
        print('  [OK] ' + rel + ' -> /' + slug + '/')
    
    # --- PASSO 4: Criar _config.yml ---
    print('\nCriando _config.yml...')
    config_lines = []
    config_lines.append('# Configuracoes do Site')
    config_lines.append('title: "' + TITULO_SITE + '"')
    config_lines.append('description: "Site organizado para GitHub Pages"')
    config_lines.append('url: "https://paulo-leads.github.io"')
    config_lines.append('baseurl: "/site"')
    config_lines.append('')
    config_lines.append('permalink: /:title/')
    config_lines.append('')
    config_lines.append('defaults:')
    config_lines.append('  - scope:')
    config_lines.append('      path: ""')
    config_lines.append('      type: "pages"')
    config_lines.append('    values:')
    config_lines.append('      layout: "null"')
    
    with open(os.path.join(PASTA_DESTINO, '_config.yml'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(config_lines))
    
    # --- PASSO 5: Copiar assets (imagens, CSS, JS) ---
    print('Copiando assets...')
    for f in assets:
        dest_path = os.path.join(PASTA_DESTINO, 'assets', f['rel_path'])
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(f['path'], dest_path)
    
    # --- PASSO 6: Criar index.html raiz ---
    print('Criando index.html raiz...')
    cards = []
    for p in sorted(paginas_processadas, key=lambda x: x['title']):
        card = ''
        card += '    <div class="card">\n'
        card += '        <h2><a href="/site/' + p['slug'] + '/">' + p['title'] + '</a></h2>\n'
        card += '        <p>Pagina: ' + p['original'] + '</p>\n'
        card += '        <a href="/site/' + p['slug'] + '/" class="btn">Acessar</a>\n'
        card += '    </div>'
        cards.append(card)
    
    cards_html = '\n'.join(cards)
    
    index_html = '''---
layout: null
permalink: /
---

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>''' + TITULO_SITE + '''</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
               line-height: 1.6; color: #333; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { background: #2c3e50; color: white; padding: 40px 0; text-align: center; }
        header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px; padding: 40px 0; }
        .card { background: white; border-radius: 8px; padding: 24px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: transform 0.2s; }
        .card:hover { transform: translateY(-4px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .card h2 { margin-bottom: 12px; }
        .card h2 a { color: #2980b9; text-decoration: none; }
        .card p { color: #666; margin-bottom: 16px; font-size: 0.9em; }
        .btn { display: inline-block; background: #2980b9; color: white; padding: 8px 20px;
               border-radius: 4px; text-decoration: none; font-weight: 500; }
        .btn:hover { background: #2471a3; }
        footer { text-align: center; padding: 20px; color: #999; }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>''' + TITULO_SITE + '''</h1>
        </div>
    </header>
    
    <main class="container">
        <div class="grid">
''' + cards_html + '''
        </div>
    </main>
    
    <footer>
        <div class="container">
            <p>&copy; 2026 ''' + TITULO_SITE + '''</p>
        </div>
    </footer>
</body>
</html>'''
    
    with open(os.path.join(PASTA_DESTINO, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # --- RESUMO ---
    print('\n' + '=' * 60)
    print('PRONTO! Site organizado em: ' + PASTA_DESTINO)
    print('=' * 60)
    print('\nPaginas criadas (HTML ORIGINAL preservado):')
    for p in sorted(paginas_processadas, key=lambda x: x['title']):
        print('  /' + p['slug'] + '/  <- ' + p['original'])
    
    print('\nEstrutura criada:')
    print('  ' + PASTA_DESTINO + '/')
    print('  |-- _config.yml')
    print('  |-- index.html          (pagina inicial com navegacao)')
    print('  |-- assets/             (imagens, CSS, JS originais)')
    for p in sorted(paginas_processadas, key=lambda x: x['slug']):
        print('  |-- ' + p['slug'] + '/')
        print('  |   |-- index.html    (HTML ORIGINAL completo)')
    
    print('\nPara commitar:')
    print('  cd ' + PASTA_DESTINO)
    print('  git init')
    print('  git add .')
    print('  git commit -m "Site organizado para GitHub Pages"')
    print('  git remote add origin https://github.com/paulo-leads/site.git')
    print('  git branch -M main')
    print('  git push -u origin main')


if __name__ == '__main__':
    main()