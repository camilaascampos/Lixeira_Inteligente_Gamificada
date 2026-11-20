/*
  ESP32 - BLUETOOTH - MODO TESTE (SO LED, SEM SERVO)

  Igual ao esp32_teste_led, mas recebe o comando por BLUETOOTH em vez do
  cabo USB. Assim o ESP32 pode ficar na lixeira alimentado por um power
  bank, sem cabo no notebook.

  O que faz:
  - Cria um dispositivo Bluetooth chamado "Lixeira-ESP32"
  - Quando recebe uma linha que comeca com "ABRIR", acende o LED azul da
    placa por 1,5 segundo e responde "OK: compartimento acionado"
  - A porta USB continua imprimindo mensagens de depuracao (Monitor Serial)

  IMPORTANTE:
  - Funciona so no ESP32 "classico" (ESP32-WROOM / ESP32 Dev Module).
    Os modelos S2, S3 e C3 NAO tem esse tipo de Bluetooth.
  - Se der erro "Sketch too big" ao compilar: Ferramentas > Partition Scheme >
    "Huge APP (3MB No OTA/1MB SPIFFS)".

  Como gravar (Arduino IDE):
  - Ferramentas > Placa > ESP32 Arduino > ESP32 Dev Module
  - Ferramentas > Porta > a COM do cabo USB (so para gravar)
  - Upload (se travar em "Connecting...", segure o botao BOOT)

  Como usar no Windows:
  1. Ligue o ESP32 (cabo ou power bank)
  2. Configuracoes > Bluetooth e dispositivos > Adicionar dispositivo >
     Bluetooth > "Lixeira-ESP32" (se pedir PIN, tente 1234 ou 0000)
  3. Ainda nas configuracoes, abra "Mais opcoes de Bluetooth" > aba
     "Portas COM" e anote a porta de tipo "Saida" (ex: COM7)
  4. Coloque essa COM em PORTA_SERIAL no detectar_lixo_yolo.py

  Observacao: o .ino precisa ficar dentro de uma pasta com o mesmo nome
  (esp32_bluetooth_teste_led).
*/

#include "BluetoothSerial.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error "Bluetooth nao esta habilitado nesta placa. Use um ESP32 classico (Dev Module)."
#endif

BluetoothSerial SerialBT;

const int PINO_LED = 2;  // LED azul embutido na maioria das placas ESP32 Dev Module
String bufferEntrada = "";

void acionarTeste() {
  digitalWrite(PINO_LED, HIGH);
  delay(1500);
  digitalWrite(PINO_LED, LOW);
}

void setup() {
  Serial.begin(115200);
  pinMode(PINO_LED, OUTPUT);
  digitalWrite(PINO_LED, LOW);

  SerialBT.begin("Lixeira-ESP32");
  Serial.println("ESP32 Bluetooth (teste LED) pronto. Procure por 'Lixeira-ESP32'.");
}

void loop() {
  while (SerialBT.available() > 0) {
    char caractere = SerialBT.read();

    if (caractere == '\n') {
      bufferEntrada.trim();

      if (bufferEntrada.startsWith("ABRIR")) {
        Serial.println("Comando ABRIR recebido por Bluetooth");
        acionarTeste();
        SerialBT.println("OK: compartimento acionado");
      }

      bufferEntrada = "";
    } else {
      bufferEntrada += caractere;
    }
  }
}
