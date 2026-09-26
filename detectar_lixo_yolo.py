"""
Deteccao e classificacao de lixo reciclavel em tempo real usando o modelo
YOLOv8 treinado (gerado pelo treinar_yolo.py).

Melhorias desta versao em relacao a anterior:
- Voto de maioria: em vez de confiar na classificacao de um unico frame,
  o sistema so pontua depois de observar varios frames seguidos e usar a
  categoria mais frequente entre eles. Isso reduz bastante o impacto de
  um frame ruim isolado (desfoque, reflexo, etc.) na pontuacao final.
- Sistema anti-fraude: so pontua quando um objeto NOVO aparece, exigindo
  que o compartimento fique vazio antes de aceitar o proximo.

Como usar:
    python detectar_lixo_yolo.py
"""

from collections import Counter, deque

import cv2
from ultralytics import YOLO

PESOS_MODELO = "runs/detect/runs_lixeira/deteccao_lixo-3/weights/best.pt"
CONFIANCA_MINIMA = 0.5
IOU_MINIMO = 0.45  # usado pelo YOLO para descartar caixas duplicadas do mesmo objeto

# Quantos frames seguidos SEM deteccao confirmam que o compartimento esvaziou
FRAMES_PARA_CONFIRMAR_VAZIO = 15
# Quantos frames seguidos COM deteccao sao observados antes de decidir a
# categoria final por voto de maioria
FRAMES_PARA_CONFIRMAR_OBJETO = 10

# Ajuste conforme os nomes de classe do SEU dataset (aparecem no data.yaml)
CATEGORIAS_NAO_RECICLAVEIS = {"organico", "rejeito", "nao reciclavel", "trash"}


def melhor_deteccao(resultado):
    """
    Retorna (x1, y1, x2, y2, categoria, confianca) da deteccao com maior
    confianca no frame atual, ou None se nenhuma passar do limiar minimo.
    """
    caixas = resultado.boxes
    if caixas is None or len(caixas) == 0:
        return None

    melhor_idx = int(caixas.conf.argmax())
    confianca = float(caixas.conf[melhor_idx])
    if confianca < CONFIANCA_MINIMA:
        return None

    x1, y1, x2, y2 = [int(v) for v in caixas.xyxy[melhor_idx].tolist()]
    classe_id = int(caixas.cls[melhor_idx])
    categoria = resultado.names[classe_id]
    return x1, y1, x2, y2, categoria, confianca


def acionar_pontuacao(categoria):
    """
    Placeholder: por enquanto so imprime no terminal. Depois entra aqui o
    codigo que envia um comando pro ESP32 (ex: HTTP, MQTT ou serial).
    """
    if categoria.lower() in CATEGORIAS_NAO_RECICLAVEIS:
        print(f">> '{categoria}' nao e reciclavel. Nenhum ponto.")
    else:
        print(f">> Descarte correto de '{categoria}'! +10 pontos.")


def main():
    modelo = YOLO(PESOS_MODELO)
    captura = cv2.VideoCapture(0)

    if not captura.isOpened():
        print("Nao foi possivel abrir a webcam.")
        return

    # Estados: "vazio" (esperando objeto novo) e "objeto_presente" (ja
    # pontuou este objeto, aguardando ele ser removido)
    estado = "vazio"
    contagem_ausencia = 0
    historico_categorias = deque(maxlen=FRAMES_PARA_CONFIRMAR_OBJETO)

    print("Pressione 'q' para sair.")

    while True:
        ok, frame = captura.read()
        if not ok:
            break

        resultados = modelo.predict(frame, conf=CONFIANCA_MINIMA, iou=IOU_MINIMO, verbose=False)
        deteccao = melhor_deteccao(resultados[0])

        if deteccao is not None:
            x1, y1, x2, y2, categoria, confianca = deteccao
            contagem_ausencia = 0

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            texto = f"{categoria} ({confianca*100:.1f}%)"
            cv2.putText(frame, texto, (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if estado == "vazio":
                historico_categorias.append(categoria)

                barra = f"Confirmando: {len(historico_categorias)}/{FRAMES_PARA_CONFIRMAR_OBJETO}"
                cv2.putText(frame, barra, (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (255, 255, 0), 2)

                if len(historico_categorias) >= FRAMES_PARA_CONFIRMAR_OBJETO:
                    # Voto de maioria: usa a categoria mais frequente entre
                    # os ultimos frames, nao so a do frame atual
                    categoria_final, _ = Counter(historico_categorias).most_common(1)[0]
                    acionar_pontuacao(categoria_final)
                    estado = "objeto_presente"
                    historico_categorias.clear()

        else:
            contagem_ausencia += 1
            historico_categorias.clear()  # objeto sumiu no meio da confirmacao, recomeca do zero

            if estado == "objeto_presente" and contagem_ausencia >= FRAMES_PARA_CONFIRMAR_VAZIO:
                estado = "vazio"

            status = "Aguardando objeto" if estado == "vazio" else "Retire o objeto anterior"
            cor = (0, 0, 255) if estado == "vazio" else (0, 165, 255)
            cv2.putText(frame, status, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)

        cv2.imshow("Deteccao YOLO - lixo reciclavel", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    captura.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
