# ArchiDive — Guia Completo de Uso
### Versão 1.0 | Conversor de Planta Baixa DXF para Ambiente 3D / VR

---

## 📖 O que é o ArchiDive?

**ArchiDive** é um software profissional que lê arquivos de planta baixa no formato **.DXF** (o formato padrão de projetos CAD — AutoCAD, LibreCAD, QCAD, etc.) e converte automaticamente os polígonos da planta em um **ambiente tridimensional completo** com paredes, piso e teto, visualizável em tempo real com iluminação 3D.

O modelo gerado pode ser exportado em dois formatos universais:
- **OBJ** — compatível com praticamente qualquer software 3D (Blender, 3ds Max, Maya, etc.)
- **glTF 2.0** — o formato padrão para VR/AR (Unity, Unreal Engine, A-Frame, Mozilla Hubs, Blender)

---

## ⚙️ Instalação

### Pré-requisitos
- **Python 3.8 ou superior** — [python.org](https://www.python.org/downloads/)
- Sistema operacional: Windows 10+, macOS 10.14+, Linux (Ubuntu 20.04+)

### Passo 1 — Baixar o projeto
Descompacte o arquivo `ArchiDive.zip` em uma pasta de sua escolha, por exemplo:
```
C:\ArchiDive\      (Windows)
~/ArchiDive/       (macOS / Linux)
```

### Passo 2 — Criar ambiente virtual (recomendado)
Abra o terminal (Prompt de Comando, PowerShell ou Terminal) dentro da pasta do projeto:

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (macOS / Linux)
source venv/bin/activate
```

### Passo 3 — Instalar dependências
```bash
pip install -r requirements.txt
```

> ⏳ Aguarde o download das bibliotecas. Isso pode levar alguns minutos na primeira vez.

### Passo 4 — Executar o ArchiDive
```bash
python main.py
```

A janela principal do ArchiDive será aberta.

---

## 🖥️ Interface do Usuário

A janela é dividida em **duas áreas principais**:

```
┌─────────────────────┬──────────────────────────────────┐
│   PAINEL LATERAL    │                                  │
│                     │       VISUALIZADOR 3D            │
│  • Arquivo DXF      │                                  │
│  • Parâmetros       │   (rotação, zoom, pan)           │
│  • Camadas          │                                  │
│  • Ações            │                                  │
│  • Estatísticas     │                                  │
└─────────────────────┴──────────────────────────────────┘
```

### Painel Lateral (esquerda)
| Seção | Descrição |
|-------|-----------|
| **Arquivo DXF** | Abre o arquivo de planta baixa |
| **Parâmetros** | Configura a altura das paredes |
| **Camadas** | Liga/desliga piso, teto, contornos, grade |
| **Ações** | Gera o 3D, exporta, limpa a cena |
| **Estatísticas** | Mostra polígonos, paredes e áreas calculadas |

### Toolbar de Câmera (topo direito)
Alterna rapidamente entre as vistas: **Perspectiva**, **Superior** e **Frontal**.

---

## 🚀 Fluxo de Uso — Passo a Passo

### PASSO 1 — Abrir um arquivo DXF

1. Clique no botão **"Abrir DXF"** no painel lateral
   *ou use o menu* `Arquivo → Abrir DXF…` *(Ctrl+O)*
2. Navegue até o arquivo `.dxf` da sua planta baixa
3. Clique em **Abrir**
4. O nome do arquivo aparecerá em destaque no painel lateral
5. A barra de status confirma o carregamento e detecta automaticamente a unidade do arquivo (mm, cm, metros, etc.)

> ✅ **Formatos aceitos:** arquivos `.dxf` de qualquer versão (AutoCAD R12 até 2024, LibreCAD, QCAD, etc.)

### PASSO 2 — Ajustar parâmetros

**Altura das paredes:**
- O campo padrão é **2,5 metros** (pé-direito residencial padrão)
- Altere conforme necessário (ex: 3.0 m para áreas comerciais, 2.7 m para residências premium)
- Você pode usar casas decimais (ex: `2.80`)

**Camadas visíveis:**
- ☑ **Exibir Piso** — gera o plano do piso baseado no contorno convexo da planta
- ☑ **Exibir Teto** — gera o plano do teto na altura configurada
- ☑ **Exibir Contornos** — realça as arestas das paredes em azul ciano
- ☑ **Exibir Grade** — mostra a grade de referência no plano Z=0

### PASSO 3 — Gerar o Ambiente 3D

1. Clique em **"Gerar Ambiente 3D"**
2. A barra de progresso indicará as etapas:
   - **20%** — Leitura das entidades DXF
   - **60%** — Extração de polígonos fechados
   - **80%** — Geração das geometrias 3D
   - **100%** — Concluído
3. O modelo 3D aparece instantaneamente no visualizador
4. As **Estatísticas** são calculadas e exibidas:
   - Número de polígonos extraídos
   - Número de paredes geradas
   - Área total de paredes (m²)
   - Área do piso (m²)

> ⚠️ **Importante:** O ArchiDive processa apenas entidades do tipo **LWPOLYLINE** e **POLYLINE fechadas** com 3 ou mais vértices. Linhas (`LINE`) soltas são ignoradas. Verifique se sua planta foi desenhada com polilínhas.

### PASSO 4 — Navegar no Visualizador 3D

| Ação | Controle |
|------|----------|
| **Rotacionar** | Clique esquerdo + arrastar |
| **Pan (mover câmera)** | Clique direito + arrastar |
| **Zoom** | Scroll do mouse |
| **Vista Perspectiva** | Botão "Perspectiva" na toolbar |
| **Vista Superior** | Botão "Superior" na toolbar |
| **Vista Frontal** | Botão "Frontal" na toolbar |

### PASSO 5 — Exportar o Modelo

#### Exportar como OBJ (para Blender, 3ds Max, Maya, etc.)
1. Clique no botão **"OBJ"** no painel lateral
   *ou use* `Arquivo → Exportar OBJ…` *(Ctrl+E)*
2. Escolha o local e nome do arquivo
3. Dois arquivos são gerados:
   - `nome.obj` — geometria das malhas
   - `nome.mtl` — definições de material (paredes cinza, piso bege, teto branco)

#### Exportar como glTF (para VR/AR — Unity, Unreal, A-Frame)
1. Clique no botão **"glTF"** no painel lateral
   *ou use* `Arquivo → Exportar glTF…`
2. Escolha o local e nome do arquivo
3. Dois arquivos são gerados:
   - `nome.gltf` — descrição JSON da cena
   - `nome.bin` — dados binários de vértices e índices

> 🥽 **Para VR:** O formato glTF é diretamente compatível com **A-Frame** (WebVR), **Mozilla Hubs**, **Unity** (via plugin glTF Tools), **Unreal Engine** (via Interchange), e qualquer headset moderno (Meta Quest, HTC Vive, etc.)

---

## 🔧 Solução de Problemas

### "Nenhum polígono fechado encontrado"
**Causa:** O arquivo DXF não contém LWPOLYLINE ou POLYLINE fechadas, ou as entidades estão em layers desativados.

**Solução:**
1. Abra o arquivo no AutoCAD ou LibreCAD
2. Certifique-se de que os contornos dos ambientes são **polilínhas fechadas** (PEDIT > Close)
3. Verifique se todas as layers estão visíveis
4. Salve e tente novamente

### "Erro ao carregar arquivo"
**Causa:** Arquivo DXF corrompido, versão incompatível ou codificação de texto inválida.

**Solução:**
1. Abra o arquivo no AutoCAD/LibreCAD e salve como DXF R2010 ou superior
2. Certifique-se de que o arquivo não está em uso por outro programa

### A geometria gerada está em escala errada
**Causa:** O arquivo DXF pode estar em unidades diferentes das esperadas.

**Solução:**
- O ArchiDive detecta automaticamente a unidade do arquivo (mm, cm, m, polegadas)
- Se a escala ainda estiver errada, verifique as configurações de unidade no seu software CAD antes de exportar o DXF

### PyOpenGL não instalado / Visualizador não aparece
**Solução:**
```bash
pip install PyOpenGL PyOpenGL-accelerate
```
Em alguns sistemas Linux pode ser necessário:
```bash
sudo apt install python3-opengl
```

### Erro ao exportar glTF: "pygltflib não instalado"
**Solução:**
```bash
pip install pygltflib
```

---

## 📁 Formatos de Saída e Compatibilidade

| Software | OBJ | glTF |
|----------|-----|------|
| **Blender** | ✅ Nativo | ✅ Nativo (2.8+) |
| **Unity** | ✅ Via import | ✅ Via plugin |
| **Unreal Engine** | ✅ Via import | ✅ Via Interchange |
| **3ds Max** | ✅ Nativo | ✅ Via plugin |
| **Maya** | ✅ Nativo | ✅ Via plugin |
| **A-Frame (WebVR)** | ✅ Via loader | ✅ Nativo |
| **Mozilla Hubs** | ❌ | ✅ Nativo |
| **Meta Quest** | ❌ | ✅ Via app |
| **Sketchfab** | ✅ | ✅ |

---

## 💡 Dicas Profissionais

1. **Organize seu DXF:** Separe cada cômodo em um layer diferente para facilitar identificação
2. **Feche os polígonos:** Use sempre `PEDIT > Close` para garantir que as polilínhas estejam fechadas
3. **Escala real:** Desenhe na escala real (1:1) para que os cálculos de área sejam corretos
4. **Exportação para Blender:** Após importar o OBJ no Blender, aplique um "Smooth Shading" e adicione luzes para um resultado fotorrealista
5. **Experiência VR com A-Frame:**
```html
<a-scene>
  <a-assets>
    <a-asset-item id="planta" src="archidive_export.gltf"></a-asset-item>
  </a-assets>
  <a-entity gltf-model="#planta" position="0 0 0"></a-entity>
  <a-camera position="0 1.6 5"></a-camera>
</a-scene>
```

---

## 📋 Atalhos de Teclado

| Atalho | Ação |
|--------|------|
| `Ctrl+O` | Abrir DXF |
| `Ctrl+E` | Exportar OBJ |
| `Ctrl+Q` | Sair |

---

## 🏗️ Estrutura do Projeto

```
archidive/
├── main.py              ← Ponto de entrada
├── requirements.txt     ← Dependências Python
├── setup.py             ← Script de instalação
├── GUIA_DE_USO.md       ← Este guia
└── archidive/
    ├── __init__.py
    ├── backend.py       ← Lógica de processamento DXF e exportação
    └── frontend.py      ← Interface gráfica PyQt5 + OpenGL
```

---

## 📜 Licença

ArchiDive é um software de código aberto. Veja o arquivo `LICENSE` para detalhes.

---

*ArchiDive v1.0 — Transformando plantas em mundos*
