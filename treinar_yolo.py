"""
Treina um modelo YOLOv8 para localizar (bounding box) e classificar o
lixo reciclavel ao mesmo tempo, usando um dataset anotado baixado do
Roboflow Universe (formato de exportacao: "YOLOv8", NAO o "Oriented
Bounding Boxes").

Como usar:
1. pip install ultralytics
2. Extraia o dataset baixado do Roboflow dentro da pasta do projeto.
3. Ajuste DATA_YAML abaixo para o caminho do arquivo data.yaml.
4. Rode: python treinar_yolo.py

Sobre o tempo de treino: sem GPU dedicada, isso pode demorar de 1 a
varias horas dependendo do tamanho do dataset e do numero de epocas.
Se tiver acesso a uma GPU NVIDIA, o script detecta e usa automaticamente.
Caso contrario, considere rodar no Google Colab (GPU gratuita) copiando
este mesmo script e o dataset para la.
"""

from ultralytics import YOLO
import torch

DATA_YAML = "data.yaml"  # o arquivo "data" esta na raiz do projeto, junto com train/valid/test

# 's' (small) da mais precisao que 'n' (nano) a um custo de treino/inferencia
# um pouco maior. Se o treino ficar impraticavelmente lento no seu notebook,
# troque para "yolov8n.pt".
MODELO_BASE = "yolov8s.pt"

EPOCHS = 100          # numero maximo de epocas
PACIENCIA = 20        # para o treino mais cedo se nao melhorar por 20 epocas seguidas
IMG_SIZE = 640
BATCH = 8              # valor conservador para GPUs com pouca VRAM (ex: 4GB); reduza para 4 se der erro de memoria


def main():
    dispositivo = 0 if torch.cuda.is_available() else "cpu"
    print(f"Treinando no dispositivo: {'GPU' if dispositivo == 0 else 'CPU'}")

    modelo = YOLO(MODELO_BASE)  # baixa os pesos pre-treinados na 1a execucao

    modelo.train(
        data=DATA_YAML,
        epochs=EPOCHS,
        patience=PACIENCIA,
        imgsz=IMG_SIZE,
        batch=BATCH,
        device=dispositivo,
        project="runs_lixeira",
        name="deteccao_lixo",
        # Aumentos de dados (augmentation) ja vem ativados por padrao no
        # ultralytics (mosaico, flip horizontal, variacao de HSV, etc.),
        # o que ajuda o modelo a generalizar melhor sem precisar configurar nada extra.
    )

    print("\nTreino concluido.")
    print("Pesos salvos em: runs_lixeira/deteccao_lixo/weights/best.pt")

    # Roda a validacao final e imprime as metricas (mAP, precisao, recall)
    metrica = modelo.val()
    print("\nResumo da validacao:")
    print(f"  mAP50:    {metrica.box.map50:.3f}")
    print(f"  mAP50-95: {metrica.box.map:.3f}")


if __name__ == "__main__":
    main()
