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

# Corrigir data no front matter
partes = conteudo.split('---')
if len(partes) >= 3:
    yaml_part = yaml.safe_load(partes[1])

    try:
        data_original = yaml_part.get('date')
        print(f"Data original ({relpath}): {data_original} (tipo: {type(data_original)})")

        if isinstance(data_original, datetime):
            data = data_original
        elif isinstance(data_original, str):
            # Tenta parsear como datetime ISO primeiro
            try:
                data = datetime.fromisoformat(data_original.replace('Z', '+00:00'))
            except ValueError:
                # Se falhar, tenta outros formatos comuns
                formatos_validos = [
                    "%Y-%m-%dT%H:%M:%S%z",  # ISO com timezone
                    "%Y-%m-%d %H:%M:%S%z",   # Espaço com timezone
                    "%Y-%m-%dT%H:%M:%S",     # ISO sem timezone
                    "%Y-%m-%d %H:%M:%S",     # Espaço sem timezone
                    "%Y-%m-%d",              # Apenas data
                    "%d-%m-%Y %H:%M:%S",     # Formato europeu
                    "%d-%m-%Y %H:%M",
                    "%d-%m-%Y"
                ]
                data = None
                for formato in formatos_validos:
                    try:
                        data = datetime.strptime(data_original, formato)
                        break
                    except ValueError:
                        continue
                if data is None:
                    raise ValueError(f"Nenhum formato válido corresponde a: {data_original}")

        # Garantir que a data tenha timezone (UTC se não especificado)
        if data.tzinfo is None:
            data = data.replace(tzinfo=timezone.utc)
        
        # Formatar no padrão RFC 3339 que o Hugo requer
        yaml_part['date'] = data.isoformat(timespec='seconds')

    except Exception as e:
        print(f"Erro crítico ao tratar data em '{relpath}': {e}")
        # Usar data de modificação do arquivo como fallback
        mtime = datetime.fromtimestamp(fonte.stat().st_mtime, tz=timezone.utc)
        yaml_part['date'] = mtime.isoformat(timespec='seconds')

    # Gerar YAML corretamente
    novo_yaml = yaml.dump(
        yaml_part,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False
    )

    # Remover aspas da data se o PyYAML tiver adicionado
    novo_yaml = re.sub(r"date: ['\"](.+?)['\"]", r'date: \1', novo_yaml)

    conteudo = f"---\n{novo_yaml}---\n{partes[2]}"
    print(f"Conteúdo processado para {relpath}:\n{conteudo[:200]}...")  # Log parcial para debug    
    # Gravar destino preservando subpastas
    destino = DEST_DIR / Path(relpath)
    destino.parent.mkdir(parents=True, exist_ok=True)

    with open(destino, 'w', encoding='utf-8') as f:
        f.write(conteudo)

    print(f"✅ Nota exportada: {destino}")
