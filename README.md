# Lixeira Inteligente — Detecção de Lixo Reciclável (YOLOv8)

Sistema de detecção automática de lixo reciclável via câmera, feito com YOLOv8.

---

## Opção 1 — Só quero rodar a detecção (usar o modelo já treinado)

Você **não precisa do dataset** para isso, só do modelo já treinado.

### O que você precisa ter
- Python 3.10, 3.11 ou 3.12 instalado (**não** use 3.13, o TensorFlow/algumas libs ainda não suportam bem)
- Nada além disso — o modelo treinado (`best.pt`) já vem junto no repositório

### Passo a passo
```
# 1. Clone o repositório
git clone [LINK DO REPOSITORIO]
cd [nome-da-pasta]

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (Mac/Linux)

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Instale o PyTorch
# Sem GPU dedicada (mais lento, mas funciona):
pip install torch torchvision

# Com GPU NVIDIA (bem mais rápido — confira sua versão de CUDA com "nvidia-smi"):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

E rode direto:
```
python detectar_lixo_yolo.py
```

---

## Opção 2 — Quero treinar com outro dataset

### O que você precisa
- Um dataset anotado com bounding box, no formato **YOLOv8** (não "Oriented Bounding Boxes"), exportado do [Roboflow Universe](https://universe.roboflow.com) ou similar
- As mesmas dependências da Opção 1, instaladas

### Passo a passo
1. Extraia o dataset baixado dentro da pasta do projeto. Deve conter as pastas `train/`, `valid/`, `test/` e um arquivo `data.yaml`
2. Abra o `data.yaml` e confirme que os caminhos (`train:`, `val:`, `test:`) apontam certo para as pastas — ajuste removendo ou adicionando `../` se necessário, dependendo de onde o `data.yaml` ficou
3. No `treinar_yolo.py`, ajuste a variável `DATA_YAML` para o caminho do seu `data.yaml`
4. Rode:
   ```
   python treinar_yolo.py
   ```
5. Se precisar pausar (Ctrl+C) e continuar depois, use:
   ```
   python retomar_treino.py
   ```
   (ajuste o caminho `CHECKPOINT` dentro dele para a pasta que o treino criou, algo como `runs/detect/runs_lixeira/deteccao_lixoX/weights/last.pt`)
6. Ao final, os pesos treinados ficam em `runs/detect/runs_lixeira/.../weights/best.pt` — aponte o `PESOS_MODELO` do `detectar_lixo_yolo.py` para esse caminho e rode normalmente

### Categorias que não pontuam
No `detectar_lixo_yolo.py`, ajuste a lista `CATEGORIAS_NAO_RECICLAVEIS` para bater com os nomes de classe (`names:`) do seu novo `data.yaml`.

---

## Arquivos do projeto

| Arquivo | Para que serve |
|---|---|
| `detectar_lixo_yolo.py` | Roda a detecção em tempo real pela webcam |
| `treinar_yolo.py` | Treina o modelo do zero com um dataset |
| `retomar_treino.py` | Continua um treino pausado, sem perder progresso |
| `requirements.txt` | Lista de bibliotecas Python necessárias |
