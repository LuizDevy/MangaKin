import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
import customtkinter as ctk
import threading
import time
import webbrowser
from io import BytesIO

# Configuração do tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def extrair_nome_capitulo(url):
    partes = url.rstrip("/").split("/")[-1].replace("-capitulo-", " Cap ").title()
    return partes

def abrir_link(url):
    webbrowser.open(url)

def baixar_imagens_manga(url, pasta_destino):
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
    
    response = requests.get(url)
    if response.status_code != 200:
        status_label.configure(text="Erro ao acessar a página.")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    imagens = soup.find_all("img", attrs={"loading": "lazy", "width": "680px", "height": "860px"})
    
    if not imagens:
        status_label.configure(text="Nenhuma imagem encontrada no padrão especificado.")
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
                    exibir_capa(url_imagem)
                elapsed_time = time.time() - start_time
                estimated_time = (elapsed_time / idx) * (total_imagens - idx)
                progress_bar.set(idx / total_imagens)
                status_label.configure(text=f"Baixando {idx}/{total_imagens}... {estimated_time:.2f}s restantes")
    
    if caminhos_imagens:
        status_label.configure(text="Convertendo imagens em PDF...")
        criar_pdf(caminhos_imagens, pasta_destino, pasta_destino)
    
    status_label.configure(text=f"Download concluído! Arquivos salvos em '{pasta_destino}'")
    progress_bar.set(1.0)

def baixar_imagem(url, pasta_destino, nome_arquivo):
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
    try:
        imagens = [Image.open(img).convert("RGB") for img in lista_imagens]
        caminho_pdf = os.path.join(pasta_destino, f"{nome_pdf}.pdf")
        imagens[0].save(caminho_pdf, save_all=True, append_images=imagens[1:])
        status_label.configure(text=f"PDF criado com sucesso: {caminho_pdf}")
    except Exception as e:
        print(f"Erro ao criar o PDF: {e}")

def exibir_capa(url):
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
    threading.Thread(target=iniciar_download, daemon=True).start()

def iniciar_download():
    url = link_input.get()
    if url:
        nome_pasta = extrair_nome_capitulo(url)
        status_label.configure(text="Iniciando download...")
        progress_bar.set(0)
        baixar_imagens_manga(url, nome_pasta)

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

start_button = ctk.CTkButton(input_frame, text="Baixar", command=iniciar_download_thread, font=("Arial", 14, "bold"), corner_radius=10)
start_button.pack(pady=10)

progress_bar = ctk.CTkProgressBar(frame, width=300)
progress_bar.pack(pady=5)
progress_bar.set(0)

status_label = ctk.CTkLabel(frame, text="", font=("Arial", 12))
status_label.pack(pady=10)

buttons_frame = ctk.CTkFrame(frame)
buttons_frame.pack(pady=10)

linkedin_button = ctk.CTkButton(buttons_frame, text="Meu LinkedIn", command=lambda: abrir_link("www.linkedin.com/in/luiz-brandão-39633a244"), font=("Arial", 12), corner_radius=10)
linkedin_button.pack(side="left", padx=5)

program_button = ctk.CTkButton(buttons_frame, text="Baixar Programa", command=lambda: abrir_link("https://calibre-ebook.com"), font=("Arial", 12), corner_radius=10)
program_button.pack(side="left", padx=5)

video_button = ctk.CTkButton(buttons_frame, text="Ver Tutorial", command=lambda: abrir_link("https://youtube.com"), font=("Arial", 12), corner_radius=10)
video_button.pack(side="left", padx=5)

app.mainloop()
