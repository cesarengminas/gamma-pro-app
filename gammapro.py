"""
GammaPro v1.01 - Processamento de Dados de Gamaespectrometria
Inclui: Índice Laterítico, Calor Radiogênico, Fator f, Mapa Ternário, eU/eTh/K Anômalos
"""

import os
os.environ['MPLBACKEND'] = 'TkAgg'

import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import Normalize

from scipy.interpolate import griddata
import pyproj
import rasterio
from rasterio.transform import from_origin
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class GammaProApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GammaPro v1.03 - Processamento de Dados de Gamaespectrometria")
        self.geometry("1400x900")
        self.data = None
        self.df_processed = None
        self.output_dir = ""
        self.setup_ui()
        print("[GammaPro v1.03] Interface criada com sucesso!")
    
    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="GAMMAPRO\nv1.01", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.btn_carregar = ctk.CTkButton(self.sidebar, text="📂 Carregar Arquivo", command=self.load_file, height=40)
        self.btn_carregar.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_dados = ctk.CTkButton(self.sidebar, text="📊 Ver Dados", command=self.show_data_viewer, height=40, state="disabled")
        self.btn_dados.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_eda = ctk.CTkButton(self.sidebar, text="📈 Análise Exploratória", command=self.show_eda, height=40, state="disabled")
        self.btn_eda.grid(row=3, column=0, padx=20, pady=10)
        
        self.btn_processar = ctk.CTkButton(self.sidebar, text="⚙️ Processar Dados", command=self.process_data, height=40, state="disabled")
        self.btn_processar.grid(row=4, column=0, padx=20, pady=10)
        
        self.btn_processar.configure(state="normal")
        
        self.btn_indices = ctk.CTkButton(self.sidebar, text="📐 Índices e Razões", command=self.show_indices, height=40, state="disabled")
        self.btn_indices.grid(row=5, column=0, padx=20, pady=10)
        
        self.btn_exportar = ctk.CTkButton(self.sidebar, text="💾 Exportar", command=self.export_data, height=40, state="disabled")
        self.btn_exportar.grid(row=6, column=0, padx=20, pady=10)
        
        self.btn_sair = ctk.CTkButton(self.sidebar, text="❌ Sair", command=self.quit, height=40, fg_color="#dc3545")
        self.btn_sair.grid(row=7, column=0, padx=20, pady=20)
        
        self.settings_frame = ctk.CTkFrame(self.sidebar)
        self.settings_frame.grid(row=8, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.settings_frame, text="Configurações", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=10, pady=(10, 5))
        ctk.CTkLabel(self.settings_frame, text="Célula (m):").grid(row=1, column=0, padx=10, sticky="w")
        self.entry_cell = ctk.CTkEntry(self.settings_frame, width=80)
        self.entry_cell.insert(0, "125")
        self.entry_cell.grid(row=2, column=0, padx=10, pady=5)
        
        ctk.CTkLabel(self.settings_frame, text="EPSG:").grid(row=3, column=0, padx=10, sticky="w")
        self.entry_epsg = ctk.CTkEntry(self.settings_frame, width=80)
        self.entry_epsg.insert(0, "31980")
        self.entry_epsg.grid(row=4, column=0, padx=10, pady=(5, 10))
        
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Bem-vindo ao GammaPro v1.01!\nCarregue um arquivo XYZ para começar.", font=ctk.CTkFont(size=16))
        self.lbl_status.place(relx=0.5, rely=0.4, anchor="center")
    
    def load_file(self):
        filepath = filedialog.askopenfilename(title="Selecionar arquivo", filetypes=[("XYZ", "*.XYZ *.xyz"), ("Todos", "*.*")])
        if not filepath:
            return
        
        print(f"[GammaPro] Carregando: {filepath}")
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            data_start = 0
            for i, line in enumerate(lines):
                if line.strip() and line.strip()[0].isdigit():
                    data_start = i
                    break
            
            self.data = pd.read_csv(filepath, skiprows=data_start, delim_whitespace=True, header=None,
                names=['X', 'Y', 'FIDUCIAL', 'GPSALT', 'BARO', 'ALTURA', 'MDT', 'CTB', 'KB', 'UB', 'THB', 
                       'UUP', 'LIVE_TIME', 'COSMICO', 'TEMP', 'CTCOR', 'KCOR', 'UCOR', 'THCOR', 'CTEXP', 
                       'KPERC', 'eU', 'eTH', 'THKRAZAO', 'UKRAZAO', 'UTHRAZAO', 'LONGITUDE', 'LATITUDE', 'DATA', 'HORA'])
            
            for col in ['X', 'Y', 'KPERC', 'eU', 'eTH', 'LONGITUDE', 'LATITUDE']:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
            
            self.original_data = self.data.copy()
            self.df_processed = self.data.copy()
            
            self.lbl_status.configure(text=f"Arquivo carregado!\n{len(self.data):,} pontos\n{len(self.data.columns)} colunas")
            self.btn_dados.configure(state="normal")
            self.btn_eda.configure(state="normal")
            self.btn_processar.configure(state="normal")
            messagebox.showinfo("Sucesso", f"Carregado: {len(self.data):,} pontos\n{len(self.data.columns)} colunas")
            print(f"[GammaPro] Dados carregados: {len(self.data)} pontos, {len(self.data.columns)} colunas")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            print(f"[GammaPro] Erro: {e}")
    
    def show_data_viewer(self):
        if self.data is None:
            return
        
        for w in self.main_frame.winfo_children():
            w.destroy()
        
        nb = ttk.Notebook(self.main_frame)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Aba 1: Tabela de dados
        f1 = ctk.CTkFrame(nb)
        nb.add(f1, text="📋 Dados")
        
        f1.grid_rowconfigure(0, weight=1)
        f1.grid_columnconfigure(0, weight=1)
        
        tree_frame = ctk.CTkFrame(f1)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        cols = list(self.data.columns)
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
        
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=80)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        for i, row in self.data.head(500).iterrows():
            tree.insert("", "end", values=list(row.values))
        
        # Aba 2: Atributos/Estatísticas
        f2 = ctk.CTkFrame(nb)
        nb.add(f2, text="📊 Atributos")
        
        txt = ctk.CTkTextbox(f2, font=("Courier", 11))
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        
        info = f"""INFORMAÇÕES DOS DADOS
====================

Total de registros: {len(self.data):,}
Total de colunas: {len(self.data.columns)}

COLUNAS:
"""
        for col in self.data.columns:
            dtype = self.data[col].dtype
            non_null = self.data[col].notna().sum()
            info += f"  - {col}: {dtype} ({non_null:,} valores não-nulos)\n"
        
        info += f"""
ESTATÍSTICAS DAS VARIÁVEIS PRINCIPAIS:
======================================

K (Potássio %):
  Mín: {self.data['KPERC'].min():.4f}
  Máx: {self.data['KPERC'].max():.4f}
  Média: {self.data['KPERC'].mean():.4f}
  Desvio: {self.data['KPERC'].std():.4f}
  Negativos: {(self.data['KPERC'] < 0).sum():,}

eU (Urânio ppm):
  Mín: {self.data['eU'].min():.4f}
  Máx: {self.data['eU'].max():.4f}
  Média: {self.data['eU'].mean():.4f}
  Desvio: {self.data['eU'].std():.4f}
  Negativos: {(self.data['eU'] < 0).sum():,}

eTh (Tório ppm):
  Mín: {self.data['eTH'].min():.4f}
  Máx: {self.data['eTH'].max():.4f}
  Média: {self.data['eTH'].mean():.4f}
  Desvio: {self.data['eTH'].std():.4f}
  Negativos: {(self.data['eTH'] < 0).sum():,}

COORDENADAS:
============
X: {self.data['X'].min():.2f} a {self.data['X'].max():.2f}
Y: {self.data['Y'].min():.2f} a {self.data['Y'].max():.2f}
"""
        txt.insert("1.0", info)
        txt.configure(state="disabled")
        
        # Aba 3: Visualização espacial interativa
        f3 = ctk.CTkFrame(nb)
        nb.add(f3, text="🗺️ Espacial")
        
        f3.grid_rowconfigure(1, weight=1)
        f3.grid_columnconfigure(0, weight=1)
        
        # Seletor de variáveis
        sel_frame = ctk.CTkFrame(f3, height=50)
        sel_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(sel_frame, text="Variável:").grid(row=0, column=0, padx=5)
        
        self.vars_to_plot = ['KPERC', 'eU', 'eTH', 'THKRAZAO', 'UKRAZAO', 'UTHRAZAO', 'CTB', 'KB', 'UB', 'THB']
        self.var_select = ctk.CTkComboBox(sel_frame, values=self.vars_to_plot, state="readonly")
        self.var_select.set("KPERC")
        self.var_select.grid(row=0, column=1, padx=5)
        
        ctk.CTkButton(sel_frame, text="🔄 Atualizar", command=lambda: self.update_plot(f3)).grid(row=0, column=2, padx=10)
        ctk.CTkButton(sel_frame, text="💾 GeoTIFF", command=lambda: self.export_current_map(self.var_select.get(), self.data)).grid(row=0, column=3, padx=10)
        
        # Frame do gráfico
        self.plot_frame = ctk.CTkFrame(f3)
        self.plot_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        self.update_plot(f3)
    
    def update_plot(self, parent_frame):
        for w in self.plot_frame.winfo_children():
            w.destroy()
        
        var_name = self.var_select.get()
        df = self.data.dropna(subset=['X', 'Y', var_name])
        
        if len(df) == 0:
            ctk.CTkLabel(self.plot_frame, text="Sem dados para plotar").pack()
            return
        
        vmin, vmax = df[var_name].quantile(0.02), df[var_name].quantile(0.98)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        sc = ax.scatter(df['X'], df['Y'], c=df[var_name], cmap='turbo', s=2, vmin=vmin, vmax=vmax)
        ax.set_title(f'Distribuição Espacial de {var_name}')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        plt.colorbar(sc, ax=ax, label=var_name)
        plt.tight_layout()
        
        c = FigureCanvasTkAgg(fig, master=self.plot_frame)
        c.draw()
        c.get_tk_widget().pack(fill="both", expand=True)
    
    def show_eda(self):
        if self.data is None:
            return
        
        for w in self.main_frame.winfo_children():
            w.destroy()
        
        nb = ttk.Notebook(self.main_frame)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        
        # Aba 1: Seletor de variável
        f0 = ctk.CTkFrame(nb)
        nb.add(f0, text="📊 Análise")
        
        f0.grid_rowconfigure(3, weight=1)
        f0.grid_columnconfigure(0, weight=1)
        
        # Seletor
        sel_frame = ctk.CTkFrame(f0)
        sel_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(sel_frame, text="Variável:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=5)
        self.eda_var_select = ctk.CTkComboBox(sel_frame, values=numeric_cols, state="readonly")
        self.eda_var_select.set("KPERC")
        self.eda_var_select.grid(row=0, column=1, padx=5)
        
        ctk.CTkButton(sel_frame, text="🔄 Plotar", command=lambda: self.update_eda_plot(nb, numeric_cols)).grid(row=0, column=2, padx=10)
        ctk.CTkButton(sel_frame, text="💾 GeoTIFF", command=lambda: self.export_current_map(self.eda_var_select.get(), self.data)).grid(row=0, column=3, padx=10)
        
        # Opções de corte
        opt_frame = ctk.CTkFrame(f0)
        opt_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(opt_frame, text="Corte por %:").grid(row=0, column=0, padx=5, sticky="w")
        self.outlier_pct = ctk.CTkEntry(opt_frame, width=60)
        self.outlier_pct.insert(0, "2")
        self.outlier_pct.grid(row=0, column=1, padx=5)
        
        ctk.CTkButton(opt_frame, text="✂️ Aplicar %", command=lambda: self.apply_outlier_cut_pct(nb, numeric_cols), fg_color="#28a745").grid(row=0, column=2, padx=10)
        
        ctk.CTkLabel(opt_frame, text="Limite inferior:").grid(row=1, column=0, padx=5, sticky="w")
        self.limit_lower = ctk.CTkEntry(opt_frame, width=80)
        self.limit_lower.grid(row=1, column=1, padx=5)
        
        ctk.CTkLabel(opt_frame, text="Limite superior:").grid(row=1, column=2, padx=5, sticky="w")
        self.limit_upper = ctk.CTkEntry(opt_frame, width=80)
        self.limit_upper.grid(row=1, column=3, padx=5)
        
        ctk.CTkButton(opt_frame, text="✂️ Aplicar Limites", command=lambda: self.apply_outlier_cut_manual(nb, numeric_cols), fg_color="#fd7e14").grid(row=1, column=4, padx=10)
        
        ctk.CTkButton(opt_frame, text="🔄 Reset Dados", command=lambda: self.reset_data(nb, numeric_cols), fg_color="#6c757d").grid(row=2, column=0, columnspan=5, pady=10)
        
        self.info_label = ctk.CTkLabel(opt_frame, text="", font=ctk.CTkFont(size=12))
        self.info_label.grid(row=3, column=0, columnspan=5, pady=5)
        
        self.eda_plot_frame = ctk.CTkFrame(f0)
        self.eda_plot_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        self.update_eda_plot(nb, numeric_cols)
    
    def update_eda_plot(self, nb, numeric_cols):
        for w in self.eda_plot_frame.winfo_children():
            w.destroy()
        
        var_name = self.eda_var_select.get()
        df = self.data.dropna(subset=[var_name])
        
        if len(df) == 0:
            ctk.CTkLabel(self.eda_plot_frame, text="Sem dados").pack()
            return
        
        q1 = df[var_name].quantile(0.25)
        q3 = df[var_name].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        
        self.limit_lower.delete(0, "end")
        self.limit_lower.insert(0, f"{lower:.4f}")
        self.limit_upper.delete(0, "end")
        self.limit_upper.insert(0, f"{upper:.4f}")
        
        self.info_label.configure(text=f"Pontos: {len(df):,} | Min: {df[var_name].min():.4f} | Max: {df[var_name].max():.4f}")
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        axes[0, 0].hist(df[var_name], bins=50, color='#2fa4e7', edgecolor='black', alpha=0.7)
        axes[0, 0].axvline(lower, color='red', linestyle='--', linewidth=2, label=f'Lim inf: {lower:.2f}')
        axes[0, 0].axvline(upper, color='red', linestyle='--', linewidth=2, label=f'Lim sup: {upper:.2f}')
        axes[0, 0].legend(fontsize=8)
        axes[0, 0].set_title(f'Histograma - {var_name}')
        axes[0, 0].set_xlabel(var_name)
        
        bp = axes[0, 1].boxplot(df[var_name], patch_artist=True,
                          boxprops=dict(facecolor='#2fa4e7', alpha=0.7))
        axes[0, 1].set_title(f'Boxplot - {var_name}')
        axes[0, 1].set_ylabel(var_name)
        
        stats_text = f"""Estatísticas:
---
Mín: {df[var_name].min():.4f}
Q1: {q1:.4f}
Mediana: {df[var_name].median():.4f}
Q3: {q3:.4f}
Máx: {df[var_name].max():.4f}
Média: {df[var_name].mean():.4f}
Desvio: {df[var_name].std():.4f}
---
IQR: {iqr:.4f}
Lim inf (1.5*IQR): {lower:.4f}
Lim sup (1.5*IQR): {upper:.4f}
Outliers: {((df[var_name] < lower) | (df[var_name] > upper)).sum():,}
"""
        axes[1, 0].text(0.1, 0.5, stats_text, transform=axes[1, 0].transAxes, 
                       fontsize=10, verticalalignment='center', fontfamily='monospace')
        axes[1, 0].axis('off')
        axes[1, 0].set_title('Estatísticas')
        
        df_sp = self.data.dropna(subset=['X', 'Y', var_name])
        if len(df_sp) > 0:
            vmin, vmax = df_sp[var_name].quantile(0.02), df_sp[var_name].quantile(0.98)
            sc = axes[1, 1].scatter(df_sp['X'], df_sp['Y'], c=df_sp[var_name], 
                                    cmap='turbo', s=1, vmin=vmin, vmax=vmax)
            axes[1, 1].set_title(f'Espacial - {var_name}')
            axes[1, 1].set_xlabel('X (m)')
            axes[1, 1].set_ylabel('Y (m)')
            plt.colorbar(sc, ax=axes[1, 1], label=var_name)
        
        plt.tight_layout()
        
        c = FigureCanvasTkAgg(fig, master=self.eda_plot_frame)
        c.draw()
        c.get_tk_widget().pack(fill="both", expand=True)
    
    def apply_outlier_cut_pct(self, nb, numeric_cols):
        try:
            pct = float(self.outlier_pct.get())
            if pct < 0 or pct > 50:
                messagebox.showerror("Erro", "Porcentagem deve estar entre 0 e 50")
                return
        except:
            messagebox.showerror("Erro", "Valor inválido")
            return
        
        original_count = len(self.data)
        
        for var in ['KPERC', 'eU', 'eTH']:
            if var in self.data.columns:
                df = self.data[var].dropna()
                lower = df.quantile(pct/100)
                upper = df.quantile(1 - pct/100)
                
                mask = (self.data[var] >= lower) & (self.data[var] <= upper)
                self.data.loc[~mask, var] = np.nan
        
        self.update_eda_plot(nb, numeric_cols)
        
        new_count = len(self.data.dropna(subset=['KPERC', 'eU', 'eTH']))
        removed = original_count - new_count
        
        messagebox.showinfo("Sucesso", f"Outliers removidos: {removed} pontos\n({pct}% em cada extremo)\nPontos restantes: {new_count:,}")
    
    def apply_outlier_cut_manual(self, nb, numeric_cols):
        var_name = self.eda_var_select.get()
        
        try:
            lower = float(self.limit_lower.get())
            upper = float(self.limit_upper.get())
            
            if lower >= upper:
                messagebox.showerror("Erro", "Limite inferior deve ser menor que superior")
                return
        except:
            messagebox.showerror("Erro", "Valores de limite inválidos")
            return
        
        original_count = len(self.data.dropna(subset=[var_name]))
        
        mask = (self.data[var_name] >= lower) & (self.data[var_name] <= upper)
        self.data.loc[~mask, var_name] = np.nan
        
        new_count = len(self.data.dropna(subset=[var_name]))
        removed = original_count - new_count
        
        messagebox.showinfo("Sucesso", f"Outliers removidos de {var_name}: {removed} pontos\nPontos restantes: {new_count:,}")
        
        self.update_eda_plot(nb, numeric_cols)
    
    def reset_data(self, nb, numeric_cols):
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja resetar os dados?\nTodos os cortes serão perdidos."):
            if hasattr(self, 'original_data'):
                self.data = self.original_data.copy()
                self.lbl_status.configure(text=f"Dados resetados\n{len(self.data):,} pontos")
                self.update_eda_plot(nb, numeric_cols)
            else:
                messagebox.showwarning("Aviso", "Dados originais não disponíveis")
    
    def process_data(self):
        if self.data is None:
            return
        
        for w in self.main_frame.winfo_children():
            w.destroy()
        
        self.df_processed = self.data.copy()
        
        self.df_processed['K_neg'] = self.df_processed['KPERC'] < 0
        self.df_processed['eU_neg'] = self.df_processed['eU'] < 0
        self.df_processed['eTh_neg'] = self.df_processed['eTH'] < 0
        self.df_processed['over_water'] = self.df_processed['KPERC'] < 0.25
        
        self.df_processed['K_display'] = self.df_processed['KPERC'].clip(lower=0.001)
        self.df_processed['eU_display'] = self.df_processed['eU'].clip(lower=0.001)
        self.df_processed['eTh_display'] = self.df_processed['eTH'].clip(lower=0.001)
        
        self.btn_exportar.configure(state="normal")
        self.btn_indices.configure(state="normal")
        
        res = ctk.CTkFrame(self.main_frame)
        res.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(res, text="✅ Processamento Concluído!", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        info = ctk.CTkTextbox(res, font=("Courier", 11))
        info.pack(fill="both", expand=True, padx=20, pady=20)
        
        txt = f"""RESULTADOS DO PROCESSAMENTO
===============================

Pontos processados: {len(self.df_processed):,}
Pontos sobre água (K < 0.25%): {self.df_processed['over_water'].sum():,}

Valores negativos preservados:
  - K: {self.df_processed['K_neg'].sum():,}
  - eU: {self.df_processed['eU_neg'].sum():,}
  - eTh: {self.df_processed['eTh_neg'].sum():,}

Próximo passo: Usar "Índices e Razões" ou Exportar dados
"""
        info.insert("1.0", txt)
        info.configure(state="disabled")
        
        print("[GammaPro] Processamento concluído")
    
    def show_indices(self):
        if self.df_processed is None:
            messagebox.showwarning("Aviso", "Processe os dados primeiro!")
            return
        
        for w in self.main_frame.winfo_children():
            w.destroy()
        
        df = self.df_processed.copy()
        
        mask = (df['KPERC'].notna() & df['eU'].notna() & df['eTH'].notna() & 
                (df['KPERC'] > 0) & (df['eU'] > 0) & (df['eTH'] > 0))
        df = df[mask].copy()
        
        if len(df) == 0:
            messagebox.showerror("Erro", "Dados insuficientes para calcular índices")
            return
        
        K_mean = df['KPERC'].mean()
        eU_mean = df['eU'].mean()
        eTh_mean = df['eTH'].mean()
        K_std = df['KPERC'].std()
        eU_std = df['eU'].std()
        eTh_std = df['eTH'].std()
        
        df['Indice_Lateritico'] = df['eTH'] / (df['eU'] * df['KPERC'])
        
        df['Calor_Radiogenico'] = (0.0256 * df['eU'] + 0.0157 * df['eTH'] + 0.0088 * df['KPERC'])
        
        df['Fator_f'] = df['eTH'] / df['eU']
        
        df['eU_anomalo'] = (df['eU'] - eU_mean) / eU_std
        df['eTh_anomalo'] = (df['eTH'] - eTh_mean) / eTh_std
        df['K_anomalo'] = (df['KPERC'] - K_mean) / K_std
        
        self.df_processed = self.df_processed.merge(
            df[['X', 'Y', 'Indice_Lateritico', 'Calor_Radiogenico', 'Fator_f', 'eU_anomalo', 'eTh_anomalo', 'K_anomalo']],
            on=['X', 'Y'], how='left'
        )
        
        nb = ttk.Notebook(self.main_frame)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        
        f_info = ctk.CTkFrame(nb)
        nb.add(f_info, text="📊 Estatísticas")
        
        txt = ctk.CTkTextbox(f_info, font=("Courier", 11))
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        
        info_text = f"""ÍNDICES E RAZÕES CALCULADOS
===============================

MÉDIAS UTILIZADAS:
  K: {K_mean:.4f}%
  eU: {eU_mean:.4f} ppm
  eTh: {eTh_mean:.4f} ppm

DESVIOS PADRÃO:
  K: {K_std:.4f}%
  eU: {eU_std:.4f} ppm
  eTh: {eTh_std:.4f} ppm

ÍNDICE LATERÍTICO (eTh / (eU × K)):
  Mín: {df['Indice_Lateritico'].min():.4f}
  Máx: {df['Indice_Lateritico'].max():.4f}
  Média: {df['Indice_Lateritico'].mean():.4f}

CALOR RADIOGÊNICO (W/g):
  H = 0.0256×eU + 0.0157×eTh + 0.0088×K
  Mín: {df['Calor_Radiogenico'].min():.6f}
  Máx: {df['Calor_Radiogenico'].max():.6f}
  Média: {df['Calor_Radiogenico'].mean():.6f}

FATOR f (eTh/eU):
  Mín: {df['Fator_f'].min():.4f}
  Máx: {df['Fator_f'].max():.4f}
  Média: {df['Fator_f'].mean():.4f}

eU ANÔMALO (z-score):
  Mín: {df['eU_anomalo'].min():.4f}
  Máx: {df['eU_anomalo'].max():.4f}

eTh ANÔMALO (z-score):
  Mín: {df['eTh_anomalo'].min():.4f}
  Máx: {df['eTh_anomalo'].max():.4f}

K ANÔMALO (z-score):
  Mín: {df['K_anomalo'].min():.4f}
  Máx: {df['K_anomalo'].max():.4f}
"""
        txt.insert("1.0", info_text)
        txt.configure(state="disabled")
        
        self.indices_plot_frame = ctk.CTkFrame(nb)
        nb.add(self.indices_plot_frame, text="🗺️ Visualização")
        
        self.indices_plot_frame.grid_rowconfigure(1, weight=1)
        self.indices_plot_frame.grid_columnconfigure(0, weight=1)
        
        sel_frame = ctk.CTkFrame(self.indices_plot_frame, height=50)
        sel_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.indices_vars = [
            'Indice_Lateritico', 'Calor_Radiogenico', 'Fator_f',
            'eU_anomalo', 'eTh_anomalo', 'K_anomalo', 'Ternario'
        ]
        
        ctk.CTkLabel(sel_frame, text="Variável:").grid(row=0, column=0, padx=5)
        self.idx_var_select = ctk.CTkComboBox(sel_frame, values=self.indices_vars, state="readonly")
        self.idx_var_select.set("Indice_Lateritico")
        self.idx_var_select.grid(row=0, column=1, padx=5)
        
        ctk.CTkButton(sel_frame, text="🔄 Plotar", command=self.plot_indices).grid(row=0, column=2, padx=10)
        ctk.CTkButton(sel_frame, text="💾 GeoTIFF", command=self.export_current_indices_map).grid(row=0, column=3, padx=10)
        
        self.idx_plot_frame = ctk.CTkFrame(self.indices_plot_frame)
        self.idx_plot_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        self.plot_indices()
        
        print("[GammaPro v1.01] Índices calculados com sucesso")
    
    def plot_indices(self):
        for w in self.idx_plot_frame.winfo_children():
            w.destroy()
        
        var_name = self.idx_var_select.get()
        
        if var_name == 'Ternario':
            self.plot_ternary()
            return
        
        df = self.df_processed.dropna(subset=['X', 'Y', var_name])
        
        if len(df) == 0:
            ctk.CTkLabel(self.idx_plot_frame, text="Sem dados para plotar").pack()
            return
        
        vmin, vmax = df[var_name].quantile(0.02), df[var_name].quantile(0.98)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        sc = ax.scatter(df['X'], df['Y'], c=df[var_name], cmap='turbo', s=3, vmin=vmin, vmax=vmax)
        ax.set_title(f'{var_name}')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        plt.colorbar(sc, ax=ax, label=var_name)
        plt.tight_layout()
        
        c = FigureCanvasTkAgg(fig, master=self.idx_plot_frame)
        c.draw()
        c.get_tk_widget().pack(fill="both", expand=True)
    
    def plot_ternary(self):
        df = self.df_processed.dropna(subset=['X', 'Y', 'KPERC', 'eU', 'eTH'])
        df = df[(df['KPERC'] > 0) & (df['eU'] > 0) & (df['eTH'] > 0)]
        
        if len(df) == 0:
            ctk.CTkLabel(self.idx_plot_frame, text="Sem dados para plotar").pack()
            return
        
        K_vals = df['KPERC'].values
        eU_vals = df['eU'].values
        eTh_vals = df['eTH'].values
        
        K_p = np.percentile(K_vals, [2, 98])
        eU_p = np.percentile(eU_vals, [2, 98])
        eTh_p = np.percentile(eTh_vals, [2, 98])
        
        K_norm = (K_vals - K_p[0]) / (K_p[1] - K_p[0])
        eU_norm = (eU_vals - eU_p[0]) / (eU_p[1] - eU_p[0])
        eTh_norm = (eTh_vals - eTh_p[0]) / (eTh_p[1] - eTh_p[0])
        
        K_norm = np.clip(K_norm, 0, 1)
        eU_norm = np.clip(eU_norm, 0, 1)
        eTh_norm = np.clip(eTh_norm, 0, 1)
        
        colors = np.column_stack([eU_norm, eTh_norm, K_norm])
        
        fig, ax = plt.subplots(figsize=(10, 8))
        scatter = ax.scatter(df['X'], df['Y'], c=colors, s=3)
        ax.set_title('Mapa Ternário (R=eU, G=eTh, B=K)')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        
        self.add_ternary_legend(ax)
        
        plt.tight_layout()
        
        c = FigureCanvasTkAgg(fig, master=self.idx_plot_frame)
        c.draw()
        c.get_tk_widget().pack(fill="both", expand=True)
    
    def add_ternary_legend(self, ax):
        from matplotlib.patches import Polygon
        from matplotlib.lines import Line2D
        
        legend_x = ax.get_xlim()[1] - (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.15
        legend_y = ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.15
        size = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.12
        
        triangle = np.array([
            [0, size],
            [size * np.cos(np.radians(30)), size * 0.5],
            [0, 0],
            [0, size]
        ])
        
        for i in range(50):
            t = i / 50
            line = plt.Line2D(
                [legend_x + triangle[0,0] * (1-t) + triangle[1,0] * t,
                 legend_x + triangle[2,0] * (1-t) + triangle[3,0] * t],
                [legend_y + triangle[0,1] * (1-t) + triangle[1,1] * t,
                 legend_y + triangle[2,1] * (1-t) + triangle[3,1] * t],
                color='black', linewidth=0.3, alpha=0.3
            )
            ax.add_line(line)
        
        for i in range(50):
            t = i / 50
            line = plt.Line2D(
                [legend_x + triangle[0,0] * (1-t) + triangle[1,0] * t,
                 legend_x + triangle[2,0]],
                [legend_y + triangle[0,1] * (1-t) + triangle[1,1] * t,
                 legend_y + triangle[2,1]],
                color='black', linewidth=0.3, alpha=0.3
            )
            ax.add_line(line)
        
        for i in range(50):
            t = i / 50
            line = plt.Line2D(
                [legend_x + triangle[1,0],
                 legend_x + triangle[2,0] * (1-t) + triangle[3,0] * t],
                [legend_y + triangle[1,1],
                 legend_y + triangle[2,1] * (1-t) + triangle[3,1] * t],
                color='black', linewidth=0.3, alpha=0.3
            )
            ax.add_line(line)
        
        ax.text(legend_x - size*0.15, legend_y - size*0.08, 'K', fontsize=10, fontweight='bold', color='blue')
        ax.text(legend_x + size*0.55, legend_y - size*0.08, 'eU', fontsize=10, fontweight='bold', color='red')
        ax.text(legend_x + size*0.2, legend_y + size*1.05, 'eTh', fontsize=10, fontweight='bold', color='green')
        
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='eU'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='eTh'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='K')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=8)
    
    def export_current_map(self, var_name, df_source):
        if df_source is None or var_name is None:
            return
        
        output_dir = filedialog.askdirectory(title="Selecionar diretório para salvar")
        if not output_dir:
            return
        
        try:
            df = df_source.dropna(subset=['X', 'Y', var_name])
            if len(df) == 0:
                messagebox.showerror("Erro", "Sem dados para exportar")
                return
            
            cell = float(self.entry_cell.get())
            epsg = int(self.entry_epsg.get())
            
            x_min, x_max = df['X'].min() - 1000, df['X'].max() + 1000
            y_min, y_max = df['Y'].min() - 1000, df['Y'].max() + 1000
            
            ncols = int((x_max - x_min) / cell)
            nrows = int((y_max - y_min) / cell)
            
            xi = np.linspace(x_min, x_max, ncols)
            yi = np.linspace(y_min, y_max, nrows)
            xi, yi = np.meshgrid(xi, yi)
            
            vals = df[var_name].values
            grid = griddata((df['X'].values, df['Y'].values), vals, (xi, yi), method='cubic')
            
            fname = os.path.join(output_dir, f"gamma_{var_name}_{int(cell)}m.tif")
            tr = from_origin(x_min, y_max, cell, cell)
            with rasterio.open(fname, 'w', driver='GTiff', height=grid.shape[0], width=grid.shape[1],
                              count=1, dtype=np.float32, crs=pyproj.CRS.from_epsg(epsg), transform=tr, nodata=np.nan) as dst:
                dst.write(grid.astype(np.float32), 1)
            
            messagebox.showinfo("Sucesso", f"GeoTIFF salvo:\n{fname}")
            print(f"[GammaPro] GeoTIFF salvo: {fname}")
            
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            print(f"[GammaPro] Erro: {e}")
    
    def export_current_indices_map(self):
        if self.df_processed is None:
            return
        
        var_name = self.idx_var_select.get()
        
        if var_name == 'Ternario':
            messagebox.showinfo("Aviso", "Mapa ternário não pode ser exportado como GeoTIFF")
            return
        
        output_dir = filedialog.askdirectory(title="Selecionar diretório para salvar")
        if not output_dir:
            return
        
        try:
            df = self.df_processed.dropna(subset=['X', 'Y', var_name])
            if len(df) == 0:
                messagebox.showerror("Erro", "Sem dados para exportar")
                return
            
            cell = float(self.entry_cell.get())
            epsg = int(self.entry_epsg.get())
            
            x_min, x_max = df['X'].min() - 1000, df['X'].max() + 1000
            y_min, y_max = df['Y'].min() - 1000, df['Y'].max() + 1000
            
            ncols = int((x_max - x_min) / cell)
            nrows = int((y_max - y_min) / cell)

            xi = np.linspace(x_min, x_max, ncols)
            yi = np.linspace(y_max, y_min, nrows)
            xi, yi = np.meshgrid(xi, yi)
            
            vals = df[var_name].values
            grid = griddata((df['X'].values, df['Y'].values), vals, (xi, yi), method='cubic')
            
            fname = os.path.join(output_dir, f"gamma_{var_name}_{int(cell)}m.tif")
            tr = from_origin(x_min, y_max, cell, cell)
            with rasterio.open(fname, 'w', driver='GTiff', height=grid.shape[0], width=grid.shape[1],
                              count=1, dtype=np.float32, crs=pyproj.CRS.from_epsg(epsg), transform=tr, nodata=np.nan) as dst:
                dst.write(grid.astype(np.float32), 1)
            
            messagebox.showinfo("Sucesso", f"GeoTIFF salvo:\n{fname}")
            print(f"[GammaPro] GeoTIFF salvo: {fname}")
            
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            print(f"[GammaPro] Erro: {e}")
    
    def export_data(self):
        if self.df_processed is None:
            return
        
        self.output_dir = filedialog.askdirectory(title="Selecionar diretório para salvar")
        if not self.output_dir:
            return
        
        for w in self.main_frame.winfo_children():
            w.destroy()
        
        opt_frame = ctk.CTkFrame(self.main_frame)
        opt_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(opt_frame, text="📦 Exportar Dados", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        ctk.CTkLabel(opt_frame, text="Selecione os formatos de saída:").pack(pady=10)
        
        self.var_csv = ctk.BooleanVar(value=True)
        self.var_tif = ctk.BooleanVar(value=True)
        self.var_xlsx = ctk.BooleanVar(value=False)
        
        ctk.CTkCheckBox(opt_frame, text="CSV (dados processados)", variable=self.var_csv).pack(pady=5)
        ctk.CTkCheckBox(opt_frame, text="Excel (dados processados)", variable=self.var_xlsx).pack(pady=5)
        ctk.CTkCheckBox(opt_frame, text="GeoTIFF (grids interpolados)", variable=self.var_tif).pack(pady=5)
        
        self.var_k = ctk.BooleanVar(value=True)
        self.var_eu = ctk.BooleanVar(value=True)
        self.var_eth = ctk.BooleanVar(value=True)
        self.var_eu_eth = ctk.BooleanVar(value=True)
        self.var_eu_k = ctk.BooleanVar(value=True)
        self.var_eth_k = ctk.BooleanVar(value=True)
        
        self.var_indice_lat = ctk.BooleanVar(value=False)
        self.var_calor = ctk.BooleanVar(value=False)
        self.var_fator_f = ctk.BooleanVar(value=False)
        self.var_eU_anomalo = ctk.BooleanVar(value=False)
        self.var_eTh_anomalo = ctk.BooleanVar(value=False)
        self.var_K_anomalo = ctk.BooleanVar(value=False)
        
        ctk.CTkLabel(opt_frame, text="Variáveis para GeoTIFF:").pack(pady=(20, 5))
        
        ctk.CTkLabel(opt_frame, text="Básicas:").pack(pady=(5, 0))
        ctk.CTkCheckBox(opt_frame, text="K (%)", variable=self.var_k).pack(pady=2)
        ctk.CTkCheckBox(opt_frame, text="eU (ppm)", variable=self.var_eu).pack(pady=2)
        ctk.CTkCheckBox(opt_frame, text="eTh (ppm)", variable=self.var_eth).pack(pady=2)
        
        ctk.CTkLabel(opt_frame, text="Razões:").pack(pady=(5, 0))
        ctk.CTkCheckBox(opt_frame, text="eU/eTh", variable=self.var_eu_eth).pack(pady=2)
        ctk.CTkCheckBox(opt_frame, text="eU/K", variable=self.var_eu_k).pack(pady=2)
        ctk.CTkCheckBox(opt_frame, text="eTh/K", variable=self.var_eth_k).pack(pady=2)
        
        ctk.CTkLabel(opt_frame, text="Índices:").pack(pady=(5, 0))
        ctk.CTkCheckBox(opt_frame, text="Índice Laterítico", variable=self.var_indice_lat).pack(pady=2)
        ctk.CTkCheckBox(opt_frame, text="Calor Radiogênico", variable=self.var_calor).pack(pady=2)
        ctk.CTkCheckBox(opt_frame, text="Fator f", variable=self.var_fator_f).pack(pady=2)
        ctk.CTkCheckBox(opt_frame, text="eU Anômalo", variable=self.var_eU_anomalo).pack(pady=2)
        ctk.CTkCheckBox(opt_frame, text="eTh Anômalo", variable=self.var_eTh_anomalo).pack(pady=2)
        ctk.CTkCheckBox(opt_frame, text="K Anômalo", variable=self.var_K_anomalo).pack(pady=2)
        
        ctk.CTkButton(opt_frame, text="💾 Exportar", command=self.do_export, height=40).pack(pady=20)
    
    def do_export(self):
        print(f"[GammaPro] Exportando para: {self.output_dir}")
        
        try:
            exported = []
            
            if self.var_csv.get():
                csv_file = os.path.join(self.output_dir, "gamma_data.csv")
                self.df_processed.to_csv(csv_file, index=False)
                exported.append(f"CSV: {csv_file}")
                print(f"[GammaPro] CSV salvo: {csv_file}")
            
            if self.var_xlsx.get():
                xlsx_file = os.path.join(self.output_dir, "gamma_data.xlsx")
                self.df_processed.to_excel(xlsx_file, index=False)
                exported.append(f"Excel: {xlsx_file}")
                print(f"[GammaPro] Excel salvo: {xlsx_file}")
            
            if self.var_tif.get():
                cell = float(self.entry_cell.get())
                epsg = int(self.entry_epsg.get())
                
                mask = ~self.df_processed['X'].isna() & ~self.df_processed['Y'].isna()
                df = self.df_processed[mask].copy()
                
            x_min, x_max = df['X'].min() - 1000, df['X'].max() + 1000
            y_min, y_max = df['Y'].min() - 1000, df['Y'].max() + 1000
            
            ncols = int((x_max - x_min) / cell)
            nrows = int((y_max - y_min) / cell)
            
            xi = np.linspace(x_min, x_max, ncols)
            yi = np.linspace(y_max, y_min, nrows)
            xi, yi = np.meshgrid(xi, yi)
            
            vars_dict = {}
            if self.var_k.get():
                vars_dict['K'] = df['K_display'].values
                if self.var_eu.get():
                    vars_dict['eU'] = df['eU_display'].values
                if self.var_eth.get():
                    vars_dict['eTh'] = df['eTh_display'].values
                
                grids = {}
                for name, vals in vars_dict.items():
                    print(f"[GammaPro] Interpolando {name}...")
                    grids[name] = griddata((df['X'].values, df['Y'].values), vals, (xi, yi), method='cubic')
                
                if self.var_eu_eth.get() and 'eU' in grids and 'eTh' in grids:
                    grids['eU_eTh_ratio'] = np.divide(grids['eU'], grids['eTh'], out=np.full_like(grids['eU'], np.nan), where=grids['eTh'] != 0)
                if self.var_eu_k.get() and 'eU' in grids and 'K' in grids:
                    grids['eU_K_ratio'] = np.divide(grids['eU'], grids['K'], out=np.full_like(grids['eU'], np.nan), where=grids['K'] != 0)
                if self.var_eth_k.get() and 'eTh' in grids and 'K' in grids:
                    grids['eTh_K_ratio'] = np.divide(grids['eTh'], grids['K'], out=np.full_like(grids['eTh'], np.nan), where=grids['K'] != 0)
                
                if self.var_indice_lat.get():
                    mask_idx = ~df['Indice_Lateritico'].isna()
                    if mask_idx.sum() > 0:
                        grids['Indice_Lateritico'] = griddata(
                            (df.loc[mask_idx, 'X'].values, df.loc[mask_idx, 'Y'].values),
                            df.loc[mask_idx, 'Indice_Lateritico'].values, (xi, yi), method='cubic'
                        )
                if self.var_calor.get():
                    mask_idx = ~df['Calor_Radiogenico'].isna()
                    if mask_idx.sum() > 0:
                        grids['Calor_Radiogenico'] = griddata(
                            (df.loc[mask_idx, 'X'].values, df.loc[mask_idx, 'Y'].values),
                            df.loc[mask_idx, 'Calor_Radiogenico'].values, (xi, yi), method='cubic'
                        )
                if self.var_fator_f.get():
                    mask_idx = ~df['Fator_f'].isna()
                    if mask_idx.sum() > 0:
                        grids['Fator_f'] = griddata(
                            (df.loc[mask_idx, 'X'].values, df.loc[mask_idx, 'Y'].values),
                            df.loc[mask_idx, 'Fator_f'].values, (xi, yi), method='cubic'
                        )
                if self.var_eU_anomalo.get():
                    mask_idx = ~df['eU_anomalo'].isna()
                    if mask_idx.sum() > 0:
                        grids['eU_anomalo'] = griddata(
                            (df.loc[mask_idx, 'X'].values, df.loc[mask_idx, 'Y'].values),
                            df.loc[mask_idx, 'eU_anomalo'].values, (xi, yi), method='cubic'
                        )
                if self.var_eTh_anomalo.get():
                    mask_idx = ~df['eTh_anomalo'].isna()
                    if mask_idx.sum() > 0:
                        grids['eTh_anomalo'] = griddata(
                            (df.loc[mask_idx, 'X'].values, df.loc[mask_idx, 'Y'].values),
                            df.loc[mask_idx, 'eTh_anomalo'].values, (xi, yi), method='cubic'
                        )
                if self.var_K_anomalo.get():
                    mask_idx = ~df['K_anomalo'].isna()
                    if mask_idx.sum() > 0:
                        grids['K_anomalo'] = griddata(
                            (df.loc[mask_idx, 'X'].values, df.loc[mask_idx, 'Y'].values),
                            df.loc[mask_idx, 'K_anomalo'].values, (xi, yi), method='cubic'
                        )
                
                for name, grid in grids.items():
                    fname = os.path.join(self.output_dir, f"gamma_{name}_{int(cell)}m.tif")
                    tr = from_origin(x_min, y_max, cell, cell)
                    with rasterio.open(fname, 'w', driver='GTiff', height=grid.shape[0], width=grid.shape[1],
                                      count=1, dtype=np.float32, crs=pyproj.CRS.from_epsg(epsg), transform=tr, nodata=np.nan) as dst:
                        dst.write(grid.astype(np.float32), 1)
                    exported.append(f"GeoTIFF: {fname}")
                    print(f"[GammaPro] GeoTIFF salvo: {fname}")
            
            messagebox.showinfo("Sucesso", "Exportação concluída!\n\n" + "\n".join(exported))
            print("[GammaPro] Exportação concluída")
            
            for w in self.main_frame.winfo_children():
                w.destroy()
            
            res = ctk.CTkFrame(self.main_frame)
            res.pack(fill="both", expand=True, padx=20, pady=20)
            ctk.CTkLabel(res, text="✅ Exportação Concluída!", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
            
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            print(f"[GammaPro] Erro: {e}")
            import traceback
            traceback.print_exc()


def main():
    print("Iniciando GammaPro v1.03...")
    try:
        app = GammaProApp()
        app.mainloop()
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        input("Pressione Enter para sair...")


if __name__ == "__main__":
    main()
