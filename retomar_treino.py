"""
Retoma um treinamento do YOLO que foi interrompido (Ctrl+C ou fechamento
do terminal), continuando exatamente da ultima epoca salva -- sem perder
o progresso anterior.

Como usar:
    python retomar_treino.py
"""

from ultralytics import YOLO

CHECKPOINT = "runs/detect/runs_lixeira/deteccao_lixo-3/weights/last.pt"


def main():
    modelo = YOLO(CHECKPOINT)
    modelo.train(resume=True)  # continua com os mesmos parametros do treino original


if __name__ == "__main__":
    main()
