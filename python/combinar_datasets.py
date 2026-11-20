"""
Combina dois datasets no formato YOLOv8 (cada um com train/valid/data.yaml)
em um dataset unico, unificando as categorias automaticamente -- mesmo que
os dois tenham nomes de classe diferentes ou em ordem diferente.

Como usar (a partir da raiz do repositorio):
1. Coloque o dataset atual em 'dataset_atual/' e o novo em 'dataset_novo/'
   (cada um com train/, valid/ e data.yaml). Ou ajuste PASTA_A e PASTA_B.
2. Rode: python python/combinar_datasets.py
3. Isso cria 'dataset_combinado/', que o python/continuar_treino_novo_dataset.py
   ja usa por padrao.

As pastas de dataset nao vao para o Git (estao no .gitignore).
"""

import os
import shutil
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
PASTA_A = str(RAIZ / "dataset_atual")       # seu dataset atual
PASTA_B = str(RAIZ / "dataset_novo")        # o dataset novo baixado
PASTA_SAIDA = str(RAIZ / "dataset_combinado")


def carregar_classes(pasta_dataset):
    with open(os.path.join(pasta_dataset, "data.yaml"), "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["names"]


def copiar_com_remapeamento(pasta_origem, split, prefixo, mapa_classes, pasta_saida):
    """Copia imagens e labels de um dataset, renomeando com prefixo (evita
    colisao de nomes entre os dois datasets) e remapeando os IDs de classe
    nos arquivos .txt de anotacao para o indice unificado."""
    origem_imgs = os.path.join(pasta_origem, split, "images")
    origem_labels = os.path.join(pasta_origem, split, "labels")
    destino_imgs = os.path.join(pasta_saida, split, "images")
    destino_labels = os.path.join(pasta_saida, split, "labels")
    os.makedirs(destino_imgs, exist_ok=True)
    os.makedirs(destino_labels, exist_ok=True)

    if not os.path.isdir(origem_imgs):
        print(f"Aviso: {origem_imgs} nao existe, pulando.")
        return 0

    total = 0
    for nome_arquivo in os.listdir(origem_imgs):
        nome_base, _ = os.path.splitext(nome_arquivo)
        novo_nome_base = f"{prefixo}_{nome_base}"

        # Copia a imagem
        shutil.copy2(
            os.path.join(origem_imgs, nome_arquivo),
            os.path.join(destino_imgs, novo_nome_base + os.path.splitext(nome_arquivo)[1]),
        )

        # Copia e remapeia o label correspondente, se existir
        caminho_label = os.path.join(origem_labels, nome_base + ".txt")
        destino_label = os.path.join(destino_labels, novo_nome_base + ".txt")
        if os.path.exists(caminho_label):
            with open(caminho_label, "r") as f_in, open(destino_label, "w") as f_out:
                for linha in f_in:
                    partes = linha.strip().split()
                    if not partes:
                        continue
                    classe_antiga = int(partes[0])
                    classe_nova = mapa_classes[classe_antiga]
                    f_out.write(" ".join([str(classe_nova)] + partes[1:]) + "\n")
        else:
            # Imagem sem objeto anotado (background) -- cria label vazio
            open(destino_label, "w").close()

        total += 1

    return total


def main():
    for pasta in (PASTA_A, PASTA_B):
        if not os.path.exists(os.path.join(pasta, "data.yaml")):
            print(f"data.yaml nao encontrado em: {pasta}")
            return
    if os.path.exists(PASTA_SAIDA):
        print(f"A pasta '{PASTA_SAIDA}' ja existe. Apague-a antes de rodar de novo.")
        return

    classes_a = carregar_classes(PASTA_A)
    classes_b = carregar_classes(PASTA_B)

    # Une as classes, mantendo a ordem de A e adicionando as novas de B no final
    classes_unificadas = list(classes_a)
    for nome in classes_b:
        if nome not in classes_unificadas:
            classes_unificadas.append(nome)

    mapa_a = {i: classes_unificadas.index(nome) for i, nome in enumerate(classes_a)}
    mapa_b = {i: classes_unificadas.index(nome) for i, nome in enumerate(classes_b)}

    print("Classes do dataset A:", classes_a)
    print("Classes do dataset B:", classes_b)
    print("Classes unificadas:  ", classes_unificadas)

    for split in ["train", "valid"]:
        n_a = copiar_com_remapeamento(PASTA_A, split, "a", mapa_a, PASTA_SAIDA)
        n_b = copiar_com_remapeamento(PASTA_B, split, "b", mapa_b, PASTA_SAIDA)
        print(f"{split}: {n_a} imagens do dataset A + {n_b} imagens do dataset B")

    # Gera o novo data.yaml
    novo_yaml = {
        "train": "train/images",
        "val": "valid/images",
        "nc": len(classes_unificadas),
        "names": classes_unificadas,
    }
    with open(os.path.join(PASTA_SAIDA, "data.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(novo_yaml, f, allow_unicode=True)

    print(f"\nDataset combinado criado em: {PASTA_SAIDA}/")
    print("Proximo passo: python python/continuar_treino_novo_dataset.py")


if __name__ == "__main__":
    main()
