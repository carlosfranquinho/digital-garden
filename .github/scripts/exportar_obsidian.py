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

# Caminhos (mantidos como antes)
REPO_BASE = Path(__file__).resolve().parent.parent.parent
NOTAS_DIR = REPO_BASE / "notas"
DEST_DIR = REPO_BASE / "content" / "post"
ATTACHMENTS_DIR = Path.home() / "cinquenta" / "attachments"

# Argumento (mantido como antes)
parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True, help="Ficheiro JSON com paths das notas a exportar")
args = parser.parse_args()

# Funções auxiliares (mantidas como antes)
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

# Lê paths das notas a exportar (mantido como antes)
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

    # Processar front matter
    # Corrigir data no front matter se necessário
    partes = conteudo.split('---')
    if len(partes) >= 3:
        yaml_part = yaml.safe_load(partes[1])
        from datetime import datetime

        if 'date' in yaml_part:
            try:
                # Converte a data no formato "13-04-2025 20:30" para ISO
                data_original = yaml_part['date']
                data_convertida = datetime.strptime(data_original, "%d-%m-%Y %H:%M")
                yaml_part['date'] = data_convertida.isoformat()
            except Exception as e:
                print(f"⚠️ Data inválida em '{relpath}': {e}")
                # Substitui por data de modificação do ficheiro
                mtime = datetime.fromtimestamp(fonte.stat().st_mtime)
                yaml_part['date'] = mtime.isoformat()
        else:
            # Se não houver campo 'date', usa a data de modificação do ficheiro
            mtime = datetime.fromtimestamp(fonte.stat().st_mtime)
            yaml_part['date'] = mtime.isoformat()

        novo_yaml = yaml.dump(yaml_part, allow_unicode=True)
        conteudo = f"---\n{novo_yaml}---\n{partes[2]}"

        # Gravar destino preservando subpastas
        destino = DEST_DIR / Path(relpath)
        destino.parent.mkdir(parents=True, exist_ok=True)

        with open(destino, 'w', encoding='utf-8') as f:
            f.write(conteudo)

        print(f"✅ Nota exportada: {destino}")

