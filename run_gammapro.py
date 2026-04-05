"""
GammaPro Launcher - Versão com threading para melhor compatibilidade
"""

import os
os.environ['MPLBACKEND'] = 'TkAgg'

import sys
import threading
import time


def main_thread():
    """Thread principal da aplicação"""
    import customtkinter as ctk
    from tkinter import filedialog, messagebox, ttk
    import pandas as pd
    import numpy as np
    
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    
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
            self.title("GammaPro - Processamento de Dados de Gammametria")
            self.geometry("1400x900")
            self.data = None
            self.df_processed = None
            self.grids = {}
            self.output_dir = ""
            self.setup_ui()
            print("[GammaPro] Interface criada com sucesso!")
        
        def setup_ui(self):
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(0, weight=1)
            
            self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            
            self.logo_label = ctk.CTkLabel(self.sidebar, text="GAMMAPRO", font=ctk.CTkFont(size=24, weight="bold"))
            self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
            
            self.btn_carregar = ctk.CTkButton(self.sidebar, text="Carregar Arquivo", command=self.load_file, height=40)
            self.btn_carregar.grid(row=1, column=0, padx=20, pady=10)
            
            self.btn_eda = ctk.CTkButton(self.sidebar, text="Análise Exploratória", command=self.show_eda, height=40, state="disabled")
            self.btn_eda.grid(row=2, column=0, padx=20, pady=10)
            
            self.btn_processar = ctk.CTkButton(self.sidebar, text="Processar Dados", command=self.process_data, height=40, state="disabled")
            self.btn_processar.grid(row=3, column=0, padx=20, pady=10)
            
            self.btn_interpolar = ctk.CTkButton(self.sidebar, text="Exportar", command=self.interpolate_and_export, height=40, state="disabled")
            self.btn_interpolar.grid(row=4, column=0, padx=20, pady=10)
            
            self.btn_sair = ctk.CTkButton(self.sidebar, text="Sair", command=self.quit, height=40, fg_color="#dc3545")
            self.btn_sair.grid(row=5, column=0, padx=20, pady=20)
            
            self.main_frame = ctk.CTkFrame(self)
            self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
            
            self.lbl_status = ctk.CTkLabel(self.main_frame, text="Bem-vindo ao GammaPro!\nCarregue um arquivo para começar.", font=ctk.CTkFont(size=16))
            self.lbl_status.place(relx=0.5, rely=0.4, anchor="center")
            
            self.settings_frame = ctk.CTkFrame(self.sidebar)
            self.settings_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
            
            ctk.CTkLabel(self.settings_frame, text="Célula (m):").grid(row=0, column=0, padx=10, sticky="w")
            self.entry_cell = ctk.CTkEntry(self.settings_frame, width=80)
            self.entry_cell.insert(0, "125")
            self.entry_cell.grid(row=1, column=0, padx=10, pady=5)
            
            ctk.CTkLabel(self.settings_frame, text="EPSG:").grid(row=2, column=0, padx=10, sticky="w")
            self.entry_epsg = ctk.CTkEntry(self.settings_frame, width=80)
            self.entry_epsg.insert(0, "31980")
            self.entry_epsg.grid(row=3, column=0, padx=10, pady=(5, 10))
        
        def load_file(self):
            filepath = filedialog.askopenfilename(title="Selecionar arquivo", filetypes=[("XYZ", "*.XYZ"), ("Todos", "*.*")])
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
                
                self.df_processed = self.data.copy()
                self.lbl_status.configure(text=f"Arquivo carregado!\n{len(self.data):,} pontos")
                self.btn_eda.configure(state="normal")
                self.btn_processar.configure(state="normal")
                messagebox.showinfo("Sucesso", f"Carregado: {len(self.data):,} pontos")
                print(f"[GammaPro] Dados carregados: {len(self.data)} pontos")
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                print(f"[GammaPro] Erro: {e}")
        
        def show_eda(self):
            if self.data is None:
                return
            
            for w in self.main_frame.winfo_children():
                w.destroy()
            
            nb = ttk.Notebook(self.main_frame)
            nb.pack(fill="both", expand=True, padx=10, pady=10)
            
            f1 = ctk.CTkFrame(nb)
            nb.add(f1, text="Histograma")
            
            df = self.data.dropna(subset=['KPERC', 'eU', 'eTH'])
            fig, axes = plt.subplots(2, 3, figsize=(10, 6))
            axes[0, 0].hist(df['KPERC'], bins=30, color='#2fa4e7')
            axes[0, 0].set_title('K (%)')
            axes[0, 1].hist(df['eU'], bins=30, color='#2fa4e7')
            axes[0, 1].set_title('eU (ppm)')
            axes[0, 2].hist(df['eTH'], bins=30, color='#2fa4e7')
            axes[0, 2].set_title('eTh (ppm)')
            axes[1, 0].boxplot(df['KPERC'])
            axes[1, 1].boxplot(df['eU'])
            axes[1, 2].boxplot(df['eTH'])
            plt.tight_layout()
            
            c = FigureCanvasTkAgg(fig, master=f1)
            c.draw()
            c.get_tk_widget().pack(fill="both", expand=True)
        
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
            
            print("[GammaPro] Processando razões...")
            
            self.btn_interpolar.configure(state="normal")
            
            res = ctk.CTkFrame(self.main_frame)
            res.pack(fill="both", expand=True, padx=20, pady=20)
            ctk.CTkLabel(res, text="Processamento concluído!", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        def interpolate_and_export(self):
            if self.df_processed is None:
                return
            
            self.output_dir = filedialog.askdirectory(title="Salvar em")
            if not self.output_dir:
                return
            
            print(f"[GammaPro] Exportando para: {self.output_dir}")
            
            try:
                cell = float(self.entry_cell.get())
                epsg = int(self.entry_epsg.get())
                
                mask = ~self.df_processed['X'].isna() & ~self.df_processed['Y'].isna()
                df = self.df_processed[mask].copy()
                
                x_min, x_max = df['X'].min() - 1000, df['X'].max() + 1000
                y_min, y_max = df['Y'].min() - 1000, df['Y'].max() + 1000
                
                ncols = int((x_max - x_min) / cell)
                nrows = int((y_max - y_min) / cell)
                
                xi = np.linspace(x_min, x_max, ncols)
                yi = np.linspace(y_min, y_max, nrows)
                xi, yi = np.meshgrid(xi, yi)
                
                vars_dict = {'K': df['K_display'].values, 'eU': df['eU_display'].values, 'eTh': df['eTh_display'].values}
                
                grids = {}
                for name, vals in vars_dict.items():
                    print(f"[GammaPro] Interpolando {name}...")
                    grids[name] = griddata((df['X'].values, df['Y'].values), vals, (xi, yi), method='cubic')
                
                grids['eU_eTh_ratio'] = np.divide(grids['eU'], grids['eTh'], out=np.full_like(grids['eU'], np.nan), where=grids['eTh'] != 0)
                grids['eU_K_ratio'] = np.divide(grids['eU'], grids['K'], out=np.full_like(grids['eU'], np.nan), where=grids['K'] != 0)
                grids['eTh_K_ratio'] = np.divide(grids['eTh'], grids['K'], out=np.full_like(grids['eTh'], np.nan), where=grids['K'] != 0)
                
                for name, grid in grids.items():
                    fname = os.path.join(self.output_dir, f"gamma_{name}_{int(cell)}m.tif")
                    tr = from_origin(x_min, y_max, cell, cell)
                    with rasterio.open(fname, 'w', driver='GTiff', height=grid.shape[0], width=grid.shape[1],
                                      count=1, dtype=np.float32, crs=pyproj.CRS.from_epsg(epsg), transform=tr, nodata=np.nan) as dst:
                        dst.write(grid.astype(np.float32), 1)
                    print(f"[GammaPro] Salvo: {fname}")
                
                csv_file = os.path.join(self.output_dir, "gamma_data.csv")
                self.df_processed.to_csv(csv_file, index=False)
                
                messagebox.showinfo("Sucesso", "Arquivos exportados!")
                print("[GammaPro] Exportação concluída")
                
            except Exception as e:
                messagebox.showerror("Erro", str(e))
                print(f"[GammaPro] Erro: {e}")
    
    app = GammaProApp()
    app.mainloop()


def run_app():
    """Executa a aplicação em thread separada"""
    print("[Launcher] Iniciando GammaPro...")
    try:
        main_thread()
    except Exception as e:
        print(f"[Launcher] Erro: {e}")
        import traceback
        traceback.print_exc()
        input("Pressione Enter para sair...")


if __name__ == "__main__":
    run_app()
