import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
import pyodbc
import re
import json
from datetime import datetime
import os
import sys
import threading # Importado para multithreading
import queue    # Importado para comunicação entre threads

# --- 1. Configurações de Conexão com o MaxDB ---
DB_CONFIG = {
    'driver': '{MaxDB}',
    'server': '192.168.170.253',
    'port': '7210',
    'database': 'SMART2',
    'uid': 'DBA',
    'pwd': 'HJMODBA'
}

# --- 2. Mapeamento de Atributos ---
MAP_ATRIBUTOS = {
    "12@11": "Classificação de Risco",
    "12@10": "Especialidade",    

    "11@28": "Hipertensão",
    "11@27": "Náuseas",
    "11@66": "Dispneia",
    "11@14": "Cefaleia",
    "12@6": "Peso_Paciente_Gramas",
    "12@7": "Altura_Paciente_cm",
    "12@9": "Temperatura_C",
    "5@1": "Diagnostico_CI10",
    "12@13": "Encaminhado para (Campo Antigo)",
    "11@31": "Campo_11_31",
    "11@38": "Campo_11_38",
    "11@4": "Campo_11_4",
    "12@8": "Campo_12_8",
    "11@44": "Campo_11_44",
    "11@76": "Campo_11_76",
    "11@29": "Campo_11_29",
    # ... Adicione MAIS mapeamentos aqui conforme necessário ...
}

# --- 3. Expressão Regular para Parsar a String RCL_TXT ---
PADRAO_RCL = re.compile(r"@#(\d+)@(\d+)[%&]([^@#]*)")

# --- Função para processar uma única string RCL_TXT ---
def processar_rcl_txt(rcl_text_string):
    dados_extraidos = {}
    if not rcl_text_string:
        return dados_extraidos

    for match in PADRAO_RCL.finditer(rcl_text_string):
        form_code = match.group(1)
        attr_code = match.group(2)
        value = match.group(3)

        chave_mapeamento = f"{form_code}@{attr_code}"
        nome_campo = MAP_ATRIBUTOS.get(chave_mapeamento, f"Campo_Desconhecido_{form_code}_{attr_code}")

        dados_extraidos[nome_campo] = value

    return dados_extraidos

# --- 4. Conexão ao Banco de Dados e Extração Principal ---
def extrair_e_processar_dados_maxdb(data_inicial_str, data_final_str, usuarios_str=""):
    conn = None
    cursor = None
    
    counts = {
        "Total de Registros Encontrados": 0,
        "Por Especialidade": {}    
    }
    
    ESPECIALIDADES_ALVO = ["CLÍNICA MÉDICA", "ORTOPEDIA", "PEDIATRIA", "OBSTETRICIA"]

    try:
        if data_inicial_str and data_inicial_str != DATE_MASK:
            data_inicial_obj = datetime.strptime(data_inicial_str, "%d/%m/%Y %H:%M:%S")
            data_inicial_sql = data_inicial_obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            data_inicial_sql = None

        if data_final_str and data_final_str != DATE_MASK:
            data_final_obj = datetime.strptime(data_final_str, "%d/%m/%Y %H:%M:%S")
            data_final_sql = data_final_obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            data_final_sql = None

    except ValueError as ve:
        return f"Erro de formato de data: {ve}\nVerifique se o formato está correto (dd/mm/aaaa hh:mm:ss).", counts
    except Exception as e:
        return f"Erro na preparação dos parâmetros: {e}", counts

    try:
        conn_str = (
            f"DRIVER={DB_CONFIG['driver']};"
            f"SERVER={DB_CONFIG['server']}:{DB_CONFIG['port']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['uid']};"
            f"PWD={DB_CONFIG['pwd']};"
        )
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        query = "SELECT RCL_TXT, rcl_dthr FROM rcl WHERE RCL_COD = '060096'"

        if usuarios_str:
            usuarios_lista = [u.strip().upper() for u in usuarios_str.split(",")]
            usuarios_sql = ", ".join(f"'{u}'" for u in usuarios_lista)
            query += f" AND UPPER(RCL_USR_LOGIN) IN ({usuarios_sql})"

        query += " AND (RCL_TXT LIKE '%@#12@11&%' OR RCL_TXT LIKE '%@#12@10&%')"
        
        if data_inicial_sql and data_final_sql:
            query += f" AND rcl_dthr BETWEEN '{data_inicial_sql}' AND '{data_final_sql}'"
        elif data_inicial_sql:
            query += f" AND rcl_dthr >= '{data_inicial_sql}'"
        elif data_final_sql:
            query += f" AND rcl_dthr <= '{data_final_sql}'"

        cursor.execute(query)

        while True:
            rows = cursor.fetchmany(1000)
            if not rows:
                break
            
            for row in rows:
                rcl_txt_data = row[0]

                dados_estruturados = processar_rcl_txt(rcl_txt_data)
                
                classificacao_valor = dados_estruturados.get("Classificação de Risco", "").upper()
                especialidade_valor = dados_estruturados.get("Especialidade", "").upper()

                if especialidade_valor in ESPECIALIDADES_ALVO:
                    especialidade_chave = especialidade_valor    
                    
                    counts["Total de Registros Encontrados"] += 1    

                    if especialidade_chave not in counts["Por Especialidade"]:
                        counts["Por Especialidade"][especialidade_chave] = {
                            "Total da Especialidade": 0,
                            "Classificação Verde": 0,
                            "Classificação Amarelo": 0,
                            "Classificação Vermelho": 0,
                            "Classificação Azul": 0,
                            "Outras Classificações": 0
                        }

                    counts["Por Especialidade"][especialidade_chave]["Total da Especialidade"] += 1

                    if classificacao_valor == "VERDE":
                        counts["Por Especialidade"][especialidade_chave]["Classificação Verde"] += 1
                    elif classificacao_valor == "AMARELO":
                        counts["Por Especialidade"][especialidade_chave]["Classificação Amarelo"] += 1
                    elif classificacao_valor == "VERMELHO":
                        counts["Por Especialidade"][especialidade_chave]["Classificação Vermelho"] += 1
                    elif classificacao_valor == "AZUL":
                        counts["Por Especialidade"][especialidade_chave]["Classificação Azul"] += 1
                    elif classificacao_valor:
                        counts["Por Especialidade"][especialidade_chave]["Outras Classificações"] += 1

        return "Sucesso na geração do relatório!", counts

    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        return f"Erro no Banco de Dados: {sqlstate}\nDetalhes: {ex}", counts
    except Exception as e:
        return f"Erro Inesperado: {e}", counts
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# --- FUNÇÕES PARA A INTERFACE GRÁFICA (TKINTER) ---

