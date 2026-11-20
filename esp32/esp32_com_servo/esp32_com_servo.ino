/*
  ESP32 - MODO FINAL (COM SERVO MOTOR)

  Use este sketch quando o servo JA estiver ligado no ESP32.

  O que faz:
  - Fica esperando comandos de texto pelo cabo USB (porta serial)
  - Quando recebe uma linha que comeca com "ABRIR", move o servo para
    "abrir" o compartimento por 1,5 segundo, depois volta para "fechado".
    O LED azul da placa acende junto, como sinal visual.
  - Responde "OK: compartimento acionado" pela serial

  Ligacao do servo SG90 (3 fios):
  - Fio marrom/preto    -> GND do ESP32
  - Fio vermelho        -> 5V (pino VIN) do ESP32
  - Fio laranja/amarelo -> GPIO 13 (sinal; troque PINO_SERVO se usar outro)
  Se o servo tremer ou o ESP32 reiniciar ao mexer, falta corrente pelo USB:
  alimente o servo com fonte externa de 5V, ligando o GND dela tambem no
  GND do ESP32.

  Biblioteca necessaria (Ferramentas > Gerenciar Bibliotecas):
  - ESP32Servo (autor: Kevin Harrington)

  Como gravar (Arduino IDE):
  - Ferramentas > Placa > ESP32 Arduino > ESP32 Dev Module
  - Ferramentas > Porta > a COM do seu ESP32 (ex: COM4)
  - Clique em Upload (se travar em "Connecting...", segure o botao BOOT)
  - Depois de gravar, FECHE o Monitor Serial para o Python poder usar a porta

  Observacao: o Arduino IDE exige que este arquivo .ino fique dentro de uma
  pasta com o mesmo nome (esp32_com_servo). Mantenha assim.
*/

#include <ESP32Servo.h>

const int PINO_SERVO = 13;
const int PINO_LED = 2;       // LED azul embutido
const int ANGULO_FECHADO = 0;  // ajuste conforme a montagem fisica
const int ANGULO_ABERTO = 90;  // ajuste conforme a montagem fisica

Servo servoCompartimento;
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

  Serial.println("ESP32 (com servo) pronto, aguardando comandos...");
}

void loop() {
  while (Serial.available() > 0) {
    char caractere = Serial.read();

    if (caractere == '\n') {
      bufferEntrada.trim();

      if (bufferEntrada.startsWith("ABRIR")) {
        abrirCompartimento();
        Serial.println("OK: compartimento acionado");
      }

      bufferEntrada = "";
    } else {
      bufferEntrada += caractere;
    }
  }
}
