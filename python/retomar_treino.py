"""
Retoma um treino do YOLO que foi interrompido (Ctrl+C, terminal fechado,
queda de energia), continuando da ultima epoca salva.

Procura sozinho o 'last.pt' mais recente dentro de 'runs/'. Se quiser
retomar um treino especifico, passe o caminho:
    python python/retomar_treino.py runs/deteccao_lixo/weights/last.pt

Como usar (a partir da raiz do repositorio):
    python python/retomar_treino.py

Use este script (e nao o treinar_yolo.py) para continuar: assim nao cria
pastas novas e mantem o progresso. Se o treino ja tinha terminado todas as
epocas, nao ha o que retomar.
"""

import sys
from pathlib import Path

from ultralytics import YOLO

RAIZ = Path(__file__).resolve().parent.parent


def encontrar_ultimo_checkpoint():
    candidatos = list(RAIZ.glob("runs/**/weights/last.pt"))
    if not candidatos:
        return None
    return max(candidatos, key=lambda caminho: caminho.stat().st_mtime)


def main():
    if len(sys.argv) > 1:
        checkpoint = Path(sys.argv[1])
    else:
        checkpoint = encontrar_ultimo_checkpoint()

    if checkpoint is None or not checkpoint.exists():
        print("Nenhum checkpoint (last.pt) encontrado em 'runs/'.")
        print("Rode primeiro o python/treinar_yolo.py.")
        return

    print(f"Retomando de: {checkpoint}")
    modelo = YOLO(str(checkpoint))
    modelo.train(resume=True)  # continua com os mesmos parametros do treino original


if __name__ == "__main__":
    main()
