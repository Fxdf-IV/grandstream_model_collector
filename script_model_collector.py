import sys
import os
# Garante que o diretório de trabalho seja o mesmo do executável/script
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    os.chdir(base_dir)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_dir, "ms-playwright")
import pandas as pd
import re
import asyncio
from playwright.async_api import async_playwright
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext
import threading
from tkinter import ttk
import time
import traceback

# Função para extrair IPs válidos usando regex
def extrair_ips_validos(coluna):
    padrao_ip = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    return [ip.strip() for ip in coluna if isinstance(ip, str) and re.match(padrao_ip, ip.strip())]

# Função para acessar um único IP
async def acessar_ip(ip, semaforo):
    async def tentar_acesso(url, pagina):
        try:
            await pagina.goto(url, timeout=20000)
            return True, None
        except Exception as erro_goto:
            return False, erro_goto

    url_http = f"http://{ip}"
    url_https = f"https://{ip}"
    async with semaforo:
        try:
            async with async_playwright() as p:
                navegador = await p.chromium.launch(headless=True)
                pagina = await navegador.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
                )
                print(f"Acessando {url_http}...")
                ok, erro = await tentar_acesso(url_http, pagina)
                if not ok:
                    print(f"HTTP falhou para {ip}, tentando HTTPS...")
                    ok, erro = await tentar_acesso(url_https, pagina)
                    if not ok:
                        msg_erro = str(erro)
                        print(f"{ip} - Falha ao acessar: {msg_erro}")
                        await navegador.close()
                        if any(x in msg_erro.lower() for x in ["timeout", "connection refused", "host unreachable", "net::err", "could not connect", "connectionerror"]):
                            return (ip, "RAMAL DESLIGADO OU INOPERANTE")
                        else:
                            return (ip, "ERRO AO ACESSAR")
                await pagina.wait_for_load_state("networkidle")
                modelo = None
                try:
                    # Tenta div.name
                    locator = pagina.locator("div.name")
                    count = await locator.count()
                    print(f"{ip} - div.name count: {count}")
                    if count > 0:
                        try:
                            await locator.first.wait_for(state="visible", timeout=10000)
                            modelo = await locator.first.inner_text()
                            print(f"{ip} - Modelo encontrado em div.name: {modelo}")
                        except Exception as e:
                            print(f"{ip} - div.name visível mas erro ao extrair: {e}")
                    if not modelo:
                        # Tenta h2.login-title
                        locator2 = pagina.locator("h2.login-title")
                        count2 = await locator2.count()
                        print(f"{ip} - h2.login-title count: {count2}")
                        if count2 > 0:
                            try:
                                await locator2.first.wait_for(state="visible", timeout=10000)
                                texto = await locator2.first.inner_text()
                                modelo = texto.replace("Welcome to ", "").strip()
                                print(f"{ip} - Modelo encontrado em h2.login-title: {modelo}")
                            except Exception as e:
                                print(f"{ip} - h2.login-title visível mas erro ao extrair: {e}")
                    if not modelo:
                        print(f"{ip} - Nenhum modelo encontrado")
                        modelo = "-"
                except Exception as erro_elemento:
                    print(f"{ip} - Erro ao buscar elemento: {erro_elemento}")
                    modelo = "ERRO AO EXTRAIR"
                await navegador.close()
                print(f"{ip}\n  Modelo final: {modelo}\n")
                return (ip, modelo)
        except Exception as erro:
            import traceback
            erro_str = f"ERRO INESPERADO: {erro}\n{traceback.format_exc()}"
            print(f"{ip}\n  {erro_str}\n")
            return (ip, erro_str)

# Função principal para acessar todos os IPs em paralelo
async def acessar_ips_em_paralelo(lista_de_ips, max_concorrentes=5):
    semaforo = asyncio.Semaphore(max_concorrentes)
    tarefas = [acessar_ip(ip, semaforo) for ip in lista_de_ips]
    resultados = await asyncio.gather(*tarefas)
    return resultados

