/*
  ESP32 - MODO TESTE (SO LED, SEM SERVO)

  Use este sketch quando o servo ainda NAO esta ligado no ESP32.

  O que faz:
  - Fica esperando comandos de texto pelo cabo USB (porta serial)
  - Quando recebe uma linha que comeca com "ABRIR", acende o LED azul
    embutido na placa por 1,5 segundo e responde "OK: compartimento acionado"

  Nao precisa de nenhuma biblioteca extra, nem de nada ligado na placa.

  Como gravar (Arduino IDE):
  - Ferramentas > Placa > ESP32 Arduino > ESP32 Dev Module
  - Ferramentas > Porta > a COM do seu ESP32 (ex: COM4)
  - Clique em Upload (se travar em "Connecting...", segure o botao BOOT)
  - Depois de gravar, FECHE o Monitor Serial para o Python poder usar a porta

  Observacao: o Arduino IDE exige que este arquivo .ino fique dentro de uma
  pasta com o mesmo nome (esp32_teste_led). Mantenha assim.
*/

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
  Serial.println("ESP32 (teste LED) pronto, aguardando comandos...");
}

void loop() {
  while (Serial.available() > 0) {
    char caractere = Serial.read();

    if (caractere == '\n') {
      bufferEntrada.trim();

      if (bufferEntrada.startsWith("ABRIR")) {
        acionarTeste();
        Serial.println("OK: compartimento acionado");
      }

      bufferEntrada = "";
    } else {
      bufferEntrada += caractere;
    }
  }
}
