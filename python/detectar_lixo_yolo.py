"""
Deteccao de lixo reciclavel em tempo real (YOLOv8) com acionamento do ESP32.

Fluxo:
    camera (webcam ou celular) -> YOLO -> voto de maioria -> pontuacao -> ESP32

O sistema so pontua quando um objeto NOVO aparece: depois de pontuar, o
compartimento precisa ficar vazio antes de aceitar o proximo (anti-fraude).

Como usar (a partir da raiz do repositorio):
    python python/detectar_lixo_yolo.py

Tecla 'q' fecha a janela. Todas as configuracoes ficam na secao
CONFIGURACOES logo abaixo.
"""

import threading
import time
from collections import Counter, deque
from pathlib import Path

import cv2
import serial
from ultralytics import YOLO

# ============================ CONFIGURACOES ============================

RAIZ = Path(__file__).resolve().parent.parent
PESOS_MODELO = RAIZ / "modelo" / "best.pt"

# --- Fonte da imagem ---
# 0 = webcam do notebook (use 1, 2... se tiver mais de uma camera).
# Para usar a camera do CELULAR, coloque o endereco que o app mostra, entre
# aspas. Exemplo com o app "IP Webcam" (Android):
#   FONTE_CAMERA = "http://192.168.43.1:8080/video"
# O celular e o notebook precisam estar na mesma rede WiFi.
FONTE_CAMERA = 0
SEGUNDOS_SEM_IMAGEM_PARA_DESISTIR = 15

# --- ESP32 (cabo USB ou Bluetooth) ---
# PORTA_SERIAL: porta COM do ESP32 (Gerenciador de Dispositivos do Windows >
# "Portas (COM e LPT)"). Com Bluetooth, use a porta de tipo "Saida".
USAR_ESP32 = True  # False = so a deteccao, sem hardware conectado
PORTA_SERIAL = "COM4"
VELOCIDADE_SERIAL = 115200

# --- Deteccao ---
CONFIANCA_MINIMA = 0.65  # mais alto = menos falsos positivos (mao, fundo)
IOU_MINIMO = 0.45        # descarta caixas duplicadas do mesmo objeto

# Filtro por tamanho da caixa em relacao ao quadro: ignora ruido (muito
# pequena) e fundo/mao (muito grande).
AREA_MINIMA_RELATIVA = 0.03  # 3% do quadro
AREA_MAXIMA_RELATIVA = 0.65  # 65% do quadro

# --- Pontuacao ---
# Frames seguidos COM objeto observados antes de decidir a categoria final
# (voto de maioria entre eles).
FRAMES_PARA_CONFIRMAR_OBJETO = 10
# Frames seguidos SEM objeto para considerar o compartimento vazio de novo.
FRAMES_PARA_CONFIRMAR_VAZIO = 15

# Nomes de classe como aparecem no data.yaml do dataset.
CATEGORIAS_NAO_RECICLAVEIS = {"organico", "rejeito", "nao reciclavel", "trash"}

# Qual categoria aciona o servo: o nome exato da classe (ex: "plastic",
# "glass", "can", "paper") ou "todas" para qualquer categoria reciclavel.
# As categorias de CATEGORIAS_NAO_RECICLAVEIS nunca abrem, nem com "todas".
CATEGORIA_QUE_ACIONA_SERVO = "plastic"

# =======================================================================


def conectar_esp32():
    """Abre a porta serial do ESP32. Devolve None se nao conseguir."""
    if not USAR_ESP32:
        return None
    try:
        conexao = serial.Serial(PORTA_SERIAL, VELOCIDADE_SERIAL, timeout=1)
        print(f"Conectado ao ESP32 em {PORTA_SERIAL}")
        return conexao
    except serial.SerialException as erro:
        print(f"Aviso: nao foi possivel conectar ao ESP32 ({erro}). "
              f"Rodando so a deteccao, sem acionar o hardware.")
        return None


def avisar_hardware(conexao):
    """
    Manda o comando ABRIR para o ESP32.

    Fica isolada numa funcao propria para facilitar trocar o meio de
    comunicacao depois (ex: de serial para HTTP/WiFi).
    """
    if conexao is not None:
        conexao.write(b"ABRIR\n")


def melhor_deteccao(resultado, largura_frame, altura_frame):
    """
    Devolve (x1, y1, x2, y2, categoria, confianca) da melhor deteccao do
    frame, ou None se nenhuma passar nos filtros de confianca e de tamanho.
    """
    caixas = resultado.boxes
    if caixas is None or len(caixas) == 0:
        return None

    area_frame = largura_frame * altura_frame

    # Do mais confiante para o menos confiante; pega o primeiro que tambem
    # passar no filtro de tamanho.
    for idx in caixas.conf.argsort(descending=True):
        idx = int(idx)
        confianca = float(caixas.conf[idx])
        if confianca < CONFIANCA_MINIMA:
            break  # ja esta ordenado: o resto e pior ainda

        x1, y1, x2, y2 = [int(v) for v in caixas.xyxy[idx].tolist()]
        area_relativa = ((x2 - x1) * (y2 - y1)) / area_frame
        if area_relativa < AREA_MINIMA_RELATIVA or area_relativa > AREA_MAXIMA_RELATIVA:
            continue

        categoria = resultado.names[int(caixas.cls[idx])]
        return x1, y1, x2, y2, categoria, confianca

    return None


def deve_acionar_servo(categoria):
    alvo = CATEGORIA_QUE_ACIONA_SERVO.lower()
    return alvo == "todas" or categoria.lower() == alvo


