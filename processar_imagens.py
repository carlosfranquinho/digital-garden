#!/usr/bin/env python3

import os
import re
import shutil
from pathlib import Path
from PIL import Image
from slugify import slugify

# Caminhos de origem e destino (ajusta conforme necessário)
vault_dir = Path("/caminho/para/obsidian-vault")
attachments_dir = vault_dir / "attachments"
notas_dir = vault_dir
destino_img = Path("static/imagens")

# JSON com notas e imagens, ou faz scan direta — exemplo simples:
mapa_notas = {
    "Borboleta Apollo.md": ["Pasted image 2025-04-15 110025.png", "Pasted image 2025-04-15 111034.png"],
    "Planta Aromática.md": ["Captured 2025-04-12 093000.png"]
}

def processar_imagem(origem_path, nome_nota_slug, contador, destino_dir, largura_max=1200):
    nome_base = f"{nome_nota_slug}-{contador}"
    nome_final = f"{nome_base}.webp"
    destino_path = destino_dir / nome_final

    with Image.open(origem_path) as img:
        if img.width > largura_max:
            nova_altura = int(img.height * largura_max / img.width)
            img = img.resize((largura_max, nova_altura))
        img.save(destino_path, "webp", quality=85)

    return nome_final

# Garantir pasta de destino
destino_img.mkdir(parents=True, exist_ok=True)

# Processar imagens
for nota, imagens in mapa_notas.items():
    slug = slugify(nota.replace(".md", ""))
    for i, img_nome in enumerate(imagens, start=1):
        origem = attachments_dir / img_nome
        if origem.exists():
            novo_nome = processar_imagem(origem, slug, i, destino_img)
            print(f"{img_nome} → {novo_nome}")
        else:
            print(f"[!] Não encontrado: {origem}")
