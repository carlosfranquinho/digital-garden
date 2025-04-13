#!/usr/bin/env python3

import os
import sys
import json
import shutil
import re
import yaml
from pathlib import Path
from slugify import slugify
import argparse
from datetime import datetime, timezone
from urllib.parse import quote

# Argumentos do script
parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True)  # ficheiro .json com lista de notas
parser.add_argument('--vault', required=True)  # caminho absoluto para o repositório obsidian-vault
args = parser.parse_args()

# Diretórios base
VAULT_DIR = Path(args.vault).resolve()
ATTACHMENTS_DIR = VAULT_DIR / "attachments"
REPO_BASE = Path(__file__).resolve().parent.parent.parent
DEST_DIR = REPO_BASE / "content" / "post"
STATIC_IMG_DIR = REPO_BASE / "static" / "imagens"

# Corrigir links internos [[...]]
def corrigir_links(conteudo):
    def format_link(link_text):
        link_text = link_text.strip().strip('"').strip("'")
        if '|' in link_text:
            target, alias = link_text.split('|', 1)
        else:
            target = alias = link_text
        slug = slugify(target)
        return f"[{alias.strip()}](/post/{slug})"

    return re.sub(r'(?<!\!)\[\[(.+?)\]\]', lambda m: format_link(m.group(1)), conteudo)

# Substituir imagens
def substituir_imagens(conteudo, slug_map):
    def sub_md(m):
        nome = m.group(1).strip()
        slug = slug_map.get(nome, nome)
        return f'{{{{< taped src="/imagens/{quote(slug)}" alt="{slugify(nome)}" >}}}}'

    conteudo = re.sub(r'!\[.*?\]\((.*?)\)', sub_md, conteudo)
    conteudo = re.sub(r'!\[\[(.*?)\]\]', sub_md, conteudo)
    return conteudo

# Copiar imagens
def copiar_e_slugificar_imagens(texto):
    imagens = re.findall(r'!\[\[(.*?)\]\]', texto) + re.findall(r'!\[.*?\]\((.*?)\)', texto)
    slug_map = {}
    for img in imagens:
        nome = Path(img).name
        src = ATTACHMENTS_DIR / nome
        if src.exists():
            slug = slugify(os.path.splitext(nome)[0]) + os.path.splitext(nome)[1].lower()
            dest = STATIC_IMG_DIR / slug
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            slug_map[nome] = slug
            print(f"📸 Imagem copiada: {nome} → {slug}")
        else:
            print(f"⚠️ Imagem não encontrada: {src}")
    return slug_map

# Corrigir datas no front matter
def corrigir_data(conteudo):
    padrao = re.compile(r'^date:\s*(\d{2})-(\d{2})-(\d{4})(?:\s+(\d{2}):(\d{2}))?', re.MULTILINE)
    def substituir(m):
        dia, mes, ano = m.group(1), m.group(2), m.group(3)
        hora, minuto = m.group(4) or "00", m.group(5) or "00"
        return f"date: {ano}-{mes}-{dia}T{hora}:{minuto}:00"
    return padrao.sub(substituir, conteudo)

# Ler lista de ficheiros
with open(args.input, 'r', encoding='utf-8') as f:
    paths = json.load(f)

# Processar cada nota
for relpath in paths:
    fonte = VAULT_DIR / relpath
    if not fonte.exists():
        print(f"❌ Nota não encontrada: {fonte}")
        continue

    with open(fonte, 'r', encoding='utf-8') as f:
        conteudo_original = f.read()

    slug_map = copiar_e_slugificar_imagens(conteudo_original)
    conteudo = substituir_imagens(conteudo_original, slug_map)
    conteudo = corrigir_links(conteudo)
    conteudo = corrigir_data(conteudo)

    nome_final = slugify(Path(relpath).stem) + ".md"
    destino = DEST_DIR / nome_final
    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists():
        with open(destino, 'r', encoding='utf-8') as f:
            existente = f.read()
        if existente == conteudo:
            print(f"⏩ Sem alterações: {nome_final}")
            continue

    with open(destino, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Nota exportada: {nome_final}")
