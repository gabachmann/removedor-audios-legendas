# Removedor de áudio e legendas

Aplicativo desktop para **remover trilhas de áudio e legendas de vídeos**, preservando as demais trilhas sem recodificação (`ffmpeg -c copy`). Interface moderna com CustomTkinter.

## Recursos

- Lista vídeo, áudio e legendas com índice, idioma, codec e título.
- Seleciona individualmente as trilhas a remover, ou marca todos os áudios/legendas.
- Preserva sempre as trilhas de vídeo.
- Executa o FFmpeg em segundo plano e apresenta progresso quando a duração é conhecida.
- Pede confirmação antes de processar e protege o arquivo original.

## Requisitos

- Python 3.10 ou superior
- FFmpeg **e FFprobe** instalados e disponíveis no `PATH`

## Instalação

```bash
python -m venv .venv
```

Ative o ambiente virtual: Windows: `.venv\Scripts\activate`; macOS/Linux: `source .venv/bin/activate`.

```bash
pip install -r requirements.txt
python main.py
```

Verifique `ffmpeg -version` e `ffprobe -version` no terminal antes de executar.

## Como usar

1. Clique em **Selecionar vídeo**.
2. Marque as trilhas de áudio e/ou legenda que deseja excluir.
3. Clique em **Remover trilhas selecionadas e salvar**.
4. Escolha outro nome/caminho de saída e confirme.

> A compatibilidade do arquivo final depende do contêiner escolhido e dos codecs preservados. Recomendamos manter a mesma extensão do original. Faça backup de arquivos importantes.

## Tecnologias

Python, CustomTkinter e FFmpeg/FFprobe. Licença MIT.
