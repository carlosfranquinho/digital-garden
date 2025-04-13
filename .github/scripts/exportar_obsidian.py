#!/usr/bin/env python3

import os
import sys
import json
import shutil
import re
import yaml
from pathlib import Path
from slugify import slugify

# Caminhos
REPO_BASE = Path(__file__).resolve().parent.parent.parent
NOTAS_DIR = REPO_BASE / "notas"
DEST_DIR = REPO_BASE / "content" / "post"
ATTACHMENTS_DIR = Path.home() / "cinquenta" / "attachments"  # ajustar se necessário

# Argumento
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True, help="Ficheiro JSON com paths das notas a exportar")
args = parser.parse_args()

# Funções auxiliares
def corrigir_links(texto):
    return re.sub(r"\[\[([^\|\]]+)(\|([^\]]+))?\]\]", r"[\3\1](\1.md)", texto)

def corrigir_imagens(texto, imagens_copiadas, slug_map):
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
            dest_path = REPO_BASE / "static" / "img" / dest_name
            shutil.copy2(src, dest_path)
            slug_map[nome] = dest_name
    return slug_map

# Lê paths das notas a exportar
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
    conteudo = corrigir_imagens(conteudo, slug_map, slug_map)

    # Corrigir data no front matter se necessário
    partes = conteudo.split('---')
    if len(partes) >= 3:
        yaml_part = yaml.safe_load(partes[1])
        if 'date' not in yaml_part:
            yaml_part['date'] = fonte.stat().st_mtime  # pode formatar melhor se quiseres
        novo_yaml = yaml.dump(yaml_part, allow_unicode=True)
        conteudo = f"---\n{novo_yaml}---\n{partes[2]}"

    # Gravar destino
    destino = DEST_DIR / Path(relpath).name
    with open(destino, 'w', encoding='utf-8') as f:
        f.write(conteudo)

    print(f"✅ Nota exportada: {destino}")
