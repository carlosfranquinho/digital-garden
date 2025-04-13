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

# Caminhos
REPO_BASE = Path(__file__).resolve().parent.parent.parent
NOTAS_DIR = REPO_BASE / "notas"
DEST_DIR = REPO_BASE / "content" / "post"
ATTACHMENTS_DIR = Path.home() / "cinquenta" / "attachments"
STATIC_IMG_DIR = REPO_BASE / "static" / "img"

# Argumento
parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True, help="Ficheiro JSON com paths das notas a exportar")
args = parser.parse_args()

# Funções auxiliares
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
            print(f"⚠️ Imagem não encontrada: {src}")
    return slug_map

# Ler paths das notas
with open(args.input, 'r', encoding='utf-8') as f:
    paths = json.load(f)

for relpath in paths:
    fonte = NOTAS_DIR / relpath
    if not fonte.exists():
        print(f"❌ Nota não encontrada: {fonte}")
        continue

    with open(fonte, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    # Corrigir links internos
    conteudo = corrigir_links(conteudo)

    # Copiar imagens e gerar shortcodes
    slug_map = copiar_e_slugificar_imagens(conteudo)
    conteudo = corrigir_imagens(conteudo, slug_map)

    # Corrigir data no front matter
    partes = conteudo.split('---')
    if len(partes) >= 3:
        yaml_part = yaml.safe_load(partes[1])

        try:
if 'date' in yaml_part:
    data_original = yaml_part['date']
    if isinstance(data_original, datetime):
        data = data_original
    else:
        formatos_validos = ["%Y-%m-%d", "%d-%m-%Y %H:%M", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"]
        data = None
        for formato in formatos_validos:
            try:
                data = datetime.strptime(data_original, formato)
                break
            except ValueError:
                continue
        if data is None:
            try:
                data = datetime.fromisoformat(data_original)
            except ValueError:
                raise Exception(f"Formato de data inválido: {data_original}")

    yaml_part['date'] = data.isoformat()
else:
    mtime = datetime.fromtimestamp(fonte.stat().st_mtime)
    yaml_part['date'] = mtime.isoformat()

            else:
                mtime = datetime.fromtimestamp(fonte.stat().st_mtime)
                yaml_part['date'] = mtime.isoformat()
        except Exception as e:
            print(f"⚠️ Erro ao tratar data em '{relpath}': {e}")
            mtime = datetime.fromtimestamp(fonte.stat().st_mtime)
            yaml_part['date'] = mtime.isoformat()

        novo_yaml = yaml.dump(yaml_part, allow_unicode=True, sort_keys=False)
        conteudo = f"---\n{novo_yaml}---\n{partes[2]}"

    # Escrever nota corrigida para DEST_DIR
    destino = DEST_DIR / relpath
    destino.parent.mkdir(parents=True, exist_ok=True)

    with open(destino, 'w', encoding='utf-8') as f:
        f.write(conteudo)

    print(f"✅ Processado: {relpath}")
