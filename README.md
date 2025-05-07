# Script GrandStream Model Collector

Coleta modelos de telefones GrandStream, acessando IPs via navegador e extraindo informações da interface web dos aparelhos.

## Funcionalidade
- Lê uma planilha Excel com IPs de telefones.
- Acessa cada IP via navegador (headless) usando Playwright.
- Extrai o modelo do telefone a partir de elementos HTML da página.
- Exibe o progresso e resultados em uma interface gráfica (Tkinter).
- Permite exportar resultados.

## Requisitos
- Python 3.8+
- Instalar dependências:
  ```bash
  pip install -r requirements.txt
  playwright install
  ```

## Como usar
1. Execute o script:
   ```bash
   python script_model_collector.py
   ```
2. Selecione a planilha e configure a aba/coluna dos IPs.
3. Clique em "Rodar coleta" para iniciar.

### Modo terminal
Para rodar sem interface gráfica:
```bash
python script_model_collector.py --no-gui
```

## Observações
- O navegador precisa ter acesso liberado aos IPs dos telefones.

## Autor
Vinicius Fxdf

## Licença
MIT
