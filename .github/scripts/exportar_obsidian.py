#!/usr/bin/env python3

import os
import re
import shutil
import filecmp
from pathlib import Path
from urllib.parse import quote
import unicodedata
import yaml

# Caminhos base
REPO_BASE = Path(__file__).resolve().parent.parent.parent
NOTAS_DIR = REPO_BASE / "notas"
DEST_DIR = REPO_BASE / "content" / "post"
ATTACHMENTS_DIR = Path.home() / "cinquenta" / "attachments"
IMG_DEST_DIR = REPO_BASE / "static" / "imagens"

# Slugify simples

def slugify(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)

# Verificar se nota tem publish: true

def deve_publicar(caminho_ficheiro):
    with open(caminho_ficheiro, 'r', encoding='utf-8') as f:
        for linha in f:
            if linha.strip().lower() == 'publish: true':
                return True
    return False

# Corrigir links internos [[...]] → [...](...)

def corrigir_links(conteudo):
    def format_link(link_text):
        link_text = link_text.strip().strip('"').strip("'")
        if '|' in link_text:
            target, alias = link_text.split('|', 1)
        else:
            target = alias = link_text
        slug = slugify(Path(target).stem)
        return f"[{alias.strip()}](/post/{slug})"

    return re.sub(r'\[\[(.+?)\]\]', lambda m: format_link(m.group(1)), conteudo)

# Corrigir datas

def corrigir_data(conteudo):
    padrao = re.compile(r'^date:\s*(\d{2})-(\d{2})-(\d{4})(?:\s+(\d{2}):(\d{2}))?', re.MULTILINE)

    def substituir(m):
        dia, mes, ano = m.group(1), m.group(2), m.group(3)
        hora, minuto = m.group(4) or "00", m.group(5) or "00"
        return f"date: {ano}-{mes}-{dia}T{hora}:{minuto}:00"

    return padrao.sub(substituir, conteudo)

# Substituir imagens pelas slugificadas e copiar

def substituir_e_copiar_imagens(conteudo):
    imagens_map = {}

    def sub_md(m):
        nome = m.group(1).strip()
        slug = imagens_map.get(nome)
        if not slug:
            slug = slugify(Path(nome).stem) + Path(nome).suffix.lower()
            imagens_map[nome] = slug
            origem = ATTACHMENTS_DIR / nome
            destino = IMG_DEST_DIR / slug
            if origem.exists():
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origem, destino)
                print(f"✅ Imagem copiada: {nome} → {slug}")
            else:
                print(f"⚠️ Imagem não encontrada: {nome}")
        return f'{{{{< taped src="/imagens/{quote(slug)}" alt="{nome}" >}}}}'

    conteudo = re.sub(r'!\[\[(.*?)\]\]', sub_md, conteudo)
    conteudo = re.sub(r'!\[.*?\]\((.*?)\)', sub_md, conteudo)
    return conteudo

# Exportar notas

def exportar_nota(caminho_original):
    with open(caminho_original, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    novo_conteudo = corrigir_data(corrigir_links(substituir_e_copiar_imagens(conteudo)))
    nome = Path(caminho_original).stem
    destino = DEST_DIR / f"{slugify(nome)}.md"

    if destino.exists():
        with open(destino, 'r', encoding='utf-8') as f:
            existente = f.read()
        if existente == novo_conteudo:
            print(f"🟡 Sem alterações: {destino.name}")
            return

    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, 'w', encoding='utf-8') as f:
        f.write(novo_conteudo)
    print(f"✅ Nota exportada: {destino.name}")

# Executar para todas as notas com publish: true

def main():
    for root, _, files in os.walk(NOTAS_DIR):
        for file in files:
            if file.endswith(".md"):
                caminho = Path(root) / file
                if deve_publicar(caminho):
                    exportar_nota(caminho)

if __name__ == '__main__':
    main()
