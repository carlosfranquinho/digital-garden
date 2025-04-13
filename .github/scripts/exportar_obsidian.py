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

REPO_BASE = Path(__file__).resolve().parent.parent.parent
NOTAS_DIR = REPO_BASE / "notas"
DEST_DIR = REPO_BASE / "content" / "post"
ATTACHMENTS_DIR = NOTAS_DIR.parent / "attachments"
STATIC_IMG_DIR = REPO_BASE / "static" / "imagens"

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True)
args = parser.parse_args()

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

def substituir_imagens(conteudo, slug_map):
    def sub_md(m):
        nome = m.group(1).strip()
        slug = slug_map.get(nome, nome)
        return f'{{{{< taped src="/imagens/{quote(slug)}" alt="{slugify(nome)}" >}}}}'

    conteudo = re.sub(r'!\[.*?\]\((.*?)\)', sub_md, conteudo)
    conteudo = re.sub(r'!\[\[(.*?)\]\]', sub_md, conteudo)
    return conteudo

def copiar_e_slugificar_imagens(texto):
    imagens = re.findall(r'!\[\[(.*?)\]\]', texto) + re.findall(r'!\[.*?\]\((.*?)\)', texto)
    slug_map = {}
    for img in imagens:
        nome = Path(img).name
        src1 = NOTAS_DIR / nome
        src2 = ATTACHMENTS_DIR / nome
        src = src1 if src1.exists() else src2
        if src.exists():
            slug = slugify(os.path.splitext(nome)[0]) + os.path.splitext(nome)[1].lower()
            dest = STATIC_IMG_DIR / slug
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            slug_map[nome] = slug
        else:
            print(f"⚠️ Imagem não encontrada: {nome}")
    return slug_map

def corrigir_data(conteudo):
    padrao = re.compile(r'^date:\s*(\d{2})-(\d{2})-(\d{4})(?:\s+(\d{2}):(\d{2}))?', re.MULTILINE)
    def substituir(m):
        dia, mes, ano = m.group(1), m.group(2), m.group(3)
        hora, minuto = m.group(4) or "00", m.group(5) or "00"
        return f"date: {ano}-{mes}-{dia}T{hora}:{minuto}:00"
    return padrao.sub(substituir, conteudo)

with open(args.input, 'r', encoding='utf-8') as f:
    paths = json.load(f)

for relpath in paths:
    fonte = NOTAS_DIR / relpath
    if not fonte.exists():
        print(f"Nota não encontrada: {fonte}")
        continue

    with open(fonte, 'r', encoding='utf-8') as f:
        conteudo_original = f.read()

    # Processamento em ordem correta
    slug_map = copiar_e_slugificar_imagens(conteudo_original)
    conteudo = substituir_imagens(conteudo_original, slug_map)
    conteudo = corrigir_links(conteudo)
    conteudo = corrigir_data(conteudo)

    # Caminho final da nota
    destino = DEST_DIR / Path(relpath).name
    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists():
        with open(destino, 'r', encoding='utf-8') as f:
            existente = f.read()
        if existente == conteudo:
            print(f"⏩ Sem alterações: {destino.name}")
            continue

    with open(destino, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Nota exportada: {destino.name}")
