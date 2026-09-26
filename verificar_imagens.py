"""
python verificar_imagens.py
"""

import os
import shutil
from PIL import Image

DATASET_DIR = "dataset"          
PASTA_QUARENTENA = "_invalidas"  
EXTENSOES_VALIDAS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")


def imagem_valida(caminho):
    try:
        with Image.open(caminho) as img:
            img.verify()  
        with Image.open(caminho) as img:
            img.load()
            return img.format in ("JPEG", "PNG", "BMP", "GIF", "WEBP")
    except Exception:
        return False


def normalizar_para_rgb(caminho):
    """
    Forca a imagem a ter exatamente 3 canais (RGB), convertendo imagens em
    escala de cinza, com transparencia (RGBA/paleta) ou em CMYK. Isso evita
    o erro 'Number of channels requested does not match input' que o
    TensorFlow lanca quando o dataset mistura imagens com quantidades
    diferentes de canais.
    """
    try:
        with Image.open(caminho) as img:
            if img.mode != "RGB":
                img.convert("RGB").save(caminho, quality=95)
        return True
    except Exception:
        return False


def main():
    total = 0
    invalidas = 0
    normalizadas = 0

    for raiz, _, arquivos in os.walk(DATASET_DIR):
        if PASTA_QUARENTENA in raiz:
            continue
        for nome in arquivos:
            if not nome.lower().endswith(EXTENSOES_VALIDAS):
                continue
            caminho = os.path.join(raiz, nome)
            total += 1

            if not imagem_valida(caminho):
                invalidas += 1
                caminho_relativo = os.path.relpath(raiz, DATASET_DIR)
                destino_pasta = os.path.join(PASTA_QUARENTENA, caminho_relativo)
                os.makedirs(destino_pasta, exist_ok=True)
                shutil.move(caminho, os.path.join(destino_pasta, nome))
                print(f"Invalida, movida: {caminho}")
                continue

            with Image.open(caminho) as img:
                precisa_normalizar = img.mode != "RGB"

            if precisa_normalizar:
                if normalizar_para_rgb(caminho):
                    normalizadas += 1
                    print(f"Convertida para RGB: {caminho}")
                else:
                    invalidas += 1
                    caminho_relativo = os.path.relpath(raiz, DATASET_DIR)
                    destino_pasta = os.path.join(PASTA_QUARENTENA, caminho_relativo)
                    os.makedirs(destino_pasta, exist_ok=True)
                    shutil.move(caminho, os.path.join(destino_pasta, nome))
                    print(f"Falhou ao converter, movida: {caminho}")

    print(f"\nVerificacao concluida: {total} imagens checadas, "
          f"{normalizadas} convertidas para RGB, "
          f"{invalidas} invalidas movidas para '{PASTA_QUARENTENA}'.")


if __name__ == "__main__":
    main()
