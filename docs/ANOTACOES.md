# Anotações — Lixeira Inteligente (YOLO + ESP32)

Notas para relembrar o que cada arquivo faz, como montar e o que fazer quando algo dá errado. Os comandos assumem que você está na **raiz do repositório** com o `(venv)` ativado.

## Visão geral

1. A **câmera** (webcam do notebook ou celular) fornece o vídeo.
2. O `python/detectar_lixo_yolo.py` roda o YOLO (`modelo/best.pt`), acha o objeto, diz a categoria e decide se pontua.
3. Se a categoria for a escolhida (`CATEGORIA_QUE_ACIONA_SERVO`), o Python manda o texto `ABRIR` ao **ESP32**.
4. O ESP32 aciona o LED (modo teste) ou o servo + LED (modo final).

O ESP32 não tem câmera nem inteligência: só obedece. Por isso o **Python é o mesmo** em todos os modos; o que muda é qual sketch está gravado no ESP32.

---

## `esp32/` — sketches do Arduino IDE

Cada `.ino` precisa ficar dentro de uma pasta com o mesmo nome. Para trocar de modo, grave outro sketch; não precisa mexer no Python.

| Sketch | Comunicação | Hardware | Biblioteca |
|---|---|---|---|
| `esp32_teste_led` | cabo USB | só o LED da placa | nenhuma |
| `esp32_com_servo` | cabo USB | servo + LED | ESP32Servo |
| `esp32_bluetooth_teste_led` | Bluetooth | só o LED da placa | nenhuma |
| `esp32_bluetooth_com_servo` | Bluetooth | servo + LED | ESP32Servo |

Todos esperam uma linha começando com `ABRIR` e respondem `OK: compartimento acionado`.

**Gravar:** Ferramentas → Placa → *ESP32 Dev Module* → Porta → sua COM → Upload. Se travar em "Connecting...", segure o botão **BOOT**. Depois feche o Monitor Serial.

**Servo SG90:**
- marrom/preto → `GND`
- vermelho → `VIN` (5 V; não use o `3V3`)
- laranja/amarelo → `GPIO 13` (se trocar, mude `PINO_SERVO` no sketch)
- Se o ESP32 reiniciar ao mexer o servo: falta corrente. Use cabo/carregador melhor ou fonte externa de 5 V com o GND em comum.

**Alimentação:** carregador de celular comum (5 V, 1 A ou mais) ou power bank, ligado na porta USB da placa. Não ligue tensão diferente de 5 V nos pinos.

---

## `python/`

### `detectar_lixo_yolo.py` — programa principal
Abre a câmera, roda o YOLO, desenha caixa e categoria e pontua com:
- **voto de maioria** entre `FRAMES_PARA_CONFIRMAR_OBJETO` (10) quadros;
- **anti-fraude:** só pontua de novo depois de `FRAMES_PARA_CONFIRMAR_VAZIO` (15) quadros sem objeto;
- filtros contra falso positivo: `CONFIANCA_MINIMA` (0.65) e tamanho da caixa entre 3% e 65% do quadro.

Se o ESP32 não for encontrado, avisa e continua só com a detecção. Tecla `q` sai.
Configurações no topo: `FONTE_CAMERA`, `USAR_ESP32`, `PORTA_SERIAL`, `CATEGORIA_QUE_ACIONA_SERVO`, `CATEGORIAS_NAO_RECICLAVEIS`.

### `testar_serial.py` — testa o ESP32 sem câmera
`python python/testar_serial.py` (ou `... COM7`). Digite `abrir`: o LED acende e aparece a resposta do ESP32. Serve para descobrir se o problema é de comunicação ou de detecção.

### `treinar_yolo.py` — treina do zero
Usa o dataset em `dataset/` (veja o README). Até 100 épocas, para sozinho se não melhorar por 20. Usa GPU se houver. Mostra no fim onde salvou o `best.pt`; copie para `modelo/best.pt`.

