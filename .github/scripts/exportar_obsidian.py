
import os
import re
import shutil
from urllib.parse import quote
import unicodedata

# Caminhos
# origem = os.path.expanduser("~/cinquenta")
# destino_md = os.path.expanduser("~/Projetos/digital-garden/content/post")
# pasta_attachments = os.path.join(origem, "attachments")
# pasta_imagens_destino = os.path.expanduser("~/Projetos/digital-garden/static/imagens")

origem = "notas"
destino_md = "content/post"
pasta_attachments = os.path.join(origem, "attachments")
pasta_imagens_destino = "static/imagens"


# Ferramenta de slugificação
def slugify(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)

# 1. Procurar notas com publish: true e copiar
import yaml

def deve_publicar(caminho_ficheiro):
    with open(caminho_ficheiro, 'r', encoding='utf-8') as f:
        lines = f.read()
        if lines.strip().startswith('---'):
            try:
                front = yaml.safe_load(lines.split('---')[1])
                return str(front.get("publish", "false")).lower() == "true"
            except Exception:
                return False
    return False


def copiar_notas_e_imagens():
    imagens_map = {}  # nome_original -> nome_slug
    for root, _, files in os.walk(origem):
        for file in files:
            if not file.endswith(".md"):
                continue
            caminho_original = os.path.join(root, file)
            if not deve_publicar(caminho_original):
                continue

            rel_path = os.path.relpath(caminho_original, origem)
            destino_ficheiro = os.path.join(destino_md, rel_path)
            os.makedirs(os.path.dirname(destino_ficheiro), exist_ok=True)
            shutil.copy2(caminho_original, destino_ficheiro)

            with open(destino_ficheiro, 'r', encoding='utf-8') as f:
                conteudo = f.read()

            # encontrar imagens ![[...]] e ![](...)
            imagens = re.findall(r'!\[\[(.*?)\]\]', conteudo) + re.findall(r'!\[.*?\]\((.*?)\)', conteudo)
            for nome in imagens:
                nome = nome.strip()
                if nome in imagens_map:
                    continue
                slug = slugify(os.path.splitext(nome)[0]) + os.path.splitext(nome)[1].lower()
                imagens_map[nome] = slug

                origem_img_1 = os.path.join(os.path.dirname(caminho_original), nome)
                origem_img_2 = os.path.join(pasta_attachments, nome)
                origem_img = origem_img_1 if os.path.isfile(origem_img_1) else origem_img_2

                if os.path.isfile(origem_img):
                    os.makedirs(pasta_imagens_destino, exist_ok=True)
                    destino_img = os.path.join(pasta_imagens_destino, slug)
                    shutil.copy2(origem_img, destino_img)
                    print(f"✅ Copiada: {nome} → {slug}")
                else:
                    print(f"⚠️ Não encontrada: {nome}")

    return imagens_map

# 2. Corrigir links internos [[...]] → [...](...)
def format_link(link_text):
    link_text = link_text.strip().strip('"').strip("'")
    if '|' in link_text:
        target, alias = link_text.split('|', 1)
    else:
        target = alias = link_text
    slug = slugify(target)
    return f"[{alias.strip()}](/post/{slug})"

def corrigir_links(conteudo):
    return re.sub(r'\[\[(.+?)\]\]', lambda m: format_link(m.group(1)), conteudo)

# 3. Corrigir datas
def corrigir_data(conteudo):
    padrao = re.compile(r'^date:\s*(\d{2})-(\d{2})-(\d{4})(?:\s+(\d{2}):(\d{2}))?', re.MULTILINE)
    def substituir(m):
        dia, mes, ano = m.group(1), m.group(2), m.group(3)
        hora, minuto = m.group(4) or "00", m.group(5) or "00"
        return f"date: {ano}-{mes}-{dia}T{hora}:{minuto}:00"
    return padrao.sub(substituir, conteudo)

# 4.1 + 4.2 Substituir imagens pelas slugificadas
def substituir_imagens(conteudo, imagens_map):
    def sub_md(m):
        nome = m.group(1).strip()
        slug = imagens_map.get(nome, nome)
        return f'{{{{< taped src="/imagens/{quote(slug)}" alt="{nome}" >}}}}'
    conteudo = re.sub(r'!\[.*?\]\((.*?)\)', sub_md, conteudo)
    conteudo = re.sub(r'!\[\[(.*?)\]\]', sub_md, conteudo)
    return conteudo

# Aplicar a todas as notas copiadas
def processar_notas(imagens_map):
    for root, _, files in os.walk(destino_md):
        for file in files:
            if not file.endswith(".md"):
                continue
            caminho = os.path.join(root, file)
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            novo = corrigir_data(corrigir_links(substituir_imagens(conteudo, imagens_map)))
            if conteudo != novo:
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write(novo)
                print(f"✏️ Atualizado: {caminho}")

# Executar tudo
imagens_map = copiar_notas_e_imagens()
processar_notas(imagens_map)
