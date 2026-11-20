"""
Treina o modelo YOLOv8 que localiza e classifica o lixo reciclavel.

Antes de rodar:
1. Baixe o dataset no Roboflow no formato "YOLOv8" (NAO o "Oriented
   Bounding Boxes") e extraia dentro da pasta 'dataset/' na raiz do
   repositorio. Ela deve ficar assim:
       dataset/data.yaml
       dataset/train/  dataset/valid/  dataset/test/
2. Confira no data.yaml se os caminhos 'train:', 'val:' e 'test:' batem com
   as pastas (ex: "train/images", sem "../" na frente).
3. pip install -r requirements.txt  (e o PyTorch, veja o README)

Como usar (a partir da raiz do repositorio):
    python python/treinar_yolo.py

Sem GPU NVIDIA o treino e MUITO lento (horas por epoca). O script usa a GPU
automaticamente se ela estiver disponivel.
"""

from pathlib import Path

import torch
from ultralytics import YOLO

RAIZ = Path(__file__).resolve().parent.parent
DATA_YAML = RAIZ / "dataset" / "data.yaml"

# 's' (small) e mais preciso que 'n' (nano), mas mais pesado. Se o treino ficar
# lento demais ou faltar memoria, troque para "yolov8n.pt".
MODELO_BASE = "yolov8s.pt"

EPOCHS = 100     # maximo de epocas
PACIENCIA = 20   # para sozinho se nao melhorar por 20 epocas seguidas
IMG_SIZE = 640
BATCH = 8        # conservador para GPUs de 4 GB; reduza para 4 se faltar memoria


def main():
    if not DATA_YAML.exists():
        print(f"data.yaml nao encontrado em: {DATA_YAML}")
        print("Extraia o dataset do Roboflow dentro da pasta 'dataset/' (veja o topo deste arquivo).")
        return

    dispositivo = 0 if torch.cuda.is_available() else "cpu"
    print(f"Treinando no dispositivo: {'GPU' if dispositivo == 0 else 'CPU'}")

    modelo = YOLO(MODELO_BASE)  # baixa os pesos pre-treinados na 1a execucao

    modelo.train(
        data=str(DATA_YAML),
        epochs=EPOCHS,
        patience=PACIENCIA,
        imgsz=IMG_SIZE,
        batch=BATCH,
        device=dispositivo,
        project=str(RAIZ / "runs"),
        name="deteccao_lixo",
    )

    metrica = modelo.val()
    print("\nResumo da validacao:")
    print(f"  mAP50:    {metrica.box.map50:.3f}")
    print(f"  mAP50-95: {metrica.box.map:.3f}")

    melhor = getattr(modelo.trainer, "best", None)
    print(f"\nTreino concluido. Melhor modelo salvo em: {melhor}")
    print("Para usa-lo na deteccao, copie esse arquivo para 'modelo/best.pt'.")


if __name__ == "__main__":
    main()
