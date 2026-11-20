"""
Testa a comunicacao serial com o ESP32, sem camera e sem deteccao.

Serve para descobrir se um problema e de comunicacao (cabo, porta COM,
sketch gravado) ou de deteccao. Digite 'abrir' + Enter: o ESP32 aciona o
LED (modo teste) ou o servo, e responde "OK: compartimento acionado".

Como usar (a partir da raiz do repositorio):
    python python/testar_serial.py          (usa a porta abaixo)
    python python/testar_serial.py COM7     (ou informe a porta)

Feche o Monitor Serial do Arduino IDE antes: so um programa usa a porta por vez.
"""

import sys
import time

import serial

PORTA_SERIAL = "COM4"  # troque se o seu ESP32 aparecer em outra porta
VELOCIDADE_SERIAL = 115200


def main():
    porta = sys.argv[1] if len(sys.argv) > 1 else PORTA_SERIAL

    print(f"Conectando em {porta}...")
    try:
        conexao = serial.Serial(porta, VELOCIDADE_SERIAL, timeout=1)
    except serial.SerialException as erro:
        print(f"Nao foi possivel abrir a porta ({erro}).")
        print("Confira a COM no Gerenciador de Dispositivos e feche o Monitor Serial do Arduino IDE.")
        return

    time.sleep(2)  # o ESP32 costuma reiniciar ao abrir a porta
    print("Conectado. Digite 'abrir' e Enter para testar. 'sair' encerra.")

    while True:
        comando = input("> ").strip().lower()

        if comando == "sair":
            break

        if comando == "abrir":
            conexao.write(b"ABRIR\n")
            time.sleep(0.5)
            # Mostra qualquer resposta que o ESP32 tenha mandado de volta
            while conexao.in_waiting:
                print("ESP32 respondeu:", conexao.readline().decode(errors="ignore").strip())

    conexao.close()


if __name__ == "__main__":
    main()