def acionar_pontuacao(categoria, conexao):
    if categoria.lower() in CATEGORIAS_NAO_RECICLAVEIS:
        print(f">> '{categoria}' nao e reciclavel. Nenhum ponto.")
        return

    print(f">> Descarte correto de '{categoria}'! +10 pontos.")

    if deve_acionar_servo(categoria):
        avisar_hardware(conexao)
    else:
        print(f">> (servo nao acionado -- so reage a '{CATEGORIA_QUE_ACIONA_SERVO}')")


class ControladorDescarte:
    """
    Maquina de estados que decide QUANDO pontuar.

    - "vazio": espera um objeto novo. Observa varios frames seguidos e, ao
      completar, escolhe a categoria mais frequente entre eles (voto de
      maioria) e libera a pontuacao.
    - "objeto_presente": ja pontuou; so volta para "vazio" depois que o
      compartimento ficar sem objeto por varios frames seguidos.
    """

    def __init__(self):
        self.estado = "vazio"
        self.frames_sem_objeto = 0
        self.historico = deque(maxlen=FRAMES_PARA_CONFIRMAR_OBJETO)

    def atualizar(self, categoria):
        """
        categoria: nome detectado neste frame, ou None se nao ha objeto.
        Devolve a categoria final se deve pontuar agora; senao, None.
        """
        if categoria is None:
            self.frames_sem_objeto += 1
            self.historico.clear()  # objeto sumiu no meio da confirmacao
            if (self.estado == "objeto_presente"
                    and self.frames_sem_objeto >= FRAMES_PARA_CONFIRMAR_VAZIO):
                self.estado = "vazio"
            return None

        self.frames_sem_objeto = 0
        if self.estado != "vazio":
            return None

        self.historico.append(categoria)
        if len(self.historico) < FRAMES_PARA_CONFIRMAR_OBJETO:
            return None

        categoria_final, _ = Counter(self.historico).most_common(1)[0]
        self.historico.clear()
        self.estado = "objeto_presente"
        return categoria_final


class LeitorCamera:
    """
    Le a camera numa thread separada e guarda sempre o frame MAIS RECENTE.

    Em cameras de rede (celular), se o YOLO demora mais que a camera para
    processar cada quadro, os quadros se acumulam e a imagem fica cada vez
    mais atrasada. Aqui o programa sempre processa o quadro mais novo e
    descarta os antigos. Funciona igual para a webcam comum.
    """

    def __init__(self, fonte):
        self.captura = cv2.VideoCapture(fonte)
        self.frame = None
        self.trava = threading.Lock()
        self.rodando = self.captura.isOpened()
        self.thread = None
        if self.rodando:
            self.thread = threading.Thread(target=self._ler_continuamente, daemon=True)
            self.thread.start()

    def aberta(self):
        return self.captura.isOpened()

    def _ler_continuamente(self):
        while self.rodando:
            ok, frame = self.captura.read()
            if ok:
                with self.trava:
                    self.frame = frame
            else:
                time.sleep(0.05)  # imagem ainda nao chegou ou o fluxo caiu

    def ler(self):
        """Devolve o frame mais recente, ou None se ainda nao chegou um novo."""
        with self.trava:
            frame = self.frame
            self.frame = None  # evita processar o mesmo quadro duas vezes
        return frame

    def fechar(self):
        self.rodando = False
        if self.thread is not None:
            self.thread.join(timeout=1)
        self.captura.release()


def desenhar_deteccao(frame, deteccao):
    x1, y1, x2, y2, categoria, confianca = deteccao
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(frame, f"{categoria} ({confianca * 100:.1f}%)",
                (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)


def desenhar_status(frame, controlador, tem_objeto):
    if tem_objeto:
        if controlador.estado == "vazio":
            texto = f"Confirmando: {len(controlador.historico)}/{FRAMES_PARA_CONFIRMAR_OBJETO}"
            cv2.putText(frame, texto, (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 255, 0), 2)
        return

    if controlador.estado == "vazio":
        texto, cor = "Aguardando objeto", (0, 0, 255)
    else:
        texto, cor = "Retire o objeto anterior", (0, 165, 255)
    cv2.putText(frame, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)


def main():
    if not PESOS_MODELO.exists():
        print(f"Modelo nao encontrado em: {PESOS_MODELO}")
        print("Coloque o best.pt na pasta 'modelo' (veja o README).")
        return

    modelo = YOLO(str(PESOS_MODELO))
    conexao = conectar_esp32()

    leitor = LeitorCamera(FONTE_CAMERA)
    if not leitor.aberta():
        print(f"Nao foi possivel abrir a camera ({FONTE_CAMERA}). "
              f"Se for o celular, confira o endereco e se esta na mesma rede.")
        return
    print(f"Camera aberta: {FONTE_CAMERA}")
    print("Pressione 'q' para sair.")

    controlador = ControladorDescarte()
    ultimo_frame_em = time.time()

    while True:
        frame = leitor.ler()
        if frame is None:
            # Ainda nao chegou um quadro novo: espera um pouco e tenta de novo
            if time.time() - ultimo_frame_em > SEGUNDOS_SEM_IMAGEM_PARA_DESISTIR:
                print("Sem imagem da camera. Encerrando.")
                break
            time.sleep(0.01)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue
        ultimo_frame_em = time.time()

        resultados = modelo.predict(frame, conf=CONFIANCA_MINIMA, iou=IOU_MINIMO, verbose=False)
        altura, largura = frame.shape[:2]
        deteccao = melhor_deteccao(resultados[0], largura, altura)

        categoria_final = controlador.atualizar(deteccao[4] if deteccao else None)
        if categoria_final is not None:
            acionar_pontuacao(categoria_final, conexao)

        if deteccao:
            desenhar_deteccao(frame, deteccao)
        desenhar_status(frame, controlador, tem_objeto=deteccao is not None)

        cv2.imshow("Deteccao YOLO - lixo reciclavel", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    leitor.fechar()
    if conexao is not None:
        conexao.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
