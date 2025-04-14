#!/usr/bin/env python3

import os
import sys
import json
import shutil
import re
import yaml
import mimetypes
from pathlib import Path
from slugify import slugify
import argparse
from datetime import datetime, timezone

REPO_BASE = Path(__file__).resolve().parent.parent.parent
NOTAS_DIR = REPO_BASE / "notas"
DEST_DIR = REPO_BASE / "content" / "post"
ATTACHMENTS_DIR = Path.home() / "attachments"
STATIC_IMG_DIR = REPO_BASE / "static" / "imagens"

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True)
args = parser.parse_args()

# Limpar notas antigas
if DEST_DIR.exists():
    for item in DEST_DIR.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    print(f"🧹 Pasta limpa: {DEST_DIR}")

def corrigir_links(texto):
    return re.sub(r"\[\[([^\|\]]+)(\|([^\]]+))?\]\]", r"[\3\1](\1.md)", texto)

def copiar_e_renomear_imagens(texto, nome_nota_slug):
    imagens = re.findall(r'!\[\[(.*?)\]\]', texto)
    slug_map = {}
    for idx, img in enumerate(imagens, start=1):
        nome = Path(img).name
        if nome in slug_map:
            continue  # já processado

        src = ATTACHMENTS_DIR / nome
        if src.exists():
            ext = Path(nome).suffix
            dest_name = f"{nome_nota_slug}_{idx}{ext}"
            dest_path = STATIC_IMG_DIR / dest_name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest_path)
            slug_map[nome] = dest_name
        else:
            print(f"⚠️ Imagem não encontrada: {src}")
    return slug_map

def corrigir_imagens(texto, slug_map):
    def substitui(match):
        path = match.group(1).strip()
        nome_original = Path(path).name
        nome_novo = slug_map.get(nome_original)
        if nome_novo:
            alt_text = nome_novo.rsplit('.', 1)[0].replace('_', ' ')
            return f'{{{{< taped src="/imagens/{nome_novo}" alt="{alt_text}" >}}}}'
        return ''
    return re.sub(r'!\[\[(.*?)\]\]', substitui, texto)

def corrigir_data(conteudo):
    padrao = re.compile(r'^date:\s*(\d{2})-(\d{2})-(\d{4})(?:\s+(\d{2}):(\d{2}))?', re.MULTILINE)

    def substituir(m):
        dia, mes, ano = m.group(1), m.group(2), m.group(3)
        hora, minuto = m.group(4) or "00", m.group(5) or "00"
        return f"date: {ano}-{mes}-{dia}T{hora}:{minuto}:00"

    return padrao.sub(substituir, conteudo)

# Começar a processar
with open(args.input, 'r', encoding='utf-8') as f:
    paths = json.load(f)

for relpath in paths:
    fonte = NOTAS_DIR / relpath
    if not fonte.exists():
        print(f"⚠️ Ficheiro não encontrado: {fonte}")
        continue

    ext = Path(fonte).suffix.lower()
    if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
        # Copiar imagem solta com nome transformado
        nome_imagem = Path(fonte).name
        src = ATTACHMENTS_DIR / nome_imagem
        if src.exists():
            # Deduzir nome da nota a partir do ficheiro anterior na lista
            i = paths.index(relpath)
            nota_anterior = next((p for p in reversed(paths[:i]) if p.endswith(".md")), None)
            if nota_anterior:
                nome_nota_slug = slugify(Path(nota_anterior).stem)
                contador = sum(1 for x in paths[:i+1] if x.endswith(Path(fonte).name))
                dest_name = f"{nome_nota_slug}_{contador}{ext}"
                dest_path = STATIC_IMG_DIR / dest_name
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest_path)
                print(f"🖼️ Imagem copiada: {src} → {dest_path}")
            else:
                print(f"⚠️ Imagem {src} ignorada (sem nota anterior)")
        else:
            print(f"⚠️ Imagem listada mas não encontrada: {src}")
        continue

    # Se não for imagem, assume que é uma nota
    tipo, _ = mimetypes.guess_type(fonte)
    if tipo and not tipo.startswith("text/"):
        print(f"📦 Ignorado (não é ficheiro de texto): {fonte}")
        continue

    with open(fonte, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    nome_nota_slug = slugify(Path(relpath).stem)
    conteudo = corrigir_links(conteudo)
    slug_map = copiar_e_renomear_imagens(conteudo, nome_nota_slug)
    conteudo = corrigir_imagens(conteudo, slug_map)
    conteudo = corrigir_data(conteudo)

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    nome_ficheiro = Path(relpath).name
    destino = DEST_DIR / nome_ficheiro

    with open(destino, 'w', encoding='utf-8') as f:
        f.write(conteudo)

    print(f"✅ Nota exportada: {destino}")
