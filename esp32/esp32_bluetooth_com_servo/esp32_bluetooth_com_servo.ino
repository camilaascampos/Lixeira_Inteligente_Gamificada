/*
  ESP32 - BLUETOOTH - MODO FINAL (COM SERVO MOTOR)

  Igual ao esp32_com_servo, mas recebe o comando por BLUETOOTH em vez do
  cabo USB. Use quando o servo ja estiver ligado e a lixeira for portatil.

  O que faz:
  - Cria um dispositivo Bluetooth chamado "Lixeira-ESP32"
  - Quando recebe uma linha que comeca com "ABRIR", move o servo para
    "abrir" por 1,5 segundo e volta para "fechado". O LED acende junto.
  - Responde "OK: compartimento acionado" por Bluetooth

  Ligacao do servo SG90 (3 fios):
  - Fio marrom/preto    -> GND do ESP32
  - Fio vermelho        -> 5V (pino VIN) do ESP32
  - Fio laranja/amarelo -> GPIO 13 (sinal; troque PINO_SERVO se usar outro)
  Com power bank, o servo costuma funcionar bem; se o ESP32 reiniciar ao
  mexer o servo, use uma fonte de 5V mais forte (GND em comum).

  Biblioteca necessaria (Ferramentas > Gerenciar Bibliotecas):
  - ESP32Servo (autor: Kevin Harrington)

  IMPORTANTE:
  - Funciona so no ESP32 "classico". Os modelos S2, S3 e C3 NAO tem esse
    tipo de Bluetooth.
  - Se der erro "Sketch too big": Ferramentas > Partition Scheme >
    "Huge APP (3MB No OTA/1MB SPIFFS)".

  Como gravar e como parear no Windows: veja o cabecalho do arquivo
  esp32_bluetooth_teste_led.ino (os passos sao os mesmos).

  Observacao: o .ino precisa ficar dentro de uma pasta com o mesmo nome
  (esp32_bluetooth_com_servo).
*/

#include "BluetoothSerial.h"
#include <ESP32Servo.h>

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error "Bluetooth nao esta habilitado nesta placa. Use um ESP32 classico (Dev Module)."
#endif

BluetoothSerial SerialBT;
Servo servoCompartimento;

const int PINO_SERVO = 13;
const int PINO_LED = 2;        // LED azul embutido
const int ANGULO_FECHADO = 0;   // ajuste conforme a montagem fisica
const int ANGULO_ABERTO = 90;   // ajuste conforme a montagem fisica

String bufferEntrada = "";

void abrirCompartimento() {
  digitalWrite(PINO_LED, HIGH);
  servoCompartimento.write(ANGULO_ABERTO);
  delay(1500);
  servoCompartimento.write(ANGULO_FECHADO);
  digitalWrite(PINO_LED, LOW);
}

void setup() {
  Serial.begin(115200);
  pinMode(PINO_LED, OUTPUT);
  digitalWrite(PINO_LED, LOW);

  servoCompartimento.attach(PINO_SERVO);
  servoCompartimento.write(ANGULO_FECHADO);

  SerialBT.begin("Lixeira-ESP32");
  Serial.println("ESP32 Bluetooth (com servo) pronto. Procure por 'Lixeira-ESP32'.");
}

void loop() {
  while (SerialBT.available() > 0) {
    char caractere = SerialBT.read();

    if (caractere == '\n') {
      bufferEntrada.trim();

      if (bufferEntrada.startsWith("ABRIR")) {
        Serial.println("Comando ABRIR recebido por Bluetooth");
        abrirCompartimento();
        SerialBT.println("OK: compartimento acionado");
      }

      bufferEntrada = "";
    } else {
      bufferEntrada += caractere;
    }
  }
}