### `retomar_treino.py` — continua um treino interrompido
Acha sozinho o `last.pt` mais recente em `runs/` e continua de onde parou. Use este (e não o `treinar_yolo.py`) para não criar pastas novas.

### `combinar_datasets.py` + `continuar_treino_novo_dataset.py` — melhorar o modelo
1. Coloque o dataset atual em `dataset_atual/` e o novo em `dataset_novo/`.
2. `python python/combinar_datasets.py` junta os dois (unindo as categorias) em `dataset_combinado/`.
3. `python python/continuar_treino_novo_dataset.py` continua a partir do `modelo/best.pt`.

Treinar só com o dataset novo faz o modelo "esquecer" parte do antigo; por isso o ideal é treinar com os dois juntos. O que mais melhora o resultado real é incluir **fotos da sua própria câmera, no ambiente da lixeira**.

---

## Versão sem fio: câmera do celular + ESP32 por Bluetooth

- **Celular:** só filma (app *IP Webcam*, Android). Mostra um endereço tipo `http://192.168.x.x:8080`; confira abrindo no navegador do notebook.
- **Rede:** celular e notebook na mesma WiFi (ou no hotspot de um celular). Redes de faculdade costumam bloquear a comunicação entre aparelhos.
- **ESP32:** grave um sketch Bluetooth, ligue num power bank e pareie no Windows (`Lixeira-ESP32`). Em *Mais opções de Bluetooth → Portas COM*, anote a porta de tipo **Saída**.
- **No Python:** `FONTE_CAMERA = "http://IP:8080/video"` e `PORTA_SERIAL = "COM?"` (a do Bluetooth).
- Ligue e pareie o ESP32 **antes** de rodar o Python; se ele reiniciar, feche e rode de novo.

**Teste em etapas:** (1) só a câmera, com `USAR_ESP32 = False`; (2) só o ESP32, com `testar_serial.py`; (3) tudo junto.

O notebook continua sendo o cérebro: só a câmera e o ESP32 ficam sem fio. Para a lixeira rodar sem notebook seria preciso um computador pequeno dentro dela (ex.: Raspberry Pi).

---

## Erros comuns

| Erro | O que fazer |
|---|---|
| `could not open port 'COM3'` | COM errada ou ESP32 desligado. Veja a COM no Gerenciador de Dispositivos (ou em Ferramentas → Porta) e ajuste `PORTA_SERIAL`. |
| Porta ocupada / "Acesso negado" | Só um programa usa a COM por vez. Feche o Monitor Serial e o Python que estiver rodando. Para gravar o ESP32, feche o Python antes. |
| `No module named 'serial'` | `pip install pyserial` (não `pip install serial`). |
| Câmera do celular não abre / "Stream timeout" | Confira o endereço no navegador, se estão na mesma rede, e se o app está aberto com o servidor iniciado. |
| Detecta mão/fundo como lixo | O dataset público difere do seu ambiente. Suba `CONFIANCA_MINIMA` e treine com fotos da sua câmera. |
| `Sketch too big` (Bluetooth) | Ferramentas → Partition Scheme → *Huge APP*. |
| Arduino: `exit status 1` | Ative "Show verbose output during compilation" em Preferências e procure a primeira linha com `error:`. Confira a placa e a biblioteca ESP32Servo. |
| Upload trava em "Connecting..." | Segure o botão **BOOT** durante a gravação. |
| VS Code: "content of the file is newer" | **Não** clique em Overwrite. Use Arquivo → Reverter Arquivo e refaça a edição. |
| Treino muito lento | Sem GPU NVIDIA leva horas por época. Instale o PyTorch com CUDA (veja o README) ou use o Google Colab. |
| `CUDA out of memory` | Reduza `BATCH` no `treinar_yolo.py` (8 → 4). |

---

## Possível evolução (WiFi)

Para tirar o cabo/Bluetooth, só a função `avisar_hardware()` do `detectar_lixo_yolo.py` muda (de `serial.write` para uma requisição HTTP), e o ESP32 passa a ter um servidor web pequeno em vez de ler a serial. O resto do código continua igual.