# Interface gráfica
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Coletor de Modelos de Telefones por IP")
        self.root.geometry("1000x700")
        self.root.minsize(700, 500)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=0)
        self.root.rowconfigure(2, weight=0)
        self.root.rowconfigure(3, weight=0)
        self.root.rowconfigure(4, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.caminho_planilha = tk.StringVar(value="Controle Rede de Dados.xlsx")
        self.nome_aba = tk.StringVar(value="Telefonia")
        self.coluna_ip = tk.StringVar(value="I")

        tk.Label(root, text="Arquivo da planilha:").pack(anchor='w')
        frame_file = tk.Frame(root)
        frame_file.pack(fill='x')
        tk.Entry(frame_file, textvariable=self.caminho_planilha, width=60).pack(side='left', padx=2)
        tk.Button(frame_file, text="Selecionar", command=self.selecionar_arquivo).pack(side='left')

        frame_opts = tk.Frame(root)
        frame_opts.pack(fill='x', pady=5)
        tk.Label(frame_opts, text="Aba:").pack(side='left')
        tk.Entry(frame_opts, textvariable=self.nome_aba, width=20).pack(side='left', padx=2)
        tk.Label(frame_opts, text="Coluna dos IPs (ex: I):").pack(side='left')
        tk.Entry(frame_opts, textvariable=self.coluna_ip, width=5).pack(side='left', padx=2)

        tk.Button(root, text="Rodar coleta", command=self.rodar_thread).pack(pady=8)

        self.result_box = scrolledtext.ScrolledText(root, width=90, height=22)
        self.result_box.pack(fill='both', expand=True)

        self.progress = ttk.Progressbar(root, orient='horizontal', length=500, mode='determinate')
        self.progress.pack(fill='x', pady=5)
        self.progress_label = tk.Label(root, text="Progresso: 0% | Tempo estimado: --:--")
        self.progress_label.pack(fill='x')

        self.cancelar = False
        self.btn_cancelar = tk.Button(root, text="Cancelar", command=self.cancelar_coleta, state='disabled', width=12)
        self.btn_cancelar.pack(pady=2)

        self.footer = tk.Label(root, text="developed by Vinicius Fxdf", fg="blue", cursor="hand2")
        self.footer.pack(side='bottom', pady=2, fill='x')
        self.footer.bind("<Button-1>", lambda e: self.abrir_github())

    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Planilhas Excel", "*.xlsx")])
        if caminho:
            self.caminho_planilha.set(caminho)
        else:
            self.caminho_planilha.set("Controle Rede de Dados.xlsx")  # Valor padrão

    def cancelar_coleta(self):
        self.cancelar = True
        self.btn_cancelar.config(state='disabled')
        self.progress_label.config(text="Coleta cancelada pelo usuário.")

    def rodar_thread(self):
        threading.Thread(target=self.rodar_asyncio, daemon=True).start()

    def rodar_asyncio(self):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.rodar())
        except Exception as e:
            self.result_box.insert(tk.END, f"Erro: {e}\n")
            self.result_box.insert(tk.END, traceback.format_exc())

    async def rodar(self):
        self.result_box.delete(1.0, tk.END)
        self.cancelar = False
        self.btn_cancelar.config(state='normal')
        caminho = self.caminho_planilha.get()
        aba = self.nome_aba.get()
        col = self.coluna_ip.get().upper()
        try:
            df = pd.read_excel(caminho, sheet_name=aba)
            idx_col = ord(col) - ord('A')
            coluna_ips = df.iloc[:, idx_col]
            lista_de_ips = extrair_ips_validos(coluna_ips)
            total = len(lista_de_ips)
            if not lista_de_ips:
                self.result_box.insert(tk.END, "Nenhum IP válido encontrado.\n")
                return
            self.result_box.insert(tk.END, f"Iniciando coleta de {total} IPs...\n\n")
            self.progress['value'] = 0
            self.progress['maximum'] = total
            self.progress_label.config(text=f"Progresso: 0% | Tempo estimado: --:--")
            start_time = time.time()
            resultados_finais = [None] * total
            semaforo = asyncio.Semaphore(5)
            async def processa_um(i, ip):
                if self.cancelar:
                    return
                resultado = await acessar_ip(ip, semaforo)
                resultados_finais[i] = resultado
                feitos = sum(1 for r in resultados_finais if r is not None)
                elapsed = time.time() - start_time
                self.progress['value'] = feitos
                if feitos > 0:
                    estimado_total = elapsed / feitos * total
                    restante = estimado_total - elapsed
                    min_rest = int(restante // 60)
                    sec_rest = int(restante % 60)
                    tempo_str = f"{min_rest:02d}:{sec_rest:02d}"
                else:
                    tempo_str = "--:--"
                self.progress_label.config(text=f"Progresso: {int(feitos/total*100)}% | Tempo estimado: {tempo_str}")
                self.result_box.insert(tk.END, f"{resultado[0]}\n  Modelo: {resultado[1]}\n\n")
                self.result_box.see(tk.END)
            tasks = [processa_um(i, ip) for i, ip in enumerate(lista_de_ips)]
            for coro in asyncio.as_completed(tasks):
                if self.cancelar:
                    break
                await coro
            if self.cancelar:
                self.result_box.insert(tk.END, "\nColeta cancelada!\n")
            else:
                self.result_box.insert(tk.END, "\nConcluído!\n")
            self.progress['value'] = total
            self.progress_label.config(text=f"Progresso: 100% | Tempo estimado: 00:00")
            self.btn_cancelar.config(state='disabled')
        except Exception as e:
            self.result_box.insert(tk.END, f"Erro: {e}\n")
            self.result_box.insert(tk.END, traceback.format_exc())

    def abrir_github(self):
        import webbrowser
        webbrowser.open_new("https://github.com/Fxdf-IV")

# EXECUÇÃO PRINCIPAL
def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--no-gui':
        # Executa modo antigo (terminal)
        df = pd.read_excel("Controle Rede de Dados.xlsx", sheet_name="Telefonia")
        coluna_ips = df.iloc[:, 8]
        lista_de_ips = extrair_ips_validos(coluna_ips)
        resultados_finais = asyncio.run(acessar_ips_em_paralelo(lista_de_ips, max_concorrentes=5))
        print("\nResumo final:")
        for ip, modelo in resultados_finais:
            print(f"{ip}\n  Modelo: {modelo}\n")
    else:
        root = tk.Tk()
        App(root)
        root.mainloop()

if __name__ == "__main__":
    main()
