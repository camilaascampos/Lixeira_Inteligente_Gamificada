"""
Continua o treinamento do modelo JA TREINADO (best.pt atual), agora usando
um dataset novo/combinado, em vez de comecar do zero com os pesos padrao
do YOLO. Isso aproveita tudo que o modelo ja aprendeu como ponto de
partida (transfer learning a partir do seu proprio modelo).

Recomendado: rode primeiro o python/combinar_datasets.py para juntar seu
dataset atual com o novo -- isso evita que o modelo "esqueca" o que aprendeu
com o dataset original. Ele gera 'dataset_combinado/data.yaml', que e o que
este script usa.

Como usar (a partir da raiz do repositorio):
    python python/continuar_treino_novo_dataset.py
"""

from pathlib import Path

import torch
from ultralytics import YOLO

RAIZ = Path(__file__).resolve().parent.parent
MODELO_ATUAL = RAIZ / "modelo" / "best.pt"
DATA_YAML = RAIZ / "dataset_combinado" / "data.yaml"  # ou outro data.yaml que for usar

EPOCHS = 50            # geralmente precisa de menos epocas que um treino do zero
PACIENCIA = 15
IMG_SIZE = 640
BATCH = 8               # ajuste conforme sua GPU (reduza se der erro de memoria)


def main():
    for caminho in (MODELO_ATUAL, DATA_YAML):
        if not caminho.exists():
            print(f"Arquivo nao encontrado: {caminho}")
            return

    dispositivo = 0 if torch.cuda.is_available() else "cpu"
    print(f"Treinando no dispositivo: {'GPU' if dispositivo == 0 else 'CPU'}")

    modelo = YOLO(str(MODELO_ATUAL))  # carrega o SEU modelo, nao o padrao do YOLO

    modelo.train(
        data=str(DATA_YAML),
        epochs=EPOCHS,
        patience=PACIENCIA,
        imgsz=IMG_SIZE,
        batch=BATCH,
        device=dispositivo,
        project=str(RAIZ / "runs"),
        name="deteccao_lixo_v2",
    )

    metrica = modelo.val()
    print("\nResumo da validacao:")
    print(f"  mAP50:    {metrica.box.map50:.3f}")
    print(f"  mAP50-95: {metrica.box.map:.3f}")

    melhor = getattr(modelo.trainer, "best", None)
    print(f"\nTreino concluido. Novo modelo salvo em: {melhor}")
    print("Para usa-lo, copie esse arquivo para 'modelo/best.pt' (guarde antes o antigo).")


if __name__ == "__main__":
    main()
