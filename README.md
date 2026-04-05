# GammaPro - Processamento de Dados de Gamaespectrometria

[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Aplicação desktop moderna para processamento, análise e exportação de dados gammetricos.

## ✨ Funcionalidades

- 📂 **Carregar arquivos** - Suporte a arquivos .XYZ de dados gammetricos
- 📊 **Visualização de dados** - Tabela de dados, atributos e mapa espacial interativo
- 📈 **Análise Exploratória** - Histograma, boxplot, estatísticas e distribuição espacial
- ✂️ **Corte de Outliers** - Três métodos:
  - Corte por porcentagem automática
  - Limites manuais (inferior/superior) para cada variável
  - Reset dos dados originais
- 💾 **Exportação** - Múltiplos formatos:
  - CSV
  - Excel (.xlsx)
  - GeoTIFF (grids interpolados)
- 🎨 **Visualização** - Paleta de cores Turbo (valores baixos = azul/frio, altos = vermelho/quente)

## 📋 Requisitos

```
pandas>=1.5.0
numpy>=1.23.0
matplotlib>=3.6.0
seaborn>=0.12.0
scipy>=1.9.0
pyproj>=3.4.0
rasterio>=1.3.0
customtkinter>=5.1.0
Pillow>=9.3.0
openpyxl>=3.0.0
```

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/gamma-pro.git
cd gamma-pro
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## ▶️ Executar

```bash
python gammapro.py
```

## 📁 Estrutura do Projeto

```
gamma-pro/
├── gammapro.py       # Aplicação principal
├── requirements.txt  # Dependências
├── README.md         # Este arquivo
└── iniciar.bat       # Script para Windows
```

## 📊 Interface

A aplicação possui interface gráfica moderna com:
- Sidebar para navegação
- Abas para diferentes funcionalidades
- Visualização interativa de dados
- Opções de exportação flexíveis

## 📝 Licença

MIT License

## Autor

Cesar Terra