import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
import customtkinter as ctk
import threading
import time
import webbrowser
from io import BytesIO
import re

# Configuração do tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def extrair_nome_capitulo(url, capitulo=None):
    match = re.search(r'/capitulo/([^/]+)-capitulo-(\d+)', url)
    if match:
        nome_manga = match.group(1).replace("-", " ").title()
        numero_capitulo = capitulo if capitulo else match.group(2)
        return f"{nome_manga} Cap {numero_capitulo}"
    return "Capitulo Desconhecido"

# Nova função para baixar apenas o PDF

def baixar_apenas_pdf(url):
    response = requests.get(url)
    if response.status_code != 200:
        status_label.configure(text=f"Erro ao acessar {url}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    imagens = soup.find_all("img", attrs={"loading": "lazy", "width": "680px", "height": "860px"})

    if not imagens:
        status_label.configure(text=f"Nenhuma imagem encontrada para {url}")
        return

    caminhos_imagens = []
    total_imagens = len(imagens)
    start_time = time.time()

    for idx, img in enumerate(imagens, start=1):
        url_imagem = img.get("src")
        if url_imagem:
            caminhos_imagens.append(BytesIO(requests.get(url_imagem).content))
            if idx == 1:
                exibir_capa(url_imagem)  # Exibe a capa do mangá
            elapsed_time = time.time() - start_time
            estimated_time = (elapsed_time / idx) * (total_imagens - idx)
            progress_bar.set(idx / total_imagens)
            status_label.configure(text=f"Baixando {idx}/{total_imagens}... {estimated_time:.2f}s restantes")
            app.update_idletasks()

    if caminhos_imagens:
        status_label.configure(text="Convertendo imagens em PDF...")
        criar_pdf(caminhos_imagens, "./", extrair_nome_capitulo(url))

    status_label.configure(text=f"PDF salvo com sucesso!")
    progress_bar.set(1.0)
    app.update_idletasks()




def abrir_link(url):
    """Abre um link no navegador."""
    webbrowser.open(url)


def baixar_imagens_manga(url, pasta_destino):
    """Baixa todas as imagens de um capítulo e as salva."""
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    response = requests.get(url)
    if response.status_code != 200:
        status_label.configure(text=f"Erro ao acessar {url}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    imagens = soup.find_all("img", attrs={"loading": "lazy", "width": "680px", "height": "860px"})

    if not imagens:
        status_label.configure(text=f"Nenhuma imagem encontrada para {url}")
        return

    caminhos_imagens = []
    total_imagens = len(imagens)
    start_time = time.time()

    for idx, img in enumerate(imagens, start=1):
        url_imagem = img.get("src")
        if url_imagem:
            caminho_imagem = baixar_imagem(url_imagem, pasta_destino, f"pagina_{idx}.png")
            if caminho_imagem:
                caminhos_imagens.append(caminho_imagem)
                if idx == 1:
                    exibir_capa(url_imagem)  # Atualiza a capa para cada capítulo
                elapsed_time = time.time() - start_time
                estimated_time = (elapsed_time / idx) * (total_imagens - idx)
                progress_bar.set(idx / total_imagens)
                status_label.configure(text=f"Baixando {idx}/{total_imagens}... {estimated_time:.2f}s restantes")

    if caminhos_imagens:
        status_label.configure(text="Convertendo imagens em PDF...")
        criar_pdf(caminhos_imagens, pasta_destino, pasta_destino)

    status_label.configure(text=f"Download concluído: {pasta_destino}")
    progress_bar.set(1.0)


def baixar_imagem(url, pasta_destino, nome_arquivo):
    """Baixa uma única imagem."""
    try:
        resposta = requests.get(url, stream=True)
        if resposta.status_code == 200:
            caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)
            with open(caminho_arquivo, "wb") as arquivo:
                for chunk in resposta.iter_content(1024):
                    arquivo.write(chunk)
            return caminho_arquivo
    except Exception as e:
        print(f"Erro ao baixar a imagem {url}: {e}")
        return None


def criar_pdf(lista_imagens, pasta_destino, nome_pdf):
    """Cria um PDF com as imagens baixadas."""
    try:
        imagens = []
        for img in lista_imagens:
            try:
                imagem = Image.open(img).convert("RGB")
                imagens.append(imagem)
            except Exception as e:
                print(f"Erro ao abrir a imagem: {e}")
        caminho_pdf = os.path.join(pasta_destino, f"{nome_pdf}.pdf")
        imagens[0].save(caminho_pdf, save_all=True, append_images=imagens[1:])
        status_label.configure(text=f"PDF criado com sucesso: {caminho_pdf}")
    except Exception as e:
        print(f"Erro ao criar o PDF: {e}")


def exibir_capa(url):
    """Exibe a capa do mangá."""
    try:
        resposta = requests.get(url)
        if resposta.status_code == 200:
            imagem_bytes = BytesIO(resposta.content)
            img = ctk.CTkImage(light_image=Image.open(imagem_bytes), size=(120, 180))
            capa_label.configure(image=img, text="")
            capa_label.image = img
    except Exception as e:
        print(f"Erro ao carregar a capa: {e}")


def iniciar_download_thread():
    """Inicia o download em uma thread separada para não travar a interface."""
    threading.Thread(target=iniciar_download, daemon=True).start()

def baixar_varios_pdfs(url_base, cap_inicio, cap_fim):
    """Baixa vários capítulos e os une em um único PDF com status atualizado."""
    todas_imagens = []
    total_capitulos = cap_fim - cap_inicio + 1
    start_time = time.time()
    capa_exibida = False  # Para exibir apenas a primeira capa

    for i, cap in enumerate(range(cap_inicio, cap_fim + 1), start=1):
        url_capitulo = re.sub(r'capitulo-\d+', f'capitulo-{cap}', url_base)
        response = requests.get(url_capitulo)
        
        if response.status_code != 200:
            status_label.configure(text=f"Erro ao acessar {url_capitulo}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        imagens = soup.find_all("img", attrs={"loading": "lazy", "width": "680px", "height": "860px"})

        if not imagens:
            status_label.configure(text=f"Nenhuma imagem encontrada para {url_capitulo}")
            continue

        for idx, img in enumerate(imagens, start=1):
            url_imagem = img.get("src")
            if url_imagem:
                img_bytes = BytesIO(requests.get(url_imagem).content)
                todas_imagens.append(img_bytes)

                # Exibir capa apenas do primeiro capítulo
                if not capa_exibida:
                    exibir_capa(url_imagem)
                    capa_exibida = True

        # Atualizar status a cada capítulo baixado
        elapsed_time = time.time() - start_time
        estimated_time = (elapsed_time / i) * (total_capitulos - i)
        status_label.configure(text=f"Baixando Volume: Capítulo {cap} ({i}/{total_capitulos})... {estimated_time:.2f}s restantes")
        progress_bar.set(i / total_capitulos)
        app.update_idletasks()

    if todas_imagens:
        status_label.configure(text="Criando PDF do volume...")
        nome_pdf = extrair_nome_capitulo(url_base, f"Volume_{cap_inicio}-{cap_fim}")
        criar_pdf(todas_imagens, "./", nome_pdf)

    status_label.configure(text="Volume criado com sucesso!")
    progress_bar.set(1.0)
    app.update_idletasks()



def iniciar_download():
    """Gerencia o download dos capítulos, incluindo o modo de volume (PDF único)."""
    url_base = link_input.get().strip()
    cap_inicio = cap_inicio_input.get().strip()
    cap_fim = cap_fim_input.get().strip()
    apenas_pdf = pdf_checkbox.get()
    baixar_volume = volume_checkbox.get()  # Verifica se o usuário quer um volume único

    if not url_base:
        status_label.configure(text="Insira um link válido.")
        return

    match = re.search(r'capitulo-(\d+)', url_base)
    if not match:
        status_label.configure(text="URL inválida. Certifique-se de que contém 'capitulo-<número>'")
        return

    try:
        cap_inicio = int(cap_inicio) if cap_inicio else int(match.group(1))
        cap_fim = int(cap_fim) if cap_fim else cap_inicio
    except ValueError:
        status_label.configure(text="Capítulos devem ser números inteiros.")
        return

    status_label.configure(text=f"Iniciando download dos capítulos {cap_inicio} a {cap_fim}...")
    app.update_idletasks()

    if apenas_pdf or baixar_volume:
        baixar_varios_pdfs(url_base, cap_inicio, cap_fim)  # Junta todos os capítulos em um único PDF
    else:
        for cap in range(cap_inicio, cap_fim + 1):
            url_capitulo = re.sub(r'capitulo-\d+', f'capitulo-{cap}', url_base)
            nome_pasta = extrair_nome_capitulo(url_base, cap)
            status_label.configure(text=f"Baixando capítulo {cap}...")
            progress_bar.set(0)
            app.update_idletasks()

            baixar_imagens_manga(url_capitulo, nome_pasta)

    status_label.configure(text="Todos os downloads concluídos!")
    app.update_idletasks()



# Criar interface gráfica
app = ctk.CTk()
app.title("MangaKin")
app.geometry("600x480")
app.resizable(False, False)

frame = ctk.CTkFrame(app, corner_radius=15)
frame.pack(pady=20, padx=20, fill="both", expand=True)

title_label = ctk.CTkLabel(frame, text="MangaKin", font=("Arial", 22, "bold"))
title_label.pack(pady=10)

content_frame = ctk.CTkFrame(frame)
content_frame.pack(pady=10, padx=10, fill="x")

capa_frame = ctk.CTkFrame(content_frame, corner_radius=10)
capa_frame.pack(side="right", padx=10, pady=10)

capa_label = ctk.CTkLabel(capa_frame, text="Capa do Mangá", width=120, height=180)
capa_label.pack()

input_frame = ctk.CTkFrame(content_frame)
input_frame.pack(side="left", fill="both", expand=True)

ctk.CTkLabel(input_frame, text="Insira o link do mangá:", font=("Arial", 14)).pack(pady=5)
link_input = ctk.CTkEntry(input_frame, width=350, height=35, font=("Arial", 12))
link_input.pack(pady=5)

ctk.CTkLabel(input_frame, text="Capítulo inicial:", font=("Arial", 12)).pack()
cap_inicio_input = ctk.CTkEntry(input_frame, width=100, height=30, font=("Arial", 12))
cap_inicio_input.pack(pady=2)

ctk.CTkLabel(input_frame, text="Capítulo final:", font=("Arial", 12)).pack()
cap_fim_input = ctk.CTkEntry(input_frame, width=100, height=30, font=("Arial", 12))
cap_fim_input.pack(pady=2)



progress_bar = ctk.CTkProgressBar(frame, width=350)
progress_bar.pack(pady=5)
progress_bar.set(0)

# Adicionando checkbox e botão para baixar apenas o PDF
pdf_checkbox = ctk.CTkCheckBox(input_frame, text="Baixar apenas o PDF")
pdf_checkbox.pack(pady=5)

# Checkbox para baixar como um volume único (PDF único)
volume_checkbox = ctk.CTkCheckBox(input_frame, text="Baixar como Volume")
volume_checkbox.pack(pady=5)


start_button = ctk.CTkButton(input_frame, text="Baixar", command=iniciar_download_thread, font=("Arial", 14, "bold"), corner_radius=10)
start_button.pack(pady=10)


status_label = ctk.CTkLabel(frame, text="", font=("Arial", 12))
status_label.pack(pady=10)

app.mainloop()