# --- Definição da Máscara de Data ---
DATE_MASK = "00/00/0000 00:00:00"
LITERAL_CHARS = ['/', ' ', ':']

def apply_date_mask_behavior(event, entry_widget):
    current_value = list(entry_widget.get())
    cursor_pos = entry_widget.index(tk.INSERT)

    if event.keysym in ('Left', 'Right', 'Home', 'End'):
        return

    if event.keysym == 'BackSpace':
        if cursor_pos > 0:
            target_pos = cursor_pos - 1
            while target_pos >= 0 and DATE_MASK[target_pos] in LITERAL_CHARS:
                target_pos -= 1
            
            if target_pos >= 0:
                current_value[target_pos] = '0'
            
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, "".join(current_value))
            entry_widget.icursor(target_pos)
        return "break"

    if event.keysym == 'Delete':
        if cursor_pos < len(current_value):
            target_pos = cursor_pos
            while target_pos < len(current_value) and DATE_MASK[target_pos] in LITERAL_CHARS:
                target_pos += 1
            
            if target_pos < len(current_value):
                current_value[target_pos] = '0'
            
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, "".join(current_value))
            entry_widget.icursor(cursor_pos)
        return "break"

    if not event.char.isdigit():
        return "break"

    if len(current_value) < len(DATE_MASK):
        current_value.extend(list(DATE_MASK[len(current_value):]))
    
    target_pos = cursor_pos
    while target_pos < len(DATE_MASK) and DATE_MASK[target_pos] in LITERAL_CHARS:
        target_pos += 1

    if target_pos < len(DATE_MASK):
        current_value[target_pos] = event.char
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, "".join(current_value))
        
        next_cursor_pos = target_pos + 1
        while next_cursor_pos < len(DATE_MASK) and DATE_MASK[next_cursor_pos] in LITERAL_CHARS:
            next_cursor_pos += 1
        
        if next_cursor_pos <= len(DATE_MASK):
            entry_widget.icursor(next_cursor_pos)
        else:
            entry_widget.icursor(len(DATE_MASK))
    
    return "break"

# --- Coloca o cursor no início do campo ---
def set_cursor_to_start(event, entry_widget):
    entry_widget.icursor(0)

current_extracted_data = {}    
report_queue = queue.Queue() # Fila para comunicação entre threads

