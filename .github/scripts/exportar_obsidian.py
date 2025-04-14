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

REPO_BASE = Path(__file__).resolve().parent.parent.parent
NOTAS_DIR = REPO_BASE / "notas"
DEST_DIR = REPO_BASE / "content" / "post"
ATTACHMENTS_DIR = Path.home() / "cinquenta" / "attachments"
STATIC_IMG_DIR = REPO_BASE / "static" / "img"

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True)
args = parser.parse_args()

def corrigir_links(texto):
    return re.sub(r"\[\[([^\|\]]+)(\|([^\]]+))?\]\]", r"[\3\1](\1.md)", texto)

def corrigir_imagens(texto, slug_map):
    def substitui(match):
        path = match.group(1).strip()
        nome_original = Path(path).name
        nome_slug = slug_map.get(nome_original)
        if nome_slug:
            return f'{{{{< taped src="/img/{nome_slug}" alt="{slugify(nome_original)}" >}}}}'
        return ''
    return re.sub(r'!\[\[(.*?)\]\]', substitui, texto)

def copiar_e_slugificar_imagens(texto):
    imagens = re.findall(r'!\[\[(.*?)\]\]', texto)
    slug_map = {}
    for img in imagens:
        nome = Path(img).name
        src = ATTACHMENTS_DIR / nome
        if src.exists():
            dest_name = slugify(nome)
            dest_path = STATIC_IMG_DIR / dest_name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest_path)
            slug_map[nome] = dest_name
        else:
            print(f"Imagem não encontrada: {src}")
    return slug_map

def corrigir_data(conteudo):
    padrao = re.compile(r'^date:\s*(\d{2})-(\d{2})-(\d{4})(?:\s+(\d{2}):(\d{2}))?', re.MULTILINE)

    def substituir(m):
        dia, mes, ano = m.group(1), m.group(2), m.group(3)
        hora, minuto = m.group(4) or "00", m.group(5) or "00"
        return f"date: {ano}-{mes}-{dia}T{hora}:{minuto}:00"

    return padrao.sub(substituir, conteudo)

def gerar_nome_unico(dest_dir, nome_base):
    destino = dest_dir / nome_base
    contador = 1
    while destino.exists():
        nome_sem_ext, ext = os.path.splitext(nome_base)
        destino = dest_dir / f"{nome_sem_ext}-{contador}{ext}"
        contador += 1
    return destino

with open(args.input, 'r', encoding='utf-8') as f:
    paths = json.load(f)

for relpath in paths:
    fonte = NOTAS_DIR / relpath
    if not fonte.exists():
        print(f"Nota não encontrada: {fonte}")
        continue

    with open(fonte, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    conteudo = corrigir_links(conteudo)
    slug_map = copiar_e_slugificar_imagens(conteudo)
    conteudo = corrigir_imagens(conteudo, slug_map)
    conteudo = corrigir_data(conteudo)

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    nome_ficheiro = Path(relpath).name
    destino = gerar_nome_unico(DEST_DIR, nome_ficheiro)

    with open(destino, 'w', encoding='utf-8') as f:
        f.write(conteudo)

    print(f"✅ Nota exportada: {destino}")
