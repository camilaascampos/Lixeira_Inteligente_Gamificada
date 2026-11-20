# Lixeira Inteligente Gamificada

Lixeira que reconhece lixo reciclável por câmera (YOLOv8) e dá pontos a quem descarta corretamente. Ao detectar a categoria certa, o computador manda um comando para um **ESP32**, que aciona um servo motor (ou, nos testes, o LED da placa).

Projeto da disciplina de Sistemas Digitais.

## Como funciona

```
Câmera (webcam ou celular)
        │  vídeo
        ▼
Notebook ── YOLOv8 ── voto de maioria ── regra de pontuação
        │
        │  texto "ABRIR" (cabo USB ou Bluetooth)
        ▼
ESP32 ── servo motor (abre o compartimento) + LED
```

- O **YOLO** localiza o objeto e diz a categoria: `can`, `glass`, `paper`, `plastic` ou `trash` (esta última não pontua).
- **Voto de maioria:** só decide depois de observar vários quadros seguidos, para um quadro ruim não errar a pontuação.
- **Anti-fraude:** depois de pontuar, o compartimento precisa ficar vazio antes de aceitar outro objeto. Deixar o mesmo item parado não dá pontos de novo.
- O **ESP32** não roda o modelo: ele só obedece ao comando. Por isso o mesmo código Python serve para o modo teste (LED) e para o modo final (servo).

## Estrutura do repositório

```
├── modelo/
│   └── best.pt                  modelo YOLO já treinado
├── python/
│   ├── detectar_lixo_yolo.py    programa principal (câmera + YOLO + ESP32)
│   ├── testar_serial.py         testa o ESP32 sem câmera
│   ├── treinar_yolo.py          treina o modelo com um dataset
│   ├── retomar_treino.py        continua um treino interrompido
│   ├── combinar_datasets.py     junta dois datasets em um
│   └── continuar_treino_novo_dataset.py   melhora o modelo atual com dados novos
├── esp32/                       sketches do Arduino IDE
│   ├── esp32_teste_led/             cabo USB, só LED (sem servo)
│   ├── esp32_com_servo/             cabo USB, servo + LED
│   ├── esp32_bluetooth_teste_led/   Bluetooth, só LED
│   └── esp32_bluetooth_com_servo/   Bluetooth, servo + LED
├── docs/
│   └── ANOTACOES.md             notas detalhadas, montagem e erros comuns
├── requirements.txt
└── README.md
```

## Instalação

Requisitos: Python 3.10 a 3.12 e, para o ESP32, o Arduino IDE.

```bash
git clone https://github.com/camilaascampos/Lixeira_Inteligente_Gamificada.git
cd Lixeira_Inteligente_Gamificada

python -m venv venv
venv\Scripts\activate            # Windows  (Mac/Linux: source venv/bin/activate)
```

**PyTorch primeiro** (no Windows, o `pip install torch` padrão instala a versão *sem* GPU):

```bash
# Com placa de vídeo NVIDIA (muito mais rápido para treinar):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
# Sem GPU:
pip install torch torchvision
```

Depois o restante:

```bash
pip install -r requirements.txt
```

## Rodar a detecção

O `modelo/best.pt` já vem no repositório, então **não é preciso treinar nada**.

```bash
python python/detectar_lixo_yolo.py
```

Tecla `q` fecha a janela. As configurações ficam no topo do arquivo, na seção `CONFIGURACOES`:

| Variável | Para que serve |
|---|---|
| `FONTE_CAMERA` | `0` = webcam do notebook; ou o endereço do celular, ex.: `"http://192.168.0.10:8080/video"` (app *IP Webcam*) |
| `USAR_ESP32` | `False` testa só a detecção, sem hardware |
| `PORTA_SERIAL` | porta COM do ESP32 (cabo ou Bluetooth) |
| `CATEGORIA_QUE_ACIONA_SERVO` | `"plastic"`, `"glass"`, `"can"`, `"paper"` ou `"todas"` |
| `CONFIANCA_MINIMA` | sobe para reduzir falsos positivos (mão, fundo) |

## ESP32

1. Abra um dos sketches da pasta `esp32/` no Arduino IDE (cada `.ino` precisa ficar dentro da pasta de mesmo nome).
2. Placa: **ESP32 Dev Module**. Se der "Sketch too big" nos sketches Bluetooth: *Partition Scheme → Huge APP*.
3. Os sketches `com_servo` precisam da biblioteca **ESP32Servo**.
4. Feche o Monitor Serial e ajuste `PORTA_SERIAL` no `detectar_lixo_yolo.py`.

Ligação do servo SG90: marrom/preto → `GND`, vermelho → `VIN` (5 V), laranja/amarelo → `GPIO 13`.

Para testar o ESP32 sem câmera: `python python/testar_serial.py` e digitar `abrir`.

O Bluetooth funciona só no ESP32 clássico (não nos modelos S2, S3 e C3). Detalhes, montagem sem fio e solução de problemas em [`docs/ANOTACOES.md`](docs/ANOTACOES.md).

## Treinar com outro dataset

O dataset **não** está no repositório (é grande). O modelo atual foi treinado com este, do Roboflow Universe (licença CC BY 4.0):
[project-g6oev/trash-s8fg7, versão 5](https://universe.roboflow.com/project-g6oev/trash-s8fg7/dataset/5) — classes `can`, `glass`, `paper`, `plastic`, `trash`.

1. Baixe no formato **YOLOv8** (não o "Oriented Bounding Boxes") e extraia dentro de `dataset/`, de modo que exista `dataset/data.yaml`.
2. No `data.yaml`, os caminhos `train:`, `val:` e `test:` devem ser `train/images`, `valid/images` e `test/images` (sem `../`).
3. `python python/treinar_yolo.py`
4. Ao terminar, ele mostra onde salvou o `best.pt`. Copie para `modelo/best.pt`.

Se o treino for interrompido: `python python/retomar_treino.py`.
Para melhorar o modelo com dados novos: `python python/combinar_datasets.py` e depois `python python/continuar_treino_novo_dataset.py`.

Treinar sem placa de vídeo NVIDIA leva horas por época. Use uma GPU, ou o Google Colab.

## Licença

Veja o arquivo `LICENSE`.