def process_report_results():
    """Processa os resultados da extração de relatório da fila da thread."""
    global current_extracted_data # <<-- CORREÇÃO AQUI!

    try:
        status_message, data_counts = report_queue.get(block=False) # Non-blocking read
    except queue.Empty:
        root.after(100, process_report_results) # Tenta novamente em 100ms se a fila estiver vazia
        return

    result_text_area.delete(1.0, tk.END) # Limpa antes de inserir
    
    if status_message.startswith("Erro"):
        result_text_area.insert(tk.END, status_message + "\n")
        messagebox.showerror("Erro no Relatório", status_message)
        current_extracted_data = {}
        update_status("Erro na geração do relatório.")
    else:
        current_extracted_data = data_counts
        result_text_area.insert(tk.END, f"{status_message}\n\n")
        
        if data_counts["Total de Registros Encontrados"] > 0:
            result_text_area.insert(tk.END, "--- Resumo do Relatório por Classificação e Especialidade ---\n", "header")
            
            total_geral_str = f"Total Geral de Registros Encontrados (somente especialidades alvo): {data_counts['Total de Registros Encontrados']}\n\n"
            result_text_area.insert(tk.END, total_geral_str)

            for especialidade_chave in sorted(data_counts["Por Especialidade"].keys()):
                especialidade_dados = data_counts["Por Especialidade"][especialidade_chave]
                
                result_text_area.insert(tk.END, f"--- {especialidade_chave} ---\n", "subheader")
                
                result_text_area.insert(tk.END, f"  Total nesta Especialidade: {especialidade_dados['Total da Especialidade']}\n")
                
                for class_key, class_value in especialidade_dados.items():
                    if class_key != "Total da Especialidade" and class_value > 0:
                        result_text_area.insert(tk.END, f"    {class_key}: {class_value}\n")
                result_text_area.insert(tk.END, "\n")
            
            messagebox.showinfo("Relatório Concluído", f"{status_message}\nTotal de {data_counts['Total de Registros Encontrados']} registros processados.")
            update_status(f"Relatório concluído! {data_counts['Total de Registros Encontrados']} registros processados.")
        else:
            result_text_area.insert(tk.END, "Nenhum registro encontrado com os critérios de data e classificação/especialidade alvo.\n")
            update_status("Relatório concluído: Nenhum registro encontrado.")
    
    # Reabilitar botão e restaurar cursor após o processamento
    btn_extract.config(state=tk.NORMAL)
    root.config(cursor="")
    
def run_extraction_thread():
    """Função que inicia a extração de dados em uma nova thread."""
    data_inicial_input = entry_data_inicial.get()
    data_final_input = entry_data_final.get()
    usuarios_input = entry_usuarios.get()

    # Desabilitar botão e mudar cursor na thread principal (GUI)
    btn_extract.config(state=tk.DISABLED)
    root.config(cursor="wait")
    result_text_area.delete(1.0, tk.END) # Limpa antes de iniciar
    update_status("Iniciando geração do relatório... Conectando ao banco de dados.")

    # Iniciar a thread de extração
    threading.Thread(target=_extraction_worker, 
                     args=(data_inicial_input, data_final_input, usuarios_input, report_queue)).start()
    
    # Começa a checar a fila por resultados
    root.after(100, process_report_results)

def _extraction_worker(data_inicial_input, data_final_input, usuarios_input, q):
    """Worker function para executar a extração em uma thread separada."""
    status_message, data_counts = extrair_e_processar_dados_maxdb(
        data_inicial_input, data_final_input, usuarios_input
    )
    q.put((status_message, data_counts)) # Coloca os resultados na fila

def save_json_gui():
    pass    

# --- CONFIGURAÇÃO DA JANELA PRINCIPAL DO TKINTER ---
root = tk.Tk()
root.title("Relatório de Classificação/Especialidade de Pacientes")    

# --- Definir o ícone da janela (AGORA COM sys._MEIPASS PARA PYINSTALLER) ---
try:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        icon_path = os.path.join(sys._MEIPASS, 'icone_relat_class.ico')
    else:
        icon_path = 'icone_relat_class.ico' 
        
    root.iconbitmap(icon_path)
except tk.TclError:
    print(f"Aviso: Ícone '{icon_path}' não encontrado ou inválido. A janela será iniciada com o ícone padrão.")

root.geometry("850x650")    

# --- Configuração de Estilo (ttk) ---
style = ttk.Style(root)
style.theme_use('vista')
style.configure('TFrame', background='#e0e0e0')
style.configure('TLabel', background='#e0e0e0', font=('Arial', 10))
style.configure('TButton', font=('Arial', 10, 'bold'))
style.configure('TLabelframe', background='#e0e0e0')
style.configure('TLabelframe.Label', background='#e0e0e0', font=('Arial', 11, 'bold'))

# Frame principal
main_frame = ttk.Frame(root, padding="10 10 10 10")
main_frame.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Frame para entrada de Datas
frame_input_dates = ttk.LabelFrame(main_frame, text="Período do Relatório", padding="10 10 10 10")
frame_input_dates.grid(row=0, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)

# Widgets de Data Inicial
label_data_inicial = ttk.Label(frame_input_dates, text="Data Inicial (dd/mm/aaaa hh:mm:ss):")
label_data_inicial.grid(row=0, column=0, sticky=tk.W, pady=5)

entry_data_inicial = ttk.Entry(frame_input_dates, width=25)
entry_data_inicial.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
entry_data_inicial.bind("<Key>", lambda event, entry=entry_data_inicial: apply_date_mask_behavior(event, entry))
entry_data_inicial.insert(0, DATE_MASK)
entry_data_inicial.bind("<Button-1>", lambda event, entry=entry_data_inicial: set_cursor_to_start(event, entry))
entry_data_inicial.bind("<FocusIn>", lambda event, entry=entry_data_inicial: set_cursor_to_start(event, entry))

# Widgets de Data Final
label_data_final = ttk.Label(frame_input_dates, text="Data Final (dd/mm/aaaa hh:mm:ss):")
label_data_final.grid(row=1, column=0, sticky=tk.W, pady=5)

entry_data_final = ttk.Entry(frame_input_dates, width=25)
entry_data_final.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
entry_data_final.bind("<Key>", lambda event, entry=entry_data_final: apply_date_mask_behavior(event, entry))
entry_data_final.insert(0, DATE_MASK)
entry_data_final.bind("<Button-1>", lambda event, entry=entry_data_final: set_cursor_to_start(event, entry))
entry_data_final.bind("<FocusIn>", lambda event, entry=entry_data_final: set_cursor_to_start(event, entry))


# --- NOVO FRAME PARA O CAMPO DE USUÁRIOS (para alinhamento) ---
frame_input_users = ttk.LabelFrame(main_frame, text="Filtro de Usuários", padding="10 10 10 10")
frame_input_users.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E)) # Posicionado abaixo das datas
frame_input_users.columnconfigure(1, weight=1) # Permite que o campo de entrada de usuários se expanda

# Widgets de Usuários (dentro do novo frame_input_users)
label_usuarios = ttk.Label(frame_input_users, text="Usuários (separados por vírgula):")
label_usuarios.grid(row=0, column=0, sticky=tk.W, pady=5) # row 0, col 0 dentro do frame_input_users

entry_usuarios = ttk.Entry(frame_input_users, width=50) # Removido padx do grid aqui
entry_usuarios.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5) # row 0, col 1 dentro do frame_input_users


# Frame para Botões (agora na row 2 do main_frame)
frame_buttons = ttk.Frame(main_frame, padding="10 0 10 0")
frame_buttons.grid(row=2, column=0, columnspan=2, pady=10) # Abaixo do filtro de usuários


# O botão agora chama run_extraction_thread
btn_extract = ttk.Button(frame_buttons, text="Gerar Relatório", command=run_extraction_thread)
btn_extract.pack(side=tk.LEFT, padx=10)

# --- Botão "Salvar Resumo" removido ---


# Área de texto rolável (agora na row 3 do main_frame)
result_text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=90, height=20, font=('Consolas', 9))
result_text_area.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky=(tk.N, tk.W, tk.E, tk.S))
main_frame.rowconfigure(3, weight=1)

# Barra de status (nova adição)
status_bar_label = ttk.Label(root, text="Pronto.", relief=tk.SUNKEN, anchor=tk.W)
# Usamos .grid em root, então precisa de sua própria row e col configuration
status_bar_label.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=0, pady=0) 
root.rowconfigure(1, weight=0) # Impede que a barra de status se expanda verticalmente

def update_status(message):
    """Função auxiliar para atualizar o texto da barra de status."""
    status_bar_label.config(text=message)
    root.update_idletasks() # Força a atualização da GUI imediatamente

# Configuração das tags de texto
result_text_area.tag_configure("header", font=('Arial', 11, 'bold'))
result_text_area.tag_configure("subheader", font=('Arial', 10, 'bold'))

# --- Binding para o TAB (adaptado à nova estrutura) ---
entry_data_inicial.bind("<Tab>", lambda event: entry_data_final.focus_set())
entry_data_final.bind("<Tab>", lambda event: entry_usuarios.focus_set())
entry_usuarios.bind("<Tab>", lambda event: btn_extract.focus_set()) # Do campo de usuário para o botão

root.mainloop()