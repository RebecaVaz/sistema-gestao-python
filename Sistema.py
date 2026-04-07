from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtGui import QFont
import sys
import os
import textwrap
import json
from datetime import date, datetime
import sqlite3
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import shutil
from PyQt5.QtCore import QTimer

ONEDRIVE_DIR = os.environ.get("OneDrive")

# 📁 Banco LOCAL seguro (fora do OneDrive)
BASE_DIR = os.path.join(
    os.environ["USERPROFILE"],
    "AppData",
    "Local",
    "EmpresaApp"
)

os.makedirs(BASE_DIR, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "banco_dados.db")

# ☁️ Pasta de backup na nuvem (opcional)
ONEDRIVE_DIR = os.environ.get("OneDrive")

if ONEDRIVE_DIR:
    BACKUP_CLOUD_DIR = os.path.join(ONEDRIVE_DIR, "EmpresaApp_Backups")
    os.makedirs(BACKUP_CLOUD_DIR, exist_ok=True)
else:
    BACKUP_CLOUD_DIR = None

def garantir_pasta_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
# Caminho do arquivo JSON que armazena os itens de "Comida"
CAMINHO_ARQUIVO = os.path.join(os.path.dirname(DB_PATH), "itens_comida.json")

def fazer_backup(DB_PATH, tipo="diario"):
    try:
        base_dir = os.path.dirname(DB_PATH)
        backup_dir = os.path.join(base_dir, "backups", tipo)
        os.makedirs(backup_dir, exist_ok=True)

        agora = datetime.now()

        # 🔹 Definir limite por tipo
        limites = {
            "diario": 30,       # 30 dias
            "fechamento": 60,   # 60 dias
            "reset": 365        # 1 ano
        }

        dias_maximos = limites.get(tipo, 30)

        # 💾 Criar backup
        data = agora.strftime("%Y-%m-%d_%H-%M")
        nome_backup = f"banco_{data}.db"
        destino = os.path.join(backup_dir, nome_backup)
        shutil.copy2(DB_PATH, destino)
        # ☁️ Backup na nuvem (OneDrive)
        if BACKUP_CLOUD_DIR:
            destino_cloud = os.path.join(BACKUP_CLOUD_DIR, nome_backup)
            shutil.copy2(DB_PATH, destino_cloud)

        # 🧹 Apagar backups antigos
        limite_timestamp = agora.timestamp() - (dias_maximos * 86400)

        for arquivo in os.listdir(backup_dir):
            caminho = os.path.join(backup_dir, arquivo)
            if os.path.isfile(caminho):
                if os.path.getmtime(caminho) < limite_timestamp:
                    os.remove(caminho)

    except Exception as e:
        print(f"Erro no backup ({tipo}): {e}")

def criar_banco():
    garantir_pasta_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela Clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        codigo_cadastro INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        data_nascimento TEXT NOT NULL,
        telefone TEXT,
        email TEXT NOT NULL UNIQUE,
        endereco TEXT
    )
    """)

    # Tabela pedidos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        codigo_cadastro INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT,
        detalhes TEXT,
        data TEXT NOT NULL,
        status TEXT,
        valor REAL
    )
    """)

    # Tabela Pagamentos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagamentos (
        codigo_cadastro INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_cliente TEXT NOT NULL,
        forma_pagamento TEXT NOT NULL,
        total REAL NOT NULL,
        data_pagamento TEXT NOT NULL,
        status_pagamento TEXT
    )
    """)

    #Pedidos por mês
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedido_mensal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano INTEGER,
            mes INTEGER,
            concluido REAL DEFAULT 0,
            cancelado REAL DEFAULT 0
        );
    """)

    #Faturamento Mensal
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faturamento_mensal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano INTEGER,
            mes INTEGER,
            total REAL DEFAULT 0
        );
    """)

    conn.commit()
    conn.close()

criar_banco()

def connect_to_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=FULL;")
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")
        return None

def connect_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=FULL;")
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")
        return None

def connect_db2():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=FULL;")
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")
        return None

class DashboardCanvas(FigureCanvas):
    def __init__(self):
        self.fig, self.axs = plt.subplots(2, 2, figsize=(10, 7))
        super().__init__(self.fig)
        self.plotar_painel()

    def salvar_pedidos_do_mes(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        agora = datetime.now()
        # Só executa no dia 01 de cada mês
        if agora.day != 1:
            conn.close()
            return
        # Determinar mês e ano ANTERIOR
        if agora.month == 1:  # Janeiro → pega Dezembro do ano anterior
            mes_anterior = 12
            ano_anterior = agora.year - 1
        else:
            mes_anterior = agora.month - 1
            ano_anterior = agora.year

        # Verifica se já foi salvo esse mês
        cursor.execute("""
            SELECT id FROM pedido_mensal
            WHERE mes = ? AND ano = ?
        """, (mes_anterior, ano_anterior))

        if cursor.fetchone():
            conn.close()
            return  # Já existe, não salva de novo

        # Calcular concluído/cancelado do mês anterior
        cursor.execute("""
            SELECT
                SUM(CASE WHEN status = 'Concluido' THEN valor ELSE 0 END),
                SUM(CASE WHEN status = 'Cancelado' THEN valor ELSE 0 END)
            FROM pedidos
            WHERE strftime('%m', data) = ?
              AND strftime('%Y', data) = ?
        """, (f"{mes_anterior:02d}", str(ano_anterior)))

        concluido, cancelado = cursor.fetchone()

        concluido = concluido if concluido else 0
        cancelado = cancelado if cancelado else 0

        # Inserir no pedido_mensal
        cursor.execute("""
            INSERT INTO pedido_mensal (ano, mes, concluido, cancelado)
            VALUES (?, ?, ?, ?)
        """, (ano_anterior, mes_anterior, concluido, cancelado))

        conn.commit()
        conn.close()

    def obter_vendas_por_produto(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                strftime('%Y', data) AS ano,
                strftime('%m', data) AS mes,
                tipo,
                COUNT(*)
            FROM pedidos
            GROUP BY ano, mes, tipo
            ORDER BY ano ASC, mes ASC
        """)

        dados = cursor.fetchall()
        conn.close()

        # Meses em português
        nomes_meses = {
            "01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun",
            "07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"
        }

        # Organizar estrutura
        vendas = {}
        tipos_produto = set()

        for ano, mes, tipo, qtd in dados:
            if mes is None:  # proteger caso o dado seja inválido
                continue
            mes_str = str(mes).zfill(2)  # garante "01", "02", ..., "12"
            label = f"{nomes_meses[mes_str]}/{ano}"
            tipos_produto.add(tipo)

            if label not in vendas:
                vendas[label] = {}

            vendas[label][tipo] = qtd

        tipos_produto = sorted(list(tipos_produto))
        meses = sorted(
            vendas.keys(),
            key=lambda m:  (
                int(m.split("/")[1]),
                list(nomes_meses.values()).index(m.split("/")[0])
            )
        )

        return meses, tipos_produto, vendas

    def obter_dados_pedidos(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                strftime('%Y', data) AS ano,
                strftime('%m', data) AS mes,
                SUM(CASE WHEN status = 'Concluido' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status = 'Cancelado' THEN 1 ELSE 0 END)
            FROM pedidos
            GROUP BY ano, mes
            ORDER BY ano ASC, mes ASC
        """)
        dados = cursor.fetchall()

        conn.close()

        nomes_meses = {
            "01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun",
            "07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"
        }

        meses = []
        concluidos = []
        cancelados = []

        for ano, mes, c, x in dados:
            if mes is None:  # proteger caso o dado seja inválido
                continue
            mes_str = str(mes).zfill(2)  # garante "01", "02", ..., "12"
            meses.append(f"{nomes_meses[mes_str]}/{ano}")
            concluidos.append(c)
            cancelados.append(x)

        return meses, concluidos, cancelados

    def obter_dados_pagamentos(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                strftime('%Y', data_pagamento) AS ano,
                strftime('%m', data_pagamento) AS mes,
                SUM(CASE WHEN status_pagamento = 'Pago' THEN total ELSE 0 END),
                SUM(CASE WHEN status_pagamento = 'Nao Pagou' THEN total ELSE 0 END),
                SUM(CASE WHEN status_pagamento = 'Pago' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status_pagamento = 'Nao Pagou' THEN 1 ELSE 0 END)
            FROM pagamentos
            GROUP BY ano, mes
            ORDER BY ano ASC, mes ASC
        """)
        dados = cursor.fetchall()

        nomes_meses = {
            "01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun",
            "07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"
        }

        meses = []
        faturado = []
        nao_pago = []
        pagos = []
        cancelados = []

        for ano, mes, f1, f2, q1, q2 in dados:
            if mes is None:  # proteger caso o dado seja inválido
                continue
            mes_str = str(mes).zfill(2)  # garante "01", "02", ..., "12"
            meses.append(f"{nomes_meses[mes_str]}/{ano}")
            faturado.append(f1)
            nao_pago.append(f2)
            pagos.append(q1)
            cancelados.append(q2)

         # Formas de Pagamento
        cursor.execute("""
            SELECT forma_pagamento, COUNT(*)
            FROM pagamentos
            GROUP BY forma_pagamento
        """)
        formas = dict(cursor.fetchall())

        conn.close()

        return meses, faturado, nao_pago, pagos, cancelados, formas

    def obter_produtos(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tipo, COUNT(*)
            FROM pedidos
            GROUP BY tipo
        """)

        dados = cursor.fetchall()
        conn.close()

        produtos = [linha[0] for linha in dados]
        quantidades = [linha[1] for linha in dados]

        return produtos, quantidades

    def plotar_painel(self):
        self.salvar_pedidos_do_mes()
        # Limpa o gráfico antes de atualizar
        for ax in self.axs.flat:
            ax.clear()
        # -------- PEDIDOS --------
        (meses_pedidos,
         status_concluido,
         status_cancelado) = self.obter_dados_pedidos()

        # -------- PAGAMENTOS --------
        (meses_pagamentos,
         faturamento_pago,
         faturamento_nao_pagou,
         pagamentos_concluidos,
         pagamentos_cancelados,
         formas_pagamento) = self.obter_dados_pagamentos()

        if not meses_pedidos and not meses_pagamentos:
            self.fig.suptitle("Nenhum dado encontrado no banco", fontsize=14)
            self.draw()
            return

        # ===== Gráfico de linha: faturamento mensal =====
        if meses_pagamentos and faturamento_pago and faturamento_nao_pagou:
            self.axs[1, 0].plot(meses_pagamentos, faturamento_pago, marker='o', label="Pago")
            self.axs[1, 0].plot(meses_pagamentos, faturamento_nao_pagou, marker='o', label="Não Pagou")
            self.axs[1, 0].set_title("Lucro Mensal (R$)")
            self.axs[1, 0].legend()
            self.axs[1, 0].grid(True, linestyle='--', alpha=0.6)
        else:
            self.axs[1, 0].text(0.5, 0.5, "Sem dados de pagamentos",
                            ha="center", va="center", fontsize=12)
            self.axs[1, 0].axis("off")

        # ===== Tabela: pedidos concluído e cancelado =====
        self.axs[0, 1].axis('off')
        colunas = ["Mês", "Concluídos", "Cancelados"]
        tabela_dados = list(zip(meses_pedidos, status_concluido, status_cancelado))

        if tabela_dados:
            tabela = self.axs[0, 1].table(
                cellText=tabela_dados,
                colLabels=colunas,
                loc='center',
                cellLoc='center'
            )
            tabela.scale(1.2, 1.4)

            # === Aplicar cores azul e branco ===
            for (row, col), cell in tabela.get_celld().items():
                if row == 0:
                # Cabeçalho
                    cell.set_facecolor("#0a65aa")
                    cell.set_text_props(weight='bold', color="white")
                elif row % 2 == 0:
                    # Linhas pares (segunda, quarta, etc.)
                    cell.set_facecolor("#e6f2ff")  # azul clarinho
                else:
                    # Linhas ímpares (terceira, quinta, etc.)
                    cell.set_facecolor("#ffffff")  # branco

        else:
            self.axs[0, 1].text(
                0.5, 0.5,
                "Nenhum dado encontrado",
                ha='center', va='center', fontsize=12
            )

        # ===== Gráfico de Pizza: formas de pagamento =====
        if formas_pagamento:
            self.axs[1, 1].pie(formas_pagamento.values(),
                               labels=formas_pagamento.keys(),
                               autopct="%1.0f%%",
                               startangle=90)
            self.axs[1, 1].set_title("Formas de Pagamento")
        else:
            self.axs[1, 1].text(0.5, 0.5, "Sem formas de pagamento registradas",
                            ha="center", va="center")
            self.axs[1, 1].axis("off")

        # ---- Gráfico de barras: Vendas por Produto ----
        meses, tipos_produto, vendas = self.obter_vendas_por_produto()
        ax = self.axs[0, 0]
        ax.set_title("Pedidos por Tipo (Separado por Mês)")

        if meses and tipos_produto:

            x = np.arange(len(meses))
            largura = 0.12  # largura de cada barra

            cmap = plt.get_cmap("tab20")
            cores = [cmap(i / len(tipos_produto)) for i in range(len(tipos_produto))]

            # Desenhar barras lado a lado
            for i, tipo in enumerate(tipos_produto):
                valores = []
                for mes in meses:
                    valores.append(vendas[mes].get(tipo, 0))

                ax.bar(x + i*largura, valores, width=largura, label=tipo, color=cores[i])

            ax.set_xticks(x + (len(tipos_produto)/2) * largura)
            ax.set_xticklabels(meses)
            ax.set_ylabel("Quantidade")
            ax.legend(ncol=2, fontsize=8)
            ax.grid(axis='y', linestyle='--', alpha=0.6)

        else:
            ax.text(0.5, 0.5, "Nenhum pedido registrado", ha='center', va='center', fontsize=12)
            ax.axis("off")

        self.fig.tight_layout()
        self.draw()
    def atualizar_dashboard(self):
        self.plotar_painel()

class MaskedDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, mask, parent=None):
        super(MaskedDelegate, self).__init__(parent)
        self.mask = mask

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QLineEdit(parent)
        editor.setInputMask(self.mask)  # Aplica a máscara
        return editor

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # 🔥 Conectar botão corretamente
        self.ui.btn_restaurar.clicked.connect(self.restaurar_backup)

        self.iniciar_backup_automatico()

    def iniciar_backup_automatico(self):
        self.timer_backup = QTimer(self)
        self.timer_backup.timeout.connect(self.backup_automatico)
        self.timer_backup.start(30 * 60 * 1000)  # 30 minutos

    def backup_automatico(self):
        try:
            conn = connect_to_db()
            conn.commit()
            conn.close()

            fazer_backup(DB_PATH, tipo="diario")
        except Exception as e:
            print("Erro no backup automático:", e)

    def closeEvent(self, event):
        try:
            conn = connect_to_db()
            conn.commit()
            conn.close()

            fazer_backup(DB_PATH, tipo="fechamento")
        except Exception as e:
            print("Erro no backup ao fechar:", e)
        event.accept()

    def restaurar_backup(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import shutil

        pasta_backup = os.path.join(os.path.dirname(DB_PATH), "backups")

        if not os.path.exists(pasta_backup):
            QMessageBox.warning(self, "Erro", "Nenhum backup encontrado.")
            return

        arquivo_backup, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Backup",
            pasta_backup,
            "Arquivos DB (*.db)"
        )

        if not arquivo_backup:
            return

        confirmacao = QMessageBox.question(
            self,
            "Confirmar Restauração",
            "Tem certeza que deseja restaurar este backup?\nO banco atual será substituído.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmacao == QMessageBox.Yes:
            try:
                # Fecha conexão ativa
                conn = connect_to_db()
                conn.close()

                # Backup emergencial antes de restaurar
                backup_emergencial = DB_PATH.replace(".db", "_antes_restaurar.db")
                shutil.copy2(DB_PATH, backup_emergencial)

                # Restaurar arquivo escolhido
                shutil.copy2(arquivo_backup, DB_PATH)

                QMessageBox.information(
                    self,
                    "Sucesso",
                    "Backup restaurado com sucesso.\nReinicie o sistema."
                )
                # Fecha o sistema
                QApplication.quit()

                # Reabre automaticamente
                QtCore.QProcess.startDetached(sys.executable, sys.argv)

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao restaurar:\n{e}")

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Programa Vila Planalto")
        MainWindow.resize(1350, 700)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        MainWindow.setFont(font)
        MainWindow.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,"
                                 "stop:0 rgba(255, 255, 255, 255),"
                                 "stop:1 rgba(255, 182, 193, 255))")

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Criando o layout principal da janela
        layout_central = QtWidgets.QVBoxLayout(self.centralwidget)

        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout_central.addWidget(self.tabWidget)

        # Aba 1 - Relatórios
        self.tab_relatorios = QtWidgets.QWidget()
        self.tab_relatorios.setObjectName("tab_relatorios")
        self.tabWidget.addTab(self.tab_relatorios, "Relatórios")
        # Layout principal da aba Relatórios
        self.layout_relatorios = QtWidgets.QVBoxLayout(self.tab_relatorios)
        self.widget_dashboard = DashboardCanvas()
        self.layout_relatorios.addWidget(self.widget_dashboard)

        # BOTÃO RESTAURAR BACKUP
        # ===============================
        top_bar = QtWidgets.QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 5)

        top_bar.addStretch()  # empurra botão para direita

        self.btn_restaurar = QtWidgets.QPushButton("Restaurar Backup")
        self.btn_restaurar.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_restaurar.setFixedHeight(28)
        self.btn_restaurar.setMaximumWidth(170)

        self.btn_restaurar.setStyleSheet("""
            QPushButton {
                background-color: #8634eb;
                color: white;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #eb34a8;
            }
        """)

        # Conectar ao método da MainWindow
        top_bar.addWidget(self.btn_restaurar)

        # adiciona a barra antes do conteúdo principal
        self.layout_relatorios.addLayout(top_bar)

        # Atualiza dashboard automaticamente a cada 1 segundos
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.widget_dashboard.atualizar_dashboard)
        self.timer.start(1800000) # = 30 minutos

        # Aba 2 - Clientes
        self.tab_clientes = QtWidgets.QWidget()
        self.tab_clientes.setObjectName("tab_clientes")
        self.setup_cliente_ui(self.tab_clientes)
        self.tabWidget.addTab(self.tab_clientes, "Clientes")

        # Aba 3 - Pedidos
        self.tab_pedidos = QtWidgets.QWidget()
        self.tab_pedidos.setObjectName("tab_pedidos")
        self.setup_pedido_ui(self.tab_pedidos)
        self.tabWidget.addTab(self.tab_pedidos, "Pedidos")

        # Aba 4 - Pagamentos
        self.tab_pagamentos = QtWidgets.QWidget()
        self.tab_pagamentos.setObjectName("tab_pagamentos")
        self.setup_pagamento_ui(self.tab_pagamentos)
        self.tabWidget.addTab(self.tab_pagamentos, "Pagamentos")

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        MainWindow.setMenuBar(self.menubar)
        self.menubar.setStyleSheet("""
    QMenuBar {
        font-weight: bold;   /* negrito */
        font-size: 11pt;     /* tamanho da letra maior */
    }
    QMenuBar::item {
        spacing: 10px;
        padding: 5px 15px;
        background: transparent;
    }
    QMenuBar::item:selected {
        background: rgba(200, 200, 200, 50);
    }
""")

    def setup_cliente_ui(self, parent):
        layout_clientes = QtWidgets.QVBoxLayout(parent)
        font_label = QtGui.QFont()
        font_label.setPointSize(12)
        font_label.setBold(True)
        font_label.setWeight(75)

        # Criando o QTabWidget para as sub-abas dentro da aba de "Clientes"
        self.tabClientesSub = QtWidgets.QTabWidget(parent)
        self.tabClientesSub.setObjectName("tabClientesSub")
        layout_clientes.addWidget(self.tabClientesSub)

        # Sub-aba 1 - Formulário de Cadastro de Cliente
        self.tab_cliente_form = QtWidgets.QWidget()
        self.tab_cliente_form.setObjectName("tab_cliente_form")
        self.setup_cliente_form(self.tab_cliente_form)
        self.tabClientesSub.addTab(self.tab_cliente_form, "Cadastro")

        # Sub-aba 2 - Lista de Clientes
        self.tab_clientes_lista = QtWidgets.QWidget()
        self.tab_clientes_lista.setObjectName("tab_clientes_lista")
        self.setup_table(self.tab_clientes_lista)
        self.tabClientesSub.addTab(
            self.tab_clientes_lista, "Lista de Clientes")

    def setup_cliente_form(self, parent):
        parent.setStyleSheet("""
    background-color: #F0A8C0;
""")
        font_label = QtGui.QFont()
        font_label.setPointSize(12)
        font_label.setBold(True)
        font_label.setWeight(75)

        # Criando um layout vertical para centralizar os campos
        layout = QtWidgets.QVBoxLayout()

        # Centralizando o formulário de cadastro
        form_layout = QtWidgets.QFormLayout()

        # Label "Nome"
        self.label_nome = QtWidgets.QLabel(parent)
        self.label_nome.setText("Nome do Cliente")
        self.label_nome.setFont(font_label)
        self.label_nome.setStyleSheet("font-size: 16pt; font-weight: bold; color: black; background: transparent;")
        self.label_nome.setGeometry(QtCore.QRect(70, 110, 300, 30))
        self.label_nome.setObjectName("label_nome")

        # Campo de texto Nome
        self.Nome = QtWidgets.QLineEdit(parent)
        self.Nome.setFont(font_label)
        self.Nome.setStyleSheet("""
             QLineEdit {
          background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }
         """)
        self.Nome.setGeometry(QtCore.QRect(70, 150, 891, 51))
        self.Nome.setObjectName("Nome")

        self.label_data_nascimento = QtWidgets.QLabel(parent)
        self.label_data_nascimento.setText("Data de Nascimento")
        self.label_data_nascimento.setFont(font_label)
        self.label_data_nascimento.setStyleSheet("font-size: 16pt; font-weight: bold; color: black; background: transparent;")
        # andar para o lado...para cima e para baixo....efeito sanfona e grossura
        self.label_data_nascimento.setGeometry(QtCore.QRect(1300, 110, 244, 20))
        self.label_data_nascimento.setObjectName("label_data_nascimento")

        # Data de nascimento
        self.Data_nascimento = QtWidgets.QLineEdit(parent)
        self.Data_nascimento.setFont(font_label)
        self.Data_nascimento.setStyleSheet("""
             QLineEdit {
          background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }
         """)
        self.Data_nascimento.setInputMask("00/00/0000")
        self.Data_nascimento.setAlignment(QtCore.Qt.AlignCenter)
        self.Data_nascimento.setObjectName("Data_nascimento")
        # andar para o lado...para cima e para baixo....efeito sanfona e grossura
        self.Data_nascimento.setGeometry(QtCore.QRect(1300, 150, 261, 51))

        self.label_email = QtWidgets.QLabel(parent)
        self.label_email.setText("Email")
        self.label_email.setFont(font_label)
        self.label_email.setStyleSheet("font-size: 16pt; font-weight: bold; color: black; background: transparent;")
        self.label_email.setGeometry(QtCore.QRect(70, 246, 80, 30))
        self.label_email.setObjectName("label_email")

        # Email
        self.Email = QtWidgets.QLineEdit(parent)
        self.Email.setFont(font_label)
        self.Email.setStyleSheet("""
             QLineEdit {
          background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }
         """)
        self.Email.setObjectName("Email")
        # andar para o lado...para cima e para baixo....efeito sanfona e grossura
        self.Email.setGeometry(QtCore.QRect(70, 286, 891, 51))

        self.label_telefone = QtWidgets.QLabel(parent)
        self.label_telefone.setText("Telefone")
        self.label_telefone.setStyleSheet("font-size: 16pt; font-weight: bold; color: black; background: transparent;")
        self.label_telefone.setFont(font_label)
        self.label_telefone.setGeometry(QtCore.QRect(1300, 240, 180, 30))
        self.label_telefone.setObjectName("label_telefone")

        # Telefone
        self.Telefone = QtWidgets.QLineEdit(parent)
        self.Telefone.setFont(font_label)
        self.Telefone.setStyleSheet("""
             QLineEdit {
          background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }
         """)
        self.Telefone.setInputMask("(00) 00000-0000")
        self.Telefone.setAlignment(QtCore.Qt.AlignCenter)
        self.Telefone.setObjectName("Telefone")
        # andar para o lado...para cima e para baixo....efeito sanfona e grossura
        self.Telefone.setGeometry(QtCore.QRect(1300, 280, 261, 51))

        self.label_endereco = QtWidgets.QLabel(parent)
        self.label_endereco.setText("Endereço")
        self.label_endereco.setFont(font_label)
        self.label_endereco.setStyleSheet("font-size: 16pt; font-weight: bold; color: black; background: transparent;")
        self.label_endereco.setGeometry(QtCore.QRect(480, 560, 120, 40))
        self.label_endereco.setObjectName("label_endereco")

        # Endereço
        self.Endereco = QtWidgets.QLineEdit(parent)
        self.Endereco.setFont(font_label)
        self.Endereco.setStyleSheet("""
             QLineEdit {
          background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }
         """)
        self.Endereco.setObjectName("Endereco")
        # andar para o lado...para cima e para baixo....efeito sanfona e grossura
        self.Endereco.setGeometry(QtCore.QRect(480, 600, 921, 51))

        # Adicionando o formulário ao layout principal
        layout.addLayout(form_layout)

        # Botão de Ação OK/CANCELAR
        self.buttonBox2 = QtWidgets.QDialogButtonBox(parent)
        self.buttonBox2.setGeometry(QtCore.QRect(750, 700, 440, 61))
        self.buttonBox2.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.buttonBox2.setStyleSheet("""
            QDialogButtonBox {
                border: 2px solid rgba(139, 0, 139, 200);
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 150);
                padding: 5px;
            }
            QDialogButtonBox QPushButton {
                min-width: 40px;          /* largura mínima */
                min-height: 20px;          /* altura mínima */
                font-size: 14pt;           /* texto maior */
                font-weight: bold;         /* texto mais forte */
            }
            QDialogButtonBox::button {
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: rgba(255, 255, 255, 200);
                color: rgba(139, 0, 139, 200);
            }
        """)
        self.buttonBox2.setStandardButtons(
            QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox2.setCenterButtons(True)
        self.buttonBox2.setObjectName("buttonBox2")
        # Conecta o botão à função de salvar
        self.buttonBox2.button(
            QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.save_data)

        self.buttonBox2.button(
            QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reset_fields)

        # Navegação entre Campos
        self.Nome.returnPressed.connect(self.Data_nascimento.setFocus)
        self.Data_nascimento.returnPressed.connect(self.Email.setFocus)
        self.Email.returnPressed.connect(self.Telefone.setFocus)
        self.Telefone.returnPressed.connect(self.Endereco.setFocus)

        self.resetButton = QtWidgets.QPushButton("Resetar IDs", parent)
        self.resetButton.setGeometry(QtCore.QRect(1700, 80, 90, 30))
        self.label_resetButton = QtWidgets.QLabel(parent)
        self.label_resetButton.setText("Zerar a tabela de Clientes")
        self.label_resetButton.setFont(font_label)
        self.label_resetButton.setStyleSheet("font-size: 12pt; font-weight: bold; color: black; background: transparent;")
        self.label_resetButton.setGeometry(QtCore.QRect(1640, 20, 400, 40))
        self.label_resetButton.setObjectName("label_resetButton")
        self.resetButton.clicked.connect(self.resetar_tabela_e_ids)

    def setup_table(self, parent):
        # Barra de Pesquisa e legenda
        layout_clientes = QtWidgets.QVBoxLayout(parent)
        self.search_box = QtWidgets.QLineEdit()
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.search_box.setFont(font)
        self.search_box.setAccessibleDescription("")
        self.search_box.setStyleSheet("font-size: 14pt;")
        self.search_box.setStyleSheet("""
    QLineEdit {
        background-color: white;
        border: 2px solid #ffb6c1; /* Rosa claro */
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 14pt;
        color: #333;
    }
    QLineEdit:focus {
        border: 2px solid #ff69b4; /* Rosa mais forte no foco */
    }
""")
        self.search_box.setInputMask("")
        self.search_box.setPlaceholderText("Pesquisar....")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setObjectName("search_box")
        self.search_box.setMinimumHeight(40)  # Mais grossa

        # Conectar, fazer a busca enquanto digita
        self.search_box.textChanged.connect(self.search_data)
        self.tabWidget.setCurrentIndex(0)

        # Criar QTableWidget para exibir clientes
        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setGeometry(QtCore.QRect(70, 60, 1000, 420))
        # 5 colunas para Nome, Nascimento, Telefone, E-mail e Endereço
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels(
            ["Código de Cadastro", "Nome", "Data de Nascimento",
             "Telefone", "E-mail", "Endereço"])
        self.tableWidget.setObjectName("Tabela de Clientes")
        self.tableWidget.horizontalHeader().setMinimumHeight(30)

        layout_clientes.addWidget(self.search_box)
        layout_clientes.addWidget(self.tableWidget)

        # Aplicar delegados para as máscaras de data e telefone
        telefone_delegate = MaskedDelegate("(00) 00000-0000", self.tableWidget)
        data_delegate = MaskedDelegate("00/00/0000", self.tableWidget)

        self.tableWidget.setItemDelegateForColumn(
            2, data_delegate)  # Data
        self.tableWidget.setItemDelegateForColumn(
            3, telefone_delegate)  # Telefone

        # Definir fonte em negrito para os cabeçalhos
        header_font = QtGui.QFont()
        header_font.setBold(True)

        for col in range(self.tableWidget.columnCount()):
            item = self.tableWidget.horizontalHeaderItem(col)
            if item:
                item.setFont(header_font)
        # Defina a política de redimensionamento da tabela
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch)

        self.load_data()
        # Conectar ao método para atualizar o banco
        self.tableWidget.itemChanged.connect(self.update_database_from_table)

        # Layout para o botão de excluir
        layout_clientes = QtWidgets.QVBoxLayout()
        self.buttonBox_delete = QtWidgets.QPushButton(
            "Excluir Cliente", parent)
        self.buttonBox_delete.setGeometry(QtCore.QRect(1760, 8, 108, 41))
        self.buttonBox_delete.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.buttonBox_delete.setStyleSheet("""
    QPushButton {
        background-color: #ff4d4d;   /* Vermelho claro */
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #e60000;  /* Vermelho mais escuro no hover */
    }
""")
        self.buttonBox_delete.clicked.connect(self.delete_order)
        self.buttonBox_delete.setVisible(False)  #escondido
        layout_clientes.addWidget(self.buttonBox_delete)


        # Definir fonte em negrito
        font = QtGui.QFont()
        font.setBold(True)
        self.buttonBox_delete.setFont(font)

        # Conectar a função de seleção de linha
        self.tableWidget.itemSelectionChanged.connect(self.show_delete_button)

        # Conectar o evento de clique fora da tabela
        parent.mousePressEvent = self.mouse_press_event
        self.tabClientesSub.currentChanged.connect(self.on_tab_changed)
        self.tableWidget.cellClicked.connect(self.on_table_cell_clicked)
        layout_clientes.addWidget(self.buttonBox_delete)

    def show_delete_button(self):
        if self.tableWidget.currentRow() >= 0:
            self.buttonBox_delete.setVisible(True)
        else:
            self.buttonBox_delete.setVisible(False)

    def search_data(self):
        search_term = self.search_box.text().lower().strip()
        self.tableWidget.setSortingEnabled(False)
        for row in range(self.tableWidget.rowCount()):
            # Pega o valor da coluna "Nome"
            item_nome = self.tableWidget.item(row, 1)
            item_data_nascimento = self.tableWidget.item(row, 2)
            if ((item_nome is not None and search_term in item_nome.text().lower()) or
                (item_data_nascimento is not None and search_term in item_data_nascimento.text().lower())):
                self.tableWidget.showRow(row)  # Mostra a linha correspondente
            else:
                # Esconde a linha que não corresponde
                self.tableWidget.hideRow(row)

    def on_tab_changed(self, index):
        current_tab = self.tabClientesSub.widget(index)
        if current_tab != self.tab_clientes_lista:
            self.buttonBox_delete.setVisible(False)

    def on_table_cell_clicked(self, row, column):
        self.buttonBox_delete.setVisible(True)

    # Evento de clique
    def mouse_press_event(self, event):
        if self.tabClientesSub.currentWidget() == self.tab_clientes_lista:
            if not self.tableWidget.viewport().rect().contains(self.tableWidget.mapFromParent(event.pos())):
                self.buttonBox_delete.setVisible(False)
                self.tableWidget.clearSelection()

    def reset_fields(self):
        # Reseta todos os campos do formulário
        self.Nome.clear()
        self.Data_nascimento.clear()
        self.Telefone.clear()
        self.Email.clear()
        self.Endereco.clear()

    def save_data(self):
        """Salva os dados no banco de dados"""
        # Obter valores dos campos
        nome = self.Nome.text()
        data_nascimento = self.Data_nascimento.text()
        telefone = self.Telefone.text()
        email = self.Email.text()
        endereco = self.Endereco.text()


        if not nome or not email:  # Validar campos obrigatórios
            QtWidgets.QMessageBox.warning(
                None, "Aviso", "Nome e Email são obrigatórios!")
            return

        # Conectar ao banco de dados usando a função `connect_to_db`
        connection = connect_to_db()
        if not connection:
            QtWidgets.QMessageBox.critical(
                None, "Erro", "Não foi possível conectar ao banco de dados.")
            return

        try:
            # Inicializar cursor
            cursor = connection.cursor()
            query = """
            INSERT INTO clientes (nome, data_nascimento,
            telefone, email, endereco)
            VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(query, (nome, data_nascimento,
                                   telefone, email, endereco))
            codigo_cadastro = cursor.lastrowid
            connection.commit()

            try:
                self.widget_dashboard.atualizar_dashboard()
            except:
                pass

            QMessageBox.information(None, "Sucesso", "Cliente cadastrado com sucesso!")
        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Erro ao salvar dados: {e}")
        finally:
            cursor.close()
            connection.close()


        row_position = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_position)
        self.tableWidget.setItem(
            row_position, 0, QtWidgets.QTableWidgetItem(str(codigo_cadastro).zfill(4)))
        self.tableWidget.setItem(
            row_position, 1, QtWidgets.QTableWidgetItem(self.Nome.text()))
        self.tableWidget.setItem(
            row_position, 2, QtWidgets.QTableWidgetItem(self.Data_nascimento.text()))
        # Telefone com máscara
        telefone = self.Telefone.text()
        self.tableWidget.setItem(
            row_position, 3, QtWidgets.QTableWidgetItem(telefone))  # Corrigido
        self.tableWidget.setItem(
            row_position, 4, QtWidgets.QTableWidgetItem(self.Email.text()))
        self.tableWidget.setItem(
            row_position, 5, QtWidgets.QTableWidgetItem(self.Endereco.text()))

        self.clear_fields()

        # Criar a fonte mais grossa (bold)
        bold_font = QtGui.QFont()
        bold_font.setBold(True)

    def load_data(self):
        conn = connect_to_db()
        cursor = conn.cursor()
        try:
            self.tableWidget.setRowCount(0)
            cursor.execute(
                "SELECT codigo_cadastro, "
                "nome, data_nascimento, telefone, email, "
                "endereco "
                "FROM CLIENTES ORDER BY codigo_cadastro ASC"
            )
            rows = cursor.fetchall()

            # Adiciona os dados na tabela da interface
            self.tableWidget.setRowCount(len(rows))
            # Desativa a ordenação automática antes de carregar
            self.tableWidget.setSortingEnabled(False)
            for row_index, row_data in enumerate(rows):
                for col_index, col_data in enumerate(row_data):
                    if col_index == 0 and col_data:
                        formatted_code = str(col_data).zfill(4)
                        print(f"Codigo Formatado: {formatted_code}")

                    # Verifica se a coluna é de data e formata
                    if col_index == 2 and col_data:
                        try:
                            # Converte a data para o formato DD/MM/YYYY
                            col_data = datetime.strptime(
                                str(col_data), "%Y-%m-%d").strftime("%d/%m/%Y")
                        except ValueError:
                            col_data = "Data Inválida"  # Fallback para casos de erro
                    item = QtWidgets.QTableWidgetItem(str(col_data))
                    self.tableWidget.setItem(
                        row_index, col_index, item)

                    # Adiciona o item à célula correspondente
                    for row in range(self.tableWidget.rowCount()):
                        item = self.tableWidget.item(
                            row, 0)  # Coluna do código
                        if item:
                            # Aplica a formatação final
                            item.setText(item.text().zfill(4))

        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
        finally:
            cursor.close()
            conn.close()

    def update_database_from_table(self, item):
        """Atualiza o banco de dados com as alterações feitas na tabela."""
        try:
            from datetime import datetime

            # Desabilitar a ordenação antes de editar
            self.tableWidget.setSortingEnabled(False)

            # Obter a linha, coluna e novo valor
            row = item.row()
            column = item.column()
            new_value = item.text()

            if column == 0:
                return

            # Mapear as colunas do banco p/ colunas QTableWidget
            column_mapping = {
                0: "codigo_cadastro",
                1: "nome",
                2: "data_nascimento",
                3: "telefone",
                4: "email",
                5: "endereco",
            }

            # Obter o nome da coluna correspondente no banco de dados
            column_name = column_mapping.get(column, None)
            if not column_name:
                return  # Ignorar colunas sem mapeamento
            # identificador único
            codigo_item = self.tableWidget.item(row, 0)
            if not codigo_item:
                return
            # Garante que o código tenha 4 dígitos, se for necessário
            codigo = int(codigo_item.text())

            # Atualizar o banco de dados
            conn = connect_to_db()
            if not conn:
                return
            cursor = conn.cursor()

            if column == 2:  # Coluna de data
                try:
                    if "-" in new_value:  # Formato ISO (YYYY-MM-DD)
                        dt = datetime.strptime(new_value, "%Y-%m-%d")
                    else:  # Formato esperado (DD/MM/YYYY)
                        dt = datetime.strptime(new_value, "%d/%m/%Y")
                    db_value = dt.strftime("%Y-%m-%d")
                    formatted_date = dt.strftime("%d/%m/%Y")
                    item.setText(formatted_date)
                    cursor.execute(
                        f"UPDATE clientes SET {column_name} = ? WHERE codigo_cadastro = ?",
                        (db_value, codigo)
                    )
                    conn.commit()
                except ValueError:
                    QtWidgets.QMessageBox.warning(
                        None,
                        "Erro",
                        "Formato de data inválido. Use DD/MM/YYYY.",
                        buttons=QtWidgets.QMessageBox.Ok
                    )
                    return
            else:
                # Atualizar outras colunas
                cursor.execute(
                    f"UPDATE clientes SET {column_name} = ? WHERE codigo_cadastro = ?",
                    (new_value, codigo)
                )
                conn.commit()
                try:
                    self.widget_dashboard.atualizar_dashboard()
                except:
                    pass

        except ValueError as ve:
            QtWidgets.QMessageBox.warning(
                None,
                "Erro",
                f"Erro de valor: {ve}",
                buttons=QtWidgets.QMessageBox.Ok
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                None,
                "Erro",
                f"Erro ao atualizar o banco: {e}",
                buttons=QtWidgets.QMessageBox.Ok
            )
        finally:
            # Garantir que a ordenação permaneça desativada
            self.tableWidget.setSortingEnabled(False)
            if 'cursor' in locals() and cursor:
                cursor.close()

    def clear_fields(self):
        """Limpa os campos do formulário."""
        self.Nome.clear()
        self.Data_nascimento.clear()
        self.Telefone.clear()
        self.Email.clear()
        self.Endereco.clear()

    def delete_order(self):
        """Exclui o(s) cliente(s) selecionado(s) do banco de dados e atualiza a tabela."""
        selected_rows = sorted(
            set(item.row() for item in self.tableWidget.selectedItems()), reverse=True
        )

        if not selected_rows:
            QtWidgets.QMessageBox.warning(
                None, "Aviso", "Nenhum cliente selecionado!")
            return

            # Criar caixa de diálogo de confirmação
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Question)
        msg_box.setWindowTitle("Confirmação")
        msg_box.setText(
            "Tem certeza que deseja excluir o(s) cliente(s) selecionado(s)?")

        # Criar botões personalizados
        btn_sim = msg_box.addButton("Sim", QtWidgets.QMessageBox.YesRole)
        btn_cancelar = msg_box.addButton(
            "Cancelar", QtWidgets.QMessageBox.RejectRole)

        msg_box.exec()  # Exibir a caixa de diálogo

        # Se o usuário pressionar "Cancelar", interrompe a função
        if msg_box.clickedButton() == btn_cancelar:
            return

        conn = connect_to_db()
        if not conn:
            QtWidgets.QMessageBox.critical(
                None, "Erro", "Falha ao conectar ao banco de dados.")
            return

        try:
            cursor = conn.cursor()
            fazer_backup(DB_PATH, tipo="diario")
            for row in selected_rows:
                # Obtenha o nome do cliente para exclusão
                # Assumindo que o nome está na coluna 0
                codigo_cliente = self.tableWidget.item(row, 0).text()
                cursor.execute(
                    "DELETE FROM clientes WHERE codigo_cadastro = ?", (codigo_cliente,))

            conn.commit()
            try:
                self.widget_dashboard.atualizar_dashboard()
            except:
                pass
            QtWidgets.QMessageBox.information(
                None, "Sucesso", "Cliente(s) excluído(s) com sucesso!")

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                None, "Erro", f"Erro ao excluir cliente(s): {e}")
        finally:
            conn.close()

        # Recarregar a tabela para garantir consistência
        self.load_data()

    def resetar_tabela_e_ids(self):
        from datetime import datetime, date
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Confirmar Reset")
        msg_box.setText("Quer apagar TODOS os clientes e resetar os IDs clique em 'Yes', "
                        "quer apenas gerar relatorio clique em 'No'")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

        # Aumentar tamanho da fonte
        font = QFont()
        font.setPointSize(14)  # Aqui você pode aumentar ainda mais
        msg_box.setFont(font)
        resposta = msg_box.exec_()

        if resposta == QMessageBox.Cancel:
            return  # Sai da função

        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute("SELECT codigo_cadastro, nome, data_nascimento, telefone, email, endereco FROM clientes")
        dados = cursor.fetchall()

        if not dados:
            QMessageBox.information(None, "Aviso", "Não há dados para gerar o relatório.")
        else:
            # === 1️⃣ Formatar datas no padrão dd/mm/aaaa ===
            dados_formatados = []
            for linha in dados:
                codigo, nome, data_nascimento, telefone, email, endereco = linha

                # Converter "2000-05-14" → "14/05/2000"
                if isinstance(data_nascimento, (datetime, date)):
                    data_formatada = data_nascimento.strftime("%d/%m/%Y")
                else:
                    try:
                       data_formatada = datetime.strptime(str(data_nascimento), "%Y-%m-%d").strftime("%d/%m/%Y")
                    except Exception:
                        data_formatada = str(data_nascimento)  # Se já estiver formatada

                dados_formatados.append([
                    codigo, nome, data_formatada, telefone, email, endereco
                ])

            # === 2️⃣ Criar o relatório ===
            from datetime import datetime
            import pandas as pd
            import os
            from PyQt5.QtGui import QDesktopServices
            from PyQt5.QtCore import QUrl
            from openpyxl.styles import Font, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            meses = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
            agora = datetime.now()
            mes_atual = f"{meses[agora.month]} de {agora.year}"

            colunas = ["Código", "Nome", "Nascimento", "Telefone", "E-mail", "Endereço"]

            # === 🔧 Quebrar textos muito longos (endereços, emails, etc.) ===
            dados_ajustados = []
            for linha in dados_formatados:
                codigo, nome, nascimento, telefone, email, endereco = linha

                dados_ajustados.append([
                    codigo,
                    "\n".join(textwrap.wrap(str(nome), 40)),
                    nascimento,
                    telefone,
                    "\n".join(textwrap.wrap(str(email), 40)),
                    "\n".join(textwrap.wrap(str(endereco), 50))
                ])
            df = pd.DataFrame(dados_ajustados, columns=colunas)

            # === 3️⃣ Criar pasta "Relatórios" na Área de Trabalho ===
            desktop = os.path.join(os.environ["USERPROFILE"], "OneDrive", "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")

            pasta = os.path.join(desktop, "Relatórios")
            os.makedirs(pasta, exist_ok=True)
            caminho_arquivo = os.path.join(pasta, f"Relatorio_Clientes_{mes_atual}.xlsx"
            )

            with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Clientes")

                workbook = writer.book
                worksheet = writer.sheets["Clientes"]
                # Estilos
                header_font = Font(bold=True)
                center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
                text_align = Alignment(vertical="top", wrap_text=True)

                thin_border = Border(
                    left=Side(style="thin"),
                    right=Side(style="thin"),
                    top=Side(style="thin"),
                    bottom=Side(style="thin")
                )

                # Cabeçalho
                for col_num, coluna in enumerate(colunas, start=1):
                    cell = worksheet.cell(row=1, column=col_num)
                    cell.value = coluna
                    cell.font = header_font
                    cell.alignment = center_align
                    cell.border = thin_border

                    # largura da coluna
                    worksheet.column_dimensions[get_column_letter(col_num)].width = 25

                # Dados
                for row in worksheet.iter_rows(
                    min_row=2,
                    max_row=worksheet.max_row,
                    min_col=1,
                    max_col=len(colunas)
                ):
                    for cell in row:
                        cell.alignment = text_align
                        cell.border = thin_border

                # Congelar cabeçalho
                worksheet.freeze_panes = "A2"
                # Autofiltro
                worksheet.auto_filter.ref = f"A1:{get_column_letter(len(colunas))}{worksheet.max_row}"

            QDesktopServices.openUrl(QUrl.fromLocalFile(caminho_arquivo))

            QMessageBox.information(
                None,
                "Relatório Gerado",
                f"Relatório gerado e aberto no Excel:\n\n{caminho_arquivo}"
            )

        # === 4️⃣ Resetar a tabela e IDs ===
        if resposta == QMessageBox.Yes:
            try:
                conn.commit()
                conn.close()

                fazer_backup(DB_PATH, tipo="reset")

                conn = connect_to_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM clientes;")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='clientes';")
                conn.commit()
                QMessageBox.information(None, "Resetado com Sucesso",
                                        "Todos os dados foram apagados e os IDs resetados para 1.")
            except Exception as e:
                QMessageBox.critical(None, "Erro", f"Ocorreu um erro ao resetar os dados: {str(e)}")
            finally:
                cursor.close()
                conn.close()
                self.load_data()
                self.tableWidget.setRowCount(0)
                try:
                    self.widget_dashboard.atualizar_dashboard()
                except:
                    pass

    def setup_pedido_ui(self, parent):
        layout_pedidos = QtWidgets.QVBoxLayout(parent)
        font_label = QtGui.QFont()
        font_label.setPointSize(12)
        font_label.setBold(True)
        font_label.setWeight(75)

        # Criando o QTabWidget para as sub-abas
        self.tabPedidosSub = QtWidgets.QTabWidget(parent)
        self.tabPedidosSub.setObjectName("tabPedidosSub")
        layout_pedidos.addWidget(self.tabPedidosSub)

        # Sub-aba 1 - Formulário de Cadastro de pedidos
        self.tab_pedido_form = QtWidgets.QWidget()
        self.tab_pedido_form.setObjectName("tab_pedido_form")
        self.setup_pedido_form(self.tab_pedido_form)
        self.tabPedidosSub.addTab(self.tab_pedido_form, "Cadastro")

        # Sub-aba 2 - Lista de pedidos
        self.tab_pedidos_lista = QtWidgets.QWidget()
        self.tab_pedidos_lista.setObjectName("tab_pedidos_lista")
        self.setup_table2(self.tab_pedidos_lista)
        self.tabPedidosSub.addTab(
            self.tab_pedidos_lista, "Lista de Pedidos")

    def setup_pedido_form(self, parent):
        parent.setStyleSheet("""
    background-color: #F0A8C0;
    """)
        font_label = QtGui.QFont()
        font_label.setPointSize(12)
        font_label.setBold(True)
        font_label.setWeight(75)

        # Criando um layout vertical para centralizar os campos
        layout = QtWidgets.QVBoxLayout()

        # Centralizando o formulário de cadastro
        form_layout = QtWidgets.QFormLayout()

        # Label "Nome"
        self.label_nome2 = QtWidgets.QLabel(parent)
        self.label_nome2.setText("Nome do Cliente")
        self.label_nome2.setFont(font_label)
        self.label_nome2.setStyleSheet("font-size: 16pt; font-weight: bold; color: black; background: transparent;")
        self.label_nome2.setGeometry(QtCore.QRect(70, 160, 200, 20))
        self.label_nome2.setObjectName("label_nome2")

        # Campo de texto Nome
        self.Nome2 = QtWidgets.QLineEdit(parent)
        self.Nome2.setFont(font_label)
        self.Nome2.setStyleSheet("""
             QLineEdit {
          background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }
         """)
        self.Nome2.setObjectName("Nome do Cliente")
        self.Nome2.setGeometry(QtCore.QRect(70, 200, 891, 51))

        # ComboBox Comida
        self.Comida = QtWidgets.QComboBox(parent)
        self.Comida.setFont(font_label)
        self.Comida.setObjectName("Comida")
        self.Comida.setEditable(True)
        self.Comida.setGeometry(QtCore.QRect(1350, 210, 261, 41))
        self.Comida.setStyleSheet("""
    QComboBox {
        background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }

    QComboBox QAbstractItemView {
        background-color: white;
        border: none;
        selection-background-color: #8B008B;  /* roxinho da sua paleta */
        selection-color: white;
        font-size: 14pt;
    }
""")
        self.carregar_item()

                # Botão para adicionar item
        self.addButton = QtWidgets.QPushButton(parent)
        self.addButton.setGeometry(QtCore.QRect(1440, 150, 30, 30))
        self.addButton.setText("✔️")
        self.addButton.clicked.connect(self.adicionar_item)
        self.addButton.setVisible(True)

        # Botão para remover item
        self.removeButton = QtWidgets.QPushButton(parent)
        self.removeButton.setGeometry(QtCore.QRect(1480, 150, 30, 30))
        self.removeButton.setText("❌")
        self.removeButton.clicked.connect(self.remover_item)
        self.removeButton.setVisible(True)

        # ComboBox Status
        self.Status = QtWidgets.QComboBox(parent)
        self.Status.setFont(font_label)
        self.Status.setObjectName("Status")
        self.Status.setGeometry(QtCore.QRect(1380, 280, 200, 51))
        self.Status.addItems(["Concluido", "Em andamento", "Cancelado"])
        self.Status.setStyleSheet("""
    QComboBox {
        background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }

    QComboBox QAbstractItemView {
        background-color: white;
        border: none;
        selection-background-color: #8B008B;  /* roxinho da sua paleta */
        selection-color: white;
        font-size: 14pt;
    }
""")
        self.label_total = QtWidgets.QLabel(parent)
        self.label_total.setText("Total do Pedido")
        self.label_total.setFont(font_label)
        self.label_total.setStyleSheet("font-size: 16pt; font-weight: bold; color: black; background: transparent;")
        self.label_total.setGeometry(QtCore.QRect(70, 310, 210, 20))
        self.label_total.setObjectName("label_total")

        # Total
        self.Total = QtWidgets.QLineEdit(parent)
        self.Total.setFont(font_label)
        self.Total.setStyleSheet("""
             QLineEdit {
          background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }
         """)
        self.Total.setObjectName("Total do Pedido")
        self.Total.setGeometry(QtCore.QRect(70, 350, 891, 51))
        self.Total.textChanged.connect(self.format_text)

        self.label_detalhes = QtWidgets.QLabel(parent)
        self.label_detalhes.setText("Detalhes")
        self.label_detalhes.setFont(font_label)
        self.label_detalhes.setStyleSheet("font-size: 16pt; font-weight: bold; color: black; background: transparent;")
        self.label_detalhes.setGeometry(QtCore.QRect(1410, 410, 170, 20))
        self.label_detalhes.setObjectName("label_detalhes")

        # Detalhes
        self.Detalhes = QtWidgets.QTextEdit(parent)
        self.Detalhes.setFont(font_label)
        self.Detalhes.setStyleSheet("""
        QTextEdit {
          background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
        }
         """)
        self.Detalhes.setObjectName("Detalhes")
        self.Detalhes.setGeometry(QtCore.QRect(1200, 450, 541, 300))

        self.label_data = QtWidgets.QLabel(parent)
        self.label_data.setText("Data")
        self.label_data.setFont(font_label)
        self.label_data.setStyleSheet("font-size: 16pt; font-weight: bold; color: black; background: transparent;")
        self.label_data.setGeometry(QtCore.QRect(290, 470, 140, 20))
        self.label_data.setObjectName("label_data")

        # Data do Pedido
        self.Data = QtWidgets.QDateEdit(parent)
        self.Data.setGeometry(QtCore.QRect(260, 510, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.Data.setFont(font)
        self.Data.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Data.setAutoFillBackground(False)
        # Conseguir andar pelas meses do ano pelo teclado
        self.Data.setWrapping(False)
        self.Data.setFrame(False)
        self.Data.setReadOnly(False)
        self.Data.setAccelerated(False)
        self.Data.setProperty("showGroupSeparator", True)
        self.Data.setDateTime(QtCore.QDateTime(
            QtCore.QDate(2024, 1, 1), QtCore.QTime(0, 0)))
        self.Data.setCalendarPopup(True)
        self.Data.setTimeSpec(QtCore.Qt.LocalTime)
        self.Data.setDate(QDate.currentDate())

        # Aplicando estilo para deixar o calendário branco
        self.Data.setStyleSheet("""
            QDateEdit {
                background-color: white;
            }

                                QCalendarWidget QToolButton {
            height: 80px;               /* botões mais altos */
            width: 110px;               /* botões mais largos */
            font-size: 16px;            /* texto maior */
            color: black;
            background-color: white;
            }
            QCalendarWidget QWidget {
                background-color: white;
            }
            QCalendarWidget QToolButton {
                background-color: white;
                color: black;
            }
            QCalendarWidget QToolButton:hover {
                background-color: lightgray;
            }
            QCalendarWidget QSpinBox {
                font-size: 16px;            /* mês/ano maiores */
                color: black;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: white;
                color: black;
                selection-background-color: rgb(0, 255, 127);
                selection-color: white;
            }
        """)

        # Adicionando o formulário ao layout principal
        layout.addLayout(form_layout)

        # Botão esta como "buttonBox" pq o "buttonBox2" eu acabei colocando lá para cima.
        self.buttonBox = QtWidgets.QDialogButtonBox(parent)
        self.buttonBox.setGeometry(QtCore.QRect(700, 720, 440, 61))
        self.buttonBox.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.buttonBox.setStyleSheet("""
            QDialogButtonBox {
                border: 2px solid rgba(139, 0, 139, 200);
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 150);
                padding: 5px;
            }
            QDialogButtonBox QPushButton {
                min-width: 40px;          /* largura mínima */
                min-height: 20px;          /* altura mínima */
                font-size: 14pt;           /* texto maior */
                font-weight: bold;         /* texto mais forte */
            }
            QDialogButtonBox::button {
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: rgba(255, 255, 255, 200);
                color: rgba(139, 0, 139, 200);
            }
        """)
        self.buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.save_data2)

        self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reset_fields2)

        # Navegação entre Campos
        self.Nome2.returnPressed.connect(self.Total.setFocus)
        self.Total.returnPressed.connect(self.Detalhes.setFocus)

        self.resetButton2 = QtWidgets.QPushButton("Resetar IDs", parent)
        self.resetButton2.setGeometry(QtCore.QRect(1700, 80, 90, 30))
        self.label_resetButton2 = QtWidgets.QLabel(parent)
        self.label_resetButton2.setText("Zerar a tabela de Pedidos")
        self.label_resetButton2.setFont(font_label)
        self.label_resetButton2.setStyleSheet("font-size: 12pt; font-weight: bold; color: black; background: transparent;")
        self.label_resetButton2.setGeometry(QtCore.QRect(1640, 20, 400, 40))
        self.label_resetButton2.setObjectName("label_resetButton")
        self.resetButton2.clicked.connect(self.resetar_tabela_e_ids2)

    def setup_table2(self, parent):
        # Barra de Pesquisa e legenda
        layout_pedidos = QtWidgets.QVBoxLayout(parent)
        self.search_box2 = QtWidgets.QLineEdit()
        self.search_box2.setGeometry(QtCore.QRect(120, 10, 861, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.search_box2.setFont(font)
        self.search_box2.setAccessibleDescription("")
        self.search_box2.setStyleSheet("font-size: 14pt;")
        self.search_box2.setStyleSheet("""
    QLineEdit {
        background-color: white;
        border: 2px solid #ffb6c1; /* Rosa claro */
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 14pt;
        color: #333;
    }
    QLineEdit:focus {
        border: 2px solid #ff69b4; /* Rosa mais forte no foco */
    }
""")
        self.search_box2.setInputMask("")
        self.search_box2.setPlaceholderText("Pesquisar....")
        self.search_box2.setClearButtonEnabled(True)
        self.search_box2.setObjectName("search_box2")
        self.search_box2.setMinimumHeight(40)
        # Conectar, fazer a busca enquanto digita
        self.search_box2.textChanged.connect(self.search_data2)


        # Criar tableWidget2
        self.tableWidget2 = QtWidgets.QTableWidget()
        self.tableWidget2.setGeometry(QtCore.QRect(70, 60, 1000, 420))
        self.tableWidget2.setColumnCount(7)
        self.tableWidget2.setHorizontalHeaderLabels(
            ["Código de Cadastro", "Nome", "Tipo", "Detalhes",
             "Data", "Status", "Valor"])
        self.tableWidget2.setObjectName("tableWidget2")
        self.tableWidget2.horizontalHeader().setMinimumHeight(30)

        layout_pedidos.addWidget(self.search_box2)
        layout_pedidos.addWidget(self.tableWidget2)

        # Aplicar delegados para as máscaras de data e telefone
        data_delegate = MaskedDelegate("00/00/0000", self.tableWidget2)

        self.tableWidget2.setItemDelegateForColumn(
            4, data_delegate)  # Data de

        # Definir fonte em negrito para os cabeçalhos
        header_font = QtGui.QFont()
        header_font.setBold(True)

        for col in range(self.tableWidget2.columnCount()):
            item = self.tableWidget2.horizontalHeaderItem(col)
            if item:
                item.setFont(header_font)
        # Defina a política de redimensionamento da tabela
        self.tableWidget2.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch)

        self.load_data2()
        # Conectar ao método para atualizar o banco
        self.tableWidget2.itemChanged.connect(self.update_database_table)

                # Layout para o botão de excluir
        self.buttonBox2_delete = QtWidgets.QPushButton(
            "Excluir Pedido", parent)
        self.buttonBox2_delete.setGeometry(QtCore.QRect(1760, 8, 108, 41))
        self.buttonBox2_delete.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.buttonBox2_delete.setStyleSheet("""
    QPushButton {
        background-color: #ff4d4d;   /* Vermelho claro */
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #e60000;  /* Vermelho mais escuro no hover */
    }
""")
        self.buttonBox2_delete.clicked.connect(self.delete_order2)
        self.buttonBox2_delete.setVisible(False)  #escondido
                # Definir fonte em negrito
        font = QtGui.QFont()
        font.setBold(True)
        self.buttonBox2_delete.setFont(font)

        # Conectar a função de seleção de linha
        self.tableWidget2.itemSelectionChanged.connect(self.show_delete)

        # Conectar o evento de clique fora da tabela
        parent.mousePressEvent = self.mouse_press_event2
        self.tabPedidosSub.currentChanged.connect(self.on_tab_changed2)
        self.tableWidget2.cellClicked.connect(self.on_table_cell_clicked2)

    def format_text(self):
        text = self.Total.text().replace("R$", "").replace(".", "").replace(",", "")  # Remove formatação anterior

        if text:
            # Garante que sempre tenha pelo menos 3 dígitos
            text = text.zfill(3)
            # Separa centavos corretamente
            formatted = f"{int(text[:-2])},{text[-2:]}"

            self.Total.blockSignals(True)
            self.Total.setText(formatted.lstrip("0").replace(
                ".,", "0,") if formatted != "" else "0,00")
            self.Total.blockSignals(False)

    def search_data2(self):
        search_term = self.search_box2.text().lower().strip()
        self.tableWidget2.setSortingEnabled(False)
        for row in range(self.tableWidget2.rowCount()):
            # Pega o valor da coluna "Nome"
            item_nome2 = self.tableWidget2.item(row, 1)
            item_data = self.tableWidget2.item(row, 4)
            if ((item_nome2 is not None and search_term in item_nome2.text().lower()) or
                (item_data is not None and search_term in item_data.text().lower())):
                self.tableWidget2.showRow(row)  # Mostra a linha correspondente
            else:
                # Esconde a linha que não corresponde
                self.tableWidget2.hideRow(row)

    def on_tab_changed2(self, index):
        current_tab = self.tabPedidosSub.widget(index)
        if current_tab != self.tab_pedidos_lista:
            self.buttonBox2_delete.setVisible(False)

    def on_table_cell_clicked2(self, row, column):
        self.buttonBox2_delete.setVisible(True)

    def carregar_item(self):
        if os.path.exists(CAMINHO_ARQUIVO):
            with open(CAMINHO_ARQUIVO, "r", encoding="utf-8") as f:
                itens = json.load(f)
                self.Comida.addItems(itens)

    def adicionar_item(self):
        novo_item = self.Comida.currentText().strip()
        if not novo_item:
            QMessageBox.warning(
                self, "Aviso", "Digite um item válido.")
            return

        if novo_item not in [self.Comida.itemText(i)
                             for i in range(self.Comida.count())]:
            self.Comida.addItem(novo_item)
            self.salvar_itens()
            self.Comida.setCurrentText("")
        else:
            QMessageBox.information(
                self, "Info", "Esse item já existe.")

    def salvar_itens(self):
        itens = [self.Comida.itemText(i)
                 for i in range(self.Comida.count())]
        with open(CAMINHO_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(itens, f, ensure_ascii=False, indent=4)

    def remover_item(self):
        item_remover = self.Comida.currentText().strip()
        if not item_remover:
            QMessageBox.warning(
                None, "Aviso", "Selecione um item para remover.")
            return

        index = self.Comida.findText(item_remover)
        if index >= 0:
            confirmar = QMessageBox.question(
                None, "Confirmar Remoção",
                f"Tem certeza que deseja remover '{item_remover}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirmar == QMessageBox.Yes:
                self.Comida.removeItem(index)
                self.salvar_itens()
                QMessageBox.information(
                    None, "Removido", f"'{item_remover}' foi removido com sucesso.")
        else:
            QMessageBox.information(
                None, "Info", "Esse item não existe.")

    def show_delete(self):
        if self.tableWidget2.currentRow() >= 0:
            self.buttonBox2_delete.setVisible(True)
        else:
            self.buttonBox2_delete.setVisible(False)

        # Evento de clique
    def mouse_press_event2(self, event):
        if self.tabPedidosSub.currentWidget() == self.tab_pedido_form:
            if not self.tableWidget2.viewport().rect().contains(self.tableWidget2.mapFromParent(event.pos())):
                self.buttonBox2_delete.setVisible(False)
                self.tableWidget2.clearSelection()

    def reset_fields2(self):
        # Reseta todos os campos do formulário
        self.Nome2.clear()
        self.Detalhes.clear()
        self.Total.clear()
        # Resetar ComboBoxes para o primeiro item
        if self.Comida.count() > 0:
           self.Comida.setCurrentIndex(0)
        if self.Status.count() > 0:
           self.Status.setCurrentIndex(0)
           # Resetar Data para hoje
        self.Data.setDate(QtCore.QDate.currentDate())

    def save_data2(self):
        """Salva os dados no banco de dados"""
        # Obter valores dos campos
        nome = self.Nome2.text()
        tipo = self.Comida.currentText()
        detalhes = self.Detalhes.toPlainText()
        data = self.Data.text()
        status = self.Status.currentText()
        valor = self.Total.text().replace(".", "").replace(",", ".")

        if not nome or not valor:  # Validar campos obrigatórios
            QtWidgets.QMessageBox.warning(
                None, "Aviso", "Nome e Valor são obrigatórios!")
            return

        # Conectar ao banco de dados usando a função `connect_to_db`
        connection = connect_db()
        if not connection:
            QtWidgets.QMessageBox.critical(
                None, "Erro", "Não foi possível conectar ao banco de dados.")
            return

        try:
            # Inicializar cursor
            cursor = connection.cursor()
            query = """
            INSERT INTO pedidos (nome, tipo,
            detalhes, data, status, valor)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (nome, tipo,
                                   detalhes, data, status, valor))
            codigo_cadastro = cursor.lastrowid
            connection.commit()

            try:
                self.widget_dashboard.atualizar_dashboard()
            except:
                pass

            # Feedback ao usuário
            QtWidgets.QMessageBox.information(
                None, "Sucesso", "Dados salvos com sucesso!")

        except Exception as e:
            QtWidgets.QMessageBox.critical(
            None, "Erro", f"Erro ao salvar os dados: {e}")

        finally:
            # Garantir que o cursor e a conexão sejam fechados
            if 'cursor' in locals() and cursor:
                cursor.close()
            if connection:
                connection.close()

        row_position = self.tableWidget2.rowCount()
        self.tableWidget2.insertRow(row_position)
        self.tableWidget2.setItem(
            row_position, 0, QtWidgets.QTableWidgetItem(str(codigo_cadastro).zfill(4)))
        self.tableWidget2.setItem(
            row_position, 1, QtWidgets.QTableWidgetItem(self.Nome2.text()))
        self.tableWidget2.setItem(
            row_position, 2, QtWidgets.QTableWidgetItem(self.Comida.currentText()))

        self.tableWidget2.setItem(
            row_position, 3, QtWidgets.QTableWidgetItem(self.Detalhes.toPlainText()))  # Corrigido
        data = self.Data.text()
        self.tableWidget2.setItem(
            row_position, 4, QtWidgets.QTableWidgetItem(data))
        self.tableWidget2.setItem(
            row_position, 5, QtWidgets.QTableWidgetItem(self.Status.currentText()))
        self.tableWidget2.setItem(
            row_position, 6, QtWidgets.QTableWidgetItem(self.Total.text()))

        self.clear_fields2()

        # Criar a fonte mais grossa (bold)
        bold_font = QtGui.QFont()
        bold_font.setBold(True)

        # Colorir a linha dependendo do status e aplicar a fonte grossa
        for col in range(self.tableWidget2.columnCount()):
            item = self.tableWidget2.item(row_position, 5)
            item.setFont(bold_font)  # Aplica a fonte grossa

         # Colorir a linha dependendo do status
        if status == "Concluido":
            for col in range(self.tableWidget2.columnCount()):
                item = self.tableWidget2.item(row_position, 5)
                # Verde para 'Concluído'
                item.setForeground(QtGui.QColor(0, 128, 0))
        elif status == "Em andamento":
            for col in range(self.tableWidget2.columnCount()):
                item = self.tableWidget2.item(row_position, 5)
                # Laranja para 'Em andamento'
                item.setForeground(QtGui.QColor(255, 135, 0))
        elif status == "Cancelado":
            for col in range(self.tableWidget2.columnCount()):
                item = self.tableWidget2.item(row_position, 5)
                # Vermelho para 'Cancelado'
                item.setForeground(QtGui.QColor(255, 0, 0))
        self.clear_fields2()

    def update_color(self, item):
        # Dicionário de cores para cada status
        status_colors = {
            "Concluido": QtGui.QColor(0, 128, 0),        # Verde
            "Em andamento": QtGui.QColor(255, 135, 0),  # Laranja
            "Cancelado": QtGui.QColor(255, 0, 0),  # Vermelho
        }
        """Atualiza a cor do texto na célula editada"""
        if item.column() == 5:  # Apenas para a coluna 4
            status = item.text()
            # Obtém a cor correspondente, se existir
            color = status_colors.get(status, None)
            if color:
                item.setForeground(color)  # Aplica a cor
            else:
                # Preto como padrão para valores não definidos
                item.setForeground(QtGui.QColor(0, 0, 0))

    def load_data2(self):
        conn = connect_db()
        cursor = conn.cursor()
        try:
            self.tableWidget2.setRowCount(0)
            cursor.execute(
                "SELECT codigo_cadastro, "
                "nome, tipo, detalhes, data, status, valor "
                "FROM PEDIDOS ORDER BY codigo_cadastro ASC"
            )
            rows = cursor.fetchall()

            # Adiciona os dados na tabela da interface
            self.tableWidget2.setRowCount(len(rows))
            # Desativa a ordenação automática antes de carregar
            self.tableWidget2.setSortingEnabled(False)
            for row_index, row_data in enumerate(rows):
                for col_index, col_data in enumerate(row_data):
                    item: None
                    if col_index == 0 and col_data:
                        formatted_code = str(col_data).zfill(4)
                        print(f"Codigo Formatado: {formatted_code}")

                    # Verifica se a coluna é de data e formata
                    if col_index == 4 and col_data:
                        try:
                            # Converte a data para o formato DD/MM/YYYY
                            col_data = datetime.strptime(
                                str(col_data), "%Y-%m-%d").strftime("%d/%m/%Y")
                        except ValueError:
                            col_data = "Data Inválida"  # Fallback para casos de erro
                        item = QtWidgets.QTableWidgetItem(col_data)
                        # Formatação especial para "valor" (coluna 6)
                    elif col_index == 6 and col_data:  # Coluna de valor
                        formatted_value = f"R${float(col_data):.2f}".replace(
                            ".", ",")
                        item = QtWidgets.QTableWidgetItem(formatted_value)
                    else:
                        item = QtWidgets.QTableWidgetItem(str(col_data))


                    # Aplica cor ao status (coluna 5)
                    if col_index == 5:  # Coluna de status
                        color = self.get_status_color(col_data)
                        item.setForeground(color)
                        font = QtGui.QFont()
                        font.setBold(True)
                        item.setFont(font)
                    self.tableWidget2.setItem(
                        row_index, col_index, item)

                    # Adiciona o item à célula correspondente
                    for row in range(self.tableWidget2.rowCount()):
                        item = self.tableWidget2.item(
                            row, 0)  # Coluna do código
                        if item:
                            # Aplica a formatação final
                            item.setText(item.text().zfill(4))

        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
        finally:
            cursor.close()
            conn.close()

    def get_status_color(self, status):
        """Retorna a cor correspondente ao status."""
        status_colors = {
            "Concluido": QtGui.QColor(0, 128, 0),        # Verde
            "Em andamento": QtGui.QColor(255, 135, 0),  # Laranja
            "Cancelado": QtGui.QColor(255, 0, 0),       # Vermelho
        }
        # Preto como padrão
        return status_colors.get(status, QtGui.QColor(0, 0, 0))

    def update_database_table(self, item):
        """Atualiza o banco de dados com as alterações feitas na tabela."""
        try:
            from datetime import datetime

            # Desabilitar a ordenação antes de editar
            self.tableWidget2.setSortingEnabled(False)

            # Obter a linha, coluna e novo valor
            row = item.row()
            column = item.column()
            new_value = item.text()

            if column == 0:
                return

            # Mapear as colunas do banco p/ colunas QTableWidget
            column_mapping = {
                0: "codigo_cadastro",
                1: "nome",
                2: "tipo",
                3: "detalhes",
                4: "data",
                5: "status",
                6: "valor",
            }

            # Obter o nome da coluna correspondente no banco de dados
            column_name = column_mapping.get(column, None)
            if not column_name:
                return  # Ignorar colunas sem mapeamento
            # identificador único
            codigo_item = self.tableWidget2.item(row, 0)
            if not codigo_item:
                return
            # Garante que o código tenha 4 dígitos, se for necessário
            codigo = int(codigo_item.text())

            # Atualizar o banco de dados
            conn = connect_db()
            if not conn:
                return
            cursor = conn.cursor()

            if column == 6:  # Coluna de valor
                try:
                    # Remover a formatação (R$ e , )
                    raw_value = new_value.replace("R$", "").replace(
                        ".", "").replace(",", ".").strip()
                    new_value_numeric = float(raw_value)
                    # Atualizar o banco com o valor numérico
                    cursor.execute(
                        f"UPDATE pedidos SET {column_name} = ? WHERE codigo_cadastro = ?",
                        (new_value_numeric, codigo)
                    )
                    conn.commit()

                    # Atualizar o valor formatado na interface
                    formatted_value = f"R$ {new_value_numeric:,.2f}".replace(
                        ",", "X").replace(".", ",").replace("X", ".")
                    item.setText(formatted_value)
                except ValueError:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Erro",
                        "Valor inválido. Use apenas números.",
                        buttons=QtWidgets.QMessageBox.Ok
                    )
                    return
            else:
                # Atualizar outras colunas
                cursor.execute(
                    f"UPDATE pedidos SET {column_name} = ? WHERE codigo_cadastro = ?",
                    (new_value, codigo)
                )
                conn.commit()

            if column == 4:  # Coluna de data
                try:
                    if "-" in new_value:  # Formato ISO (YYYY-MM-DD)
                        dt = datetime.strptime(new_value, "%Y-%m-%d")
                    else:  # Formato esperado (DD/MM/YYYY)
                        dt = datetime.strptime(new_value, "%d/%m/%Y")
                    db_value = dt.strftime("%Y-%m-%d")
                    formatted_date = dt.strftime("%d/%m/%Y")
                    item.setText(formatted_date)
                    cursor.execute(
                        f"UPDATE pedidos SET {column_name} = ? WHERE codigo_cadastro = ?",
                        (db_value, codigo)
                    )

                except ValueError:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Erro",
                        "Formato de data inválido. Use DD/MM/YYYY.",
                        buttons=QtWidgets.QMessageBox.Ok
                    )
                    self.load_data2()
                    return
            elif column == 5:  # Coluna de status
                color = self.get_status_color(new_value)
                item.setForeground(color)
                font = QtGui.QFont()
                font.setBold(True)
                item.setFont(font)

        except ValueError as ve:
            QtWidgets.QMessageBox.warning(
                self,
                "Erro",
                f"Erro de valor: {ve}",
                buttons=QtWidgets.QMessageBox.Ok
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao atualizar o banco: {e}",
                buttons=QtWidgets.QMessageBox.Ok
            )
        finally:
            # Garantir que a ordenação permaneça desativada
            self.tableWidget2.setSortingEnabled(False)
            if 'cursor' in locals() and cursor:
                cursor.close()
                conn.commit()
                try:
                    self.widget_dashboard.atualizar_dashboard()
                except:
                    pass

    def delete_order2(self):
        """Exclui o(s) pedidos(s) selecionado(s) do banco de dados e atualiza a tabela."""
        selected_rows = sorted(
            set(item.row() for item in self.tableWidget2.selectedItems()), reverse=True
        )

        if not selected_rows:
            QtWidgets.QMessageBox.warning(
                None, "Aviso", "Nenhum pedido selecionado!")
            return

            # Criar caixa de diálogo de confirmação
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Question)
        msg_box.setWindowTitle("Confirmação")
        msg_box.setText(
            "Tem certeza que deseja excluir o(s) pedido(s) selecionado(s)?")

        # Criar botões personalizados
        btn_sim = msg_box.addButton("Sim", QtWidgets.QMessageBox.YesRole)
        btn_cancelar = msg_box.addButton(
            "Cancelar", QtWidgets.QMessageBox.RejectRole)

        msg_box.exec()  # Exibir a caixa de diálogo

        # Se o usuário pressionar "Cancelar", interrompe a função
        if msg_box.clickedButton() == btn_cancelar:
            return

        conn = connect_db()
        if not conn:
            QtWidgets.QMessageBox.critical(
                None, "Erro", "Falha ao conectar ao banco de dados.")
            return

        try:
            cursor = conn.cursor()
            fazer_backup(DB_PATH, tipo="diario")
            for row in selected_rows:
                # Obtenha o nome do cliente para exclusão
                # Assumindo que o nome está na coluna 0
                codigo_pedido = self.tableWidget2.item(row, 0).text()
                cursor.execute(
                    "DELETE FROM pedidos WHERE codigo_cadastro = ?", (codigo_pedido,))

            conn.commit()
            try:
                self.widget_dashboard.atualizar_dashboard()
            except:
                pass
            QtWidgets.QMessageBox.information(
                None, "Sucesso", "Pedidos(s) excluído(s) com sucesso!")

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                None, "Erro", f"Erro ao excluir pedido(s): {e}")
        finally:
            conn.close()

        # Recarregar a tabela para garantir consistência
        self.load_data2()

    def clear_fields2(self):
        """Limpa os campos do formulário."""
        self.Nome2.clear()
        self.Detalhes.clear()
        self.Total.clear()
        # Resetar ComboBoxes para o primeiro item
        if self.Comida.count() > 0:
           self.Comida.setCurrentIndex(0)
        if self.Status.count() > 0:
           self.Status.setCurrentIndex(0)
           # Resetar Data para hoje
        self.Data.setDate(QtCore.QDate.currentDate())

    def resetar_tabela_e_ids2(self):
        from datetime import datetime, date

        msg_box2 = QMessageBox()
        msg_box2.setWindowTitle("Confirmar Reset")
        msg_box2.setText("Quer apagar TODOS os pedidos e resetar os IDs clique em 'Yes', "
                        "quer apenas gerar relatorio clique em 'No'")
        msg_box2.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

        # Aumentar tamanho da fonte
        font = QFont()
        font.setPointSize(14)  # Aqui você pode aumentar ainda mais
        msg_box2.setFont(font)
        resposta = msg_box2.exec()

        if resposta == QMessageBox.Cancel:
            return  # Sai da função

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT codigo_cadastro, nome, tipo, detalhes, data, status, valor
            FROM pedidos
        """)
        dados = cursor.fetchall()

        if not dados:
            QMessageBox.information(None, "Aviso", "Não há dados para gerar o relatório.")
        else:
            # === 1️⃣ Formatar datas no padrão dd/mm/aaaa ===
            dados_formatados = []
            for linha in dados:
                codigo_cadastro, nome, tipo, detalhes, data, status, valor = linha

                # Converter "2000-05-14" → "14/05/2000"
                if isinstance(data, (datetime, date)):
                    data = data.strftime("%d/%m/%Y")
                else:
                    try:
                        data = datetime.strptime(str(data), "%Y-%m-%d").strftime("%d/%m/%Y")
                    except Exception:
                        data = str(data)  # Se já estiver formatada

                dados_formatados.append([
                    codigo_cadastro, nome, tipo, detalhes, data, status, valor
                ])

            # === 2️⃣ Criar o relatório (imagem .png) ===
            from datetime import datetime
            import pandas as pd
            import os
            from PyQt5.QtGui import QDesktopServices
            from PyQt5.QtCore import QUrl
            from openpyxl.styles import Font, Alignment, Border, Side
            from openpyxl.utils import get_column_letter


            meses = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
            agora = datetime.now()
            mes_atual = f"{meses[agora.month]} de {agora.year}"

            colunas = ["Codigo_Cadastro", "Nome", "Tipo", "Detalhes", "Data", "Status", "Valor"]

            # === 🔧 Quebrar textos muito longos (endereços, emails, etc.) ===
            dados_ajustados = []
            for linha in dados_formatados:
                codigo_cadastro, nome, tipo, detalhes, data, status, valor = linha

                dados_ajustados.append([
                    codigo_cadastro,
                    "\n".join(textwrap.wrap(str(nome), 40)),
                    tipo,
                    "\n".join(textwrap.wrap(str(detalhes), 40)),
                    data,
                    status,
                    valor
                ])
            df = pd.DataFrame(dados_ajustados, columns=colunas)

            # === 3️⃣ Criar pasta "Relatórios" na Área de Trabalho ===
            desktop = os.path.join(os.environ["USERPROFILE"], "OneDrive", "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")

            pasta = os.path.join(desktop, "Relatórios")
            os.makedirs(pasta, exist_ok=True)
            caminho_arquivo = os.path.join(pasta, f"Relatorio_Pedidos_{mes_atual}.xlsx"
            )

            with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Pedidos")

                workbook = writer.book
                worksheet = writer.sheets["Pedidos"]
                # Estilos
                header_font = Font(bold=True)
                center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
                text_align = Alignment(vertical="top", wrap_text=True)

                thin_border = Border(
                    left=Side(style="thin"),
                    right=Side(style="thin"),
                    top=Side(style="thin"),
                    bottom=Side(style="thin")
                )
                # Cabeçalho
                for col_num, coluna in enumerate(colunas, start=1):
                    cell = worksheet.cell(row=1, column=col_num)
                    cell.value = coluna
                    cell.font = header_font
                    cell.alignment = center_align
                    cell.border = thin_border

                    # largura da coluna
                    worksheet.column_dimensions[get_column_letter(col_num)].width = 25

                                    # Dados
                for row in worksheet.iter_rows(
                    min_row=2,
                    max_row=worksheet.max_row,
                    min_col=1,
                    max_col=len(colunas)
                ):
                    for cell in row:
                        cell.alignment = text_align
                        cell.border = thin_border

                # Congelar cabeçalho
                worksheet.freeze_panes = "A2"
                # Autofiltro
                worksheet.auto_filter.ref = f"A1:{get_column_letter(len(colunas))}{worksheet.max_row}"

            QDesktopServices.openUrl(QUrl.fromLocalFile(caminho_arquivo))

            QMessageBox.information(
                None,
                "Relatório Gerado",
                f"Relatório gerado e aberto no Excel:\n\n{caminho_arquivo}"
            )

        # === 4️⃣ Resetar a tabela e IDs ===
        if resposta == QMessageBox.Yes:
            try:
                conn.commit()
                conn.close()

                fazer_backup(DB_PATH, tipo="reset")

                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM pedidos;")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='pedidos';")
                conn.commit()
                QMessageBox.information(None, "Resetado com Sucesso",
                                        "Todos os dados foram apagados e os IDs resetados para 1.")
            except Exception as e:
                QMessageBox.critical(None, "Erro", f"Ocorreu um erro ao resetar os dados: {str(e)}")
            finally:
                cursor.close()
                conn.close()
                self.load_data2()
                self.tableWidget2.setRowCount(0)
                try:
                    self.widget_dashboard.atualizar_dashboard()
                except:
                    pass

    def setup_pagamento_ui(self, parent):
        layout_pagamentos = QtWidgets.QVBoxLayout(parent)
        font_label = QtGui.QFont()
        font_label.setPointSize(12)
        font_label.setBold(True)
        font_label.setWeight(75)

        self.tabPagamentosSub = QtWidgets.QTabWidget(parent)
        self.tabPagamentosSub.setObjectName("tabPagamentosSub")
        layout_pagamentos.addWidget(self.tabPagamentosSub)

        # Sub-aba 1 - Formulário de Cadastro de pagamentos
        self.tab_pagamento_form = QtWidgets.QWidget()
        self.tab_pagamento_form.setObjectName("tab_pagamento_form")
        self.setup_pagamento_form(self.tab_pagamento_form)
        self.tabPagamentosSub.addTab(self.tab_pagamento_form, "Cadastro")

        # Sub-aba 2 - Lista de pagamentos
        self.tab_pagamentos_lista = QtWidgets.QWidget()
        self.tab_pagamentos_lista.setObjectName("tab_pagamentos_lista")
        self.setup_table3(self.tab_pagamentos_lista)
        self.tabPagamentosSub.addTab(
            self.tab_pagamentos_lista, "Lista de Pagamentos")

    def setup_pagamento_form(self, parent):
        parent.setStyleSheet("""
    background-color: #F0A8C0;
""")
        font_label = QtGui.QFont()
        font_label.setPointSize(12)
        font_label.setBold(True)
        font_label.setWeight(75)

        # Criando um layout vertical para centralizar os campos
        layout = QtWidgets.QVBoxLayout()

        # Centralizando o formulário de cadastro
        form_layout = QtWidgets.QFormLayout()

        # Label "Nome"
        self.label_nome3 = QtWidgets.QLabel(parent)
        self.label_nome3.setText("Nome do Cliente")
        self.label_nome3.setFont(font_label)
        self.label_nome3.setStyleSheet("font-size: 16pt; font-weight: bold; color: black; background: transparent;")
        self.label_nome3.setGeometry(QtCore.QRect(70, 210, 200, 20))
        self.label_nome3.setObjectName("label_nome3")

        # Campo de texto Nome
        self.Nome3 = QtWidgets.QLineEdit(parent)
        self.Nome3.setFont(font_label)
        self.Nome3.setStyleSheet("""
             QLineEdit {
          background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }
         """)
        self.Nome3.setObjectName("Nome")
        self.Nome3.setGeometry(QtCore.QRect(70, 250, 891, 51))

        self.label_total2 = QtWidgets.QLabel(parent)
        self.label_total2.setText("Total do Pagamento")
        self.label_total2.setFont(font_label)
        self.label_total2.setStyleSheet("font-size: 16pt; font-weight: bold; color: black; background: transparent;")
        self.label_total2.setGeometry(QtCore.QRect(430, 560, 240, 30))
        self.label_total2.setObjectName("label_total2")

        # Total
        self.Total2 = QtWidgets.QLineEdit(parent)
        self.Total2.setFont(font_label)
        self.Total2.setStyleSheet("""
             QLineEdit {
          background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }
         """)
        self.Total2.setObjectName("Total do Pagamento")
        self.Total2.setGeometry(QtCore.QRect(430, 600, 891, 51))
        self.Total2.textChanged.connect(self.format_text2)

        # ComboBox Opções
        self.Opções = QtWidgets.QComboBox(parent)
        self.Opções.setFont(font_label)
        self.Opções.setObjectName("Opções de Pagamento")
        self.Opções.setEditable(True)
        self.Opções.setGeometry(QtCore.QRect(1200, 250, 261, 51))
        self.Opções.setStyleSheet("""
    QComboBox {
        background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }

    QComboBox QAbstractItemView {
        background-color: white;
        border: none;
        selection-background-color: #8B008B;  /* roxinho da sua paleta */
        selection-color: white;
        font-size: 14pt;
    }
""")

        self.Opções.addItems(["Pix", "Cartão Débito", "Cartão Crédito", "Dinheiro", "Boleto", "Transferência Bancária", "Carteira Digital", "Outro"])

        # ComboBox Status
        self.Status2 = QtWidgets.QComboBox(parent)
        self.Status2.setFont(font_label)
        self.Status2.setObjectName("Status")
        self.Status2.setGeometry(QtCore.QRect(1500, 350, 200, 51))
        self.Status2.setStyleSheet("""
    QComboBox {
        background-color: white;
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-size: 14pt;
        color: #333;
    }

    QComboBox QAbstractItemView {
        background-color: white;
        border: none;
        selection-background-color: #8B008B;  /* roxinho da sua paleta */
        selection-color: white;
        font-size: 14pt;
    }
""")
        self.Status2.addItems(["Pago", "Vai Pagar", "Nao Pagou"])

        # Data do Pagamento
        self.Data2 = QtWidgets.QDateEdit(parent)
        self.Data2.setGeometry(QtCore.QRect(1540, 260, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.Data2.setFont(font)
        self.Data2.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.Data2.setAutoFillBackground(False)
        # Conseguir andar pelas meses do ano pelo teclado
        self.Data2.setWrapping(False)
        self.Data2.setFrame(False)
        self.Data2.setReadOnly(False)
        self.Data2.setAccelerated(False)
        self.Data2.setProperty("showGroupSeparator", True)
        self.Data2.setDateTime(QtCore.QDateTime(
            QtCore.QDate(2024, 1, 1), QtCore.QTime(0, 0)))
        self.Data2.setCalendarPopup(True)
        self.Data2.setTimeSpec(QtCore.Qt.LocalTime)
        self.Data2.setDate(QDate.currentDate())

        # Aplicando estilo para deixar o calendário branco
        self.Data2.setStyleSheet("""
            QDateEdit {
                background-color: white;
            }
            QCalendarWidget QWidget {
                background-color: white;
            }
            QCalendarWidget QToolButton {
                background-color: white;
                color: black;
            }
            QCalendarWidget QToolButton:hover {
                background-color: lightgray;
            }
            QCalendarWidget QSpinBox {
                color: black;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: white;
                color: black;
                selection-background-color: rgb(0, 255, 127);
                selection-color: white;
            }
        """)

        # Adicionando o formulário ao layout principal
        layout.addLayout(form_layout)

        # Botão de Ação OK/CANCELAR
        self.buttonBox3 = QtWidgets.QDialogButtonBox(parent)
        self.buttonBox3.setGeometry(QtCore.QRect(650, 700, 440, 61))
        self.buttonBox3.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.buttonBox3.setStyleSheet("""
            QDialogButtonBox {
                border: 2px solid rgba(139, 0, 139, 200);
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 150);
                padding: 5px;
            }
            QDialogButtonBox QPushButton {
                min-width: 40px;          /* largura mínima */
                min-height: 20px;          /* altura mínima */
                font-size: 14pt;           /* texto maior */
                font-weight: bold;         /* texto mais forte */
            }
            QDialogButtonBox::button {
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: rgba(255, 255, 255, 200);
                color: rgba(139, 0, 139, 200);
            }
        """)
        self.buttonBox3.setStandardButtons(
            QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox3.setCenterButtons(True)
        self.buttonBox3.setObjectName("buttonBox3")
        self.buttonBox3.button(
            QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.save_data3)

        self.buttonBox3.button(
            QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reset_fields3)

        # Navegação entre Campos
        self.Nome3.returnPressed.connect(self.Total2.setFocus)

        self.resetButton3 = QtWidgets.QPushButton("Resetar IDs", parent)
        self.resetButton3.setGeometry(QtCore.QRect(1700, 80, 90, 30))
        self.label_resetButton3 = QtWidgets.QLabel(parent)
        self.label_resetButton3.setText("Zerar a tabela de Pagamentos")
        self.label_resetButton3.setFont(font_label)
        self.label_resetButton3.setStyleSheet("font-size: 12pt; font-weight: bold; color: black; background: transparent;")
        self.label_resetButton3.setGeometry(QtCore.QRect(1600, 20, 400, 40))
        self.label_resetButton3.setObjectName("label_resetButton")
        self.resetButton3.clicked.connect(self.resetar_tabela_e_ids3)

    def setup_table3(self, parent):
        # Barra de Pesquisa e legenda
        layout_pagamentos = QtWidgets.QVBoxLayout(parent)
        self.search_box3 = QtWidgets.QLineEdit()
        self.search_box3.setGeometry(QtCore.QRect(120, 10, 861, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.search_box3.setFont(font)
        self.search_box3.setAccessibleDescription("")
        self.search_box3.setStyleSheet("font-size: 14pt;")
        self.search_box3.setStyleSheet("""
    QLineEdit {
        background-color: white;
        border: 2px solid #ffb6c1; /* Rosa claro */
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 14pt;
        color: #333;
    }
    QLineEdit:focus {
        border: 2px solid #ff69b4; /* Rosa mais forte no foco */
    }
""")
        self.search_box3.setInputMask("")
        self.search_box3.setPlaceholderText("Pesquisar....")
        self.search_box3.setClearButtonEnabled(True)
        self.search_box3.setObjectName("search_box3")
        self.search_box3.setMinimumHeight(40)
        self.search_box3.textChanged.connect(self.search_data3)

        # Criar QTableWidget3
        self.tableWidget3 = QtWidgets.QTableWidget()
        self.tableWidget3.setGeometry(QtCore.QRect(70, 60, 1000, 420))
        self.tableWidget3.setColumnCount(6)
        self.tableWidget3.setHorizontalHeaderLabels(
            ["Código de Cadastro", "Nome do Cliente", "Forma do Pagamento", "Valor do Pagamento", "Data", "Status"])
        self.tableWidget3.setObjectName("tableWidget3")
        self.tableWidget3.horizontalHeader().setMinimumHeight(30)

        layout_pagamentos.addWidget(self.search_box3)
        layout_pagamentos.addWidget(self.tableWidget3)

                # Aplicar delegados para as máscaras de data e telefone
        data_delegate = MaskedDelegate("00/00/0000", self.tableWidget3)

        self.tableWidget3.setItemDelegateForColumn(
            4, data_delegate)  # Data de

        # Definir fonte em negrito para os cabeçalhos
        header_font = QtGui.QFont()
        header_font.setBold(True)

        for col in range(self.tableWidget3.columnCount()):
            item = self.tableWidget3.horizontalHeaderItem(col)
            if item:
                item.setFont(header_font)

        # Defina a política de redimensionamento da tabela
        self.tableWidget3.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch)

        self.load_data3()
        # Conectar ao método para atualizar o banco
        self.tableWidget3.itemChanged.connect(self.update_database)

        # Layout para o botão de excluir
        self.buttonBox3_delete = QtWidgets.QPushButton(
            "Excluir Pedido", parent)
        self.buttonBox3_delete.setGeometry(QtCore.QRect(1760, 8, 108, 41))
        self.buttonBox3_delete.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.buttonBox3_delete.setStyleSheet("""
    QPushButton {
        background-color: #ff4d4d;   /* Vermelho claro */
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #e60000;  /* Vermelho mais escuro no hover */
    }
""")
        self.buttonBox3_delete.clicked.connect(self.delete_order3)
        self.buttonBox3_delete.setVisible(False)  #escondido
                # Definir fonte em negrito
        font = QtGui.QFont()
        font.setBold(True)
        self.buttonBox3_delete.setFont(font)

        # Conectar a função de seleção de linha
        self.tableWidget3.itemSelectionChanged.connect(self.show_delete2)

        # Conectar o evento de clique fora da tabela
        parent.mousePressEvent = self.mouse_press_event3
        self.tabPagamentosSub.currentChanged.connect(self.on_tab_changed3)
        self.tableWidget3.cellClicked.connect(self.on_table_cell_clicked3)

    def format_text2(self):
        text = self.Total2.text().replace("R$", "").replace(".", "").replace(",", "")  # Remove formatação anterior

        if text:
            # Garante que sempre tenha pelo menos 3 dígitos
            text = text.zfill(3)
            # Separa centavos corretamente
            formatted = f"{int(text[:-2])},{text[-2:]}"

            self.Total2.blockSignals(True)
            self.Total2.setText(formatted.lstrip("0").replace(
                ".,", "0,") if formatted != "" else "0,00")
            self.Total2.blockSignals(False)

    def search_data3(self):
        search_term = self.search_box3.text().lower().strip()
        self.tableWidget3.setSortingEnabled(False)
        for row in range(self.tableWidget3.rowCount()):
            # Pega o valor da coluna "Nome"
            item_nome3 = self.tableWidget3.item(row, 1)
            item_data2 = self.tableWidget3.item(row, 4)
            if ((item_nome3 is not None and search_term in item_nome3.text().lower()) or
                (item_data2 is not None and search_term in item_data2.text().lower())):
                self.tableWidget3.showRow(row)  # Mostra a linha correspondente
            else:
                # Esconde a linha que não corresponde
                self.tableWidget3.hideRow(row)

    def on_tab_changed3(self, index):
        current_tab = self.tabPagamentosSub.widget(index)
        if current_tab != self.tab_pagamentos_lista:
            self.buttonBox3_delete.setVisible(False)

    def on_table_cell_clicked3(self, row, column):
        self.buttonBox3_delete.setVisible(True)

    def show_delete2(self):
        if self.tableWidget3.currentRow() >= 0:
            self.buttonBox3_delete.setVisible(True)
        else:
            self.buttonBox3_delete.setVisible(False)

                    # Evento de clique
    def mouse_press_event3(self, event):
        if self.tabPagamentosSub.currentWidget() == self.tab_pagamento_form:
            if not self.tableWidget3.viewport().rect().contains(self.tableWidget3.mapFromParent(event.pos())):
                self.buttonBox3_delete.setVisible(False)
                self.tableWidget3.clearSelection()

    def reset_fields3(self):
        # Reseta todos os campos do formulário
        self.Nome3.clear()
        self.Total2.clear()
        # Resetar ComboBoxes para o primeiro item
        if self.Opções.count() > 0:
           self.Opções.setCurrentIndex(0)
        if self.Status2.count() > 0:
           self.Status2.setCurrentIndex(0)
           # Resetar Data para hoje
        self.Data2.setDate(QtCore.QDate.currentDate())

    def save_data3(self):
        """Salva os dados no banco de dados"""
        # Obter valores dos campos
        nome_cliente = self.Nome3.text()
        forma_pagamento = self.Opções.currentText()
        total = self.Total2.text().replace(".", "").replace(",", ".")
        data_pagamento = self.Data2.text()
        status_pagamento = self.Status2.currentText()

        if not nome_cliente or not total:  # Validar campos obrigatórios
            QtWidgets.QMessageBox.warning(
                None, "Aviso", "Nome e Valor são obrigatórios!")
            return

        # Conectar ao banco de dados usando a função `connect_to_db`
        connection = connect_db2()
        if not connection:
            QtWidgets.QMessageBox.critical(
                None, "Erro", "Não foi possível conectar ao banco de dados.")
            return

        try:
            # Inicializar cursor
            cursor = connection.cursor()
            query = """
            INSERT INTO pagamentos (nome_cliente, forma_pagamento, total,
            data_pagamento, status_pagamento)
            VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(query, (nome_cliente, forma_pagamento, total,
                                   data_pagamento, status_pagamento))
            codigo_cadastro = cursor.lastrowid
            connection.commit()

            try:
                self.widget_dashboard.atualizar_dashboard()
            except:
                pass

            # Feedback ao usuário
            QtWidgets.QMessageBox.information(
                None, "Sucesso", "Dados salvos com sucesso!")

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                None, "Erro", f"Erro ao salvar os dados: {e}")

        finally:
            # Garantir que o cursor e a conexão sejam fechados
            if 'cursor' in locals() and cursor:
                cursor.close()
            if connection:
                connection.close()

        row_position = self.tableWidget3.rowCount()
        self.tableWidget3.insertRow(row_position)
        self.tableWidget3.setItem(
            row_position, 0, QtWidgets.QTableWidgetItem(str(codigo_cadastro).zfill(4)))
        self.tableWidget3.setItem(
            row_position, 1, QtWidgets.QTableWidgetItem(self.Nome3.text()))
        self.tableWidget3.setItem(
            row_position, 2, QtWidgets.QTableWidgetItem(self.Opções.currentText()))
        self.tableWidget3.setItem(
            row_position, 3, QtWidgets.QTableWidgetItem(self.Total2.text()))
        data_pagamento = self.Data2.text()
        self.tableWidget3.setItem(
            row_position, 4, QtWidgets.QTableWidgetItem(data_pagamento))
        self.tableWidget3.setItem(
            row_position, 5, QtWidgets.QTableWidgetItem(self.Status2.currentText()))

        self.clear_fields3()

        # Criar a fonte mais grossa (bold)
        bold_font = QtGui.QFont()
        bold_font.setBold(True)

        # Colorir a linha dependendo do status e aplicar a fonte grossa
        for col in range(self.tableWidget3.columnCount()):
            item = self.tableWidget3.item(row_position, 5)
            item.setFont(bold_font)  # Aplica a fonte grossa

         # Colorir a linha dependendo do status
        if status_pagamento == "Pago":
            for col in range(self.tableWidget3.columnCount()):
                item = self.tableWidget3.item(row_position, 5)
                # Verde para 'Concluído'
                item.setForeground(QtGui.QColor(0, 128, 0))
        elif status_pagamento == "Vai Pagar":
            for col in range(self.tableWidget3.columnCount()):
                item = self.tableWidget3.item(row_position, 5)
                # Laranja para 'Em andamento'
                item.setForeground(QtGui.QColor(255, 135, 0))
        elif status_pagamento == "Nao Pagou":
            for col in range(self.tableWidget3.columnCount()):
                item = self.tableWidget3.item(row_position, 5)
                # Vermelho para 'Cancelado'
                item.setForeground(QtGui.QColor(255, 0, 0))
        self.clear_fields3()

    def update_color2(self, item):
        # Dicionário de cores para cada status
        status_colors = {
            "Pago": QtGui.QColor(0, 128, 0),        # Verde
            "Vai Pagar": QtGui.QColor(255, 135, 0),  # Laranja
            "Nao Pagou": QtGui.QColor(255, 0, 0),  # Vermelho
        }
        """Atualiza a cor do texto na célula editada"""
        if item.column() == 5:  # Apenas para a coluna 5
            status_pagamento = item.text()
            # Obtém a cor correspondente, se existir
            color = status_colors.get(status_pagamento, None)
            if color:
                item.setForeground(color)  # Aplica a cor
            else:
                # Preto como padrão para valores não definidos
                item.setForeground(QtGui.QColor(0, 0, 0))

    def load_data3(self):
        conn = connect_db2()
        cursor = conn.cursor()
        try:
            self.tableWidget3.setRowCount(0)
            cursor.execute(
                "SELECT codigo_cadastro, "
                "nome_cliente, forma_pagamento, total, data_pagamento, status_pagamento "
                "FROM pagamentos ORDER BY codigo_cadastro ASC"
            )
            rows = cursor.fetchall()

            # Adiciona os dados na tabela da interface
            self.tableWidget3.setRowCount(len(rows))
            # Desativa a ordenação automática antes de carregar
            self.tableWidget3.setSortingEnabled(False)
            for row_index, row_data in enumerate(rows):
                for col_index, col_data in enumerate(row_data):
                    item: None
                    if col_index == 0 and col_data:
                        formatted_code = str(col_data).zfill(4)
                        print(f"Codigo Formatado: {formatted_code}")

                    # Verifica se a coluna é de data e formata
                    if col_index == 4 and col_data:
                        try:
                            # Converte a data para o formato DD/MM/YYYY
                            col_data = datetime.strptime(
                                str(col_data), "%Y-%m-%d").strftime("%d/%m/%Y")
                        except ValueError:
                            col_data = "Data Inválida"  # Fallback para casos de erro
                        item = QtWidgets.QTableWidgetItem(col_data)
                        # Formatação especial para "valor"
                    elif col_index == 3 and col_data:  # Coluna de valor
                        formatted_value = f"R${float(col_data):.2f}".replace(
                            ".", ",")
                        item = QtWidgets.QTableWidgetItem(formatted_value)
                    else:
                        item = QtWidgets.QTableWidgetItem(str(col_data))


                    # Aplica cor ao status (coluna 5)
                    if col_index == 5:  # Coluna de status
                        color = self.get_status_color2(col_data)
                        item.setForeground(color)
                        font = QtGui.QFont()
                        font.setBold(True)
                        item.setFont(font)
                    self.tableWidget3.setItem(
                        row_index, col_index, item)

                    # Adiciona o item à célula correspondente
                    for row in range(self.tableWidget3.rowCount()):
                        item = self.tableWidget3.item(
                            row, 0)  # Coluna do código
                        if item:
                            # Aplica a formatação final
                            item.setText(item.text().zfill(4))

        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
        finally:
            cursor.close()
            conn.close()

    def get_status_color2(self, status):
        """Retorna a cor correspondente ao status."""
        status_colors = {
            "Pago": QtGui.QColor(0, 128, 0),        # Verde
            "Vai Pagar": QtGui.QColor(255, 135, 0),  # Laranja
            "Nao Pagou": QtGui.QColor(255, 0, 0),       # Vermelho
        }
        # Preto como padrão
        return status_colors.get(status, QtGui.QColor(0, 0, 0))

    def update_database(self, item):
        """Atualiza o banco de dados com as alterações feitas na tabela."""
        try:
            from datetime import datetime

            # Desabilitar a ordenação antes de editar
            self.tableWidget3.setSortingEnabled(False)

            # Obter a linha, coluna e novo valor
            row = item.row()
            column = item.column()
            new_value = item.text()

            if column == 0:
                return

            # Mapear as colunas do banco p/ colunas QTableWidget
            column_mapping = {
                0: "codigo_cadastro",
                1: "nome_cliente",
                2: "forma_pagamento",
                3: "total",
                4: "data_pagamento",
                5: "status_pagamento",
            }

            # Obter o nome da coluna correspondente no banco de dados
            column_name = column_mapping.get(column, None)
            if not column_name:
                return  # Ignorar colunas sem mapeamento
            # identificador único
            codigo_item = self.tableWidget3.item(row, 0)
            if not codigo_item:
                return
            # Garante que o código tenha 4 dígitos, se for necessário
            codigo = int(codigo_item.text())

            # Atualizar o banco de dados
            conn = connect_db2()
            if not conn:
                return
            cursor = conn.cursor()

            if column == 3:  # Coluna de valor
                try:
                    # Remover a formatação (R$ e , )
                    raw_value = new_value.replace("R$", "").replace(
                        ".", "").replace(",", ".").strip()
                    new_value_numeric = float(raw_value)
                    # Atualizar o banco com o valor numérico
                    cursor.execute(
                        f"UPDATE pagamentos SET {column_name} = ? WHERE codigo_cadastro = ?",
                        (new_value_numeric, codigo)
                    )
                    conn.commit()

                    # Atualizar o valor formatado na interface
                    formatted_value = f"R$ {new_value_numeric:,.2f}".replace(
                        ",", "X").replace(".", ",").replace("X", ".")
                    item.setText(formatted_value)
                except ValueError:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Erro",
                        "Valor inválido. Use apenas números.",
                        buttons=QtWidgets.QMessageBox.Ok
                    )
                    return
            else:
                # Atualizar outras colunas
                cursor.execute(
                    f"UPDATE pagamentos SET {column_name} = ? WHERE codigo_cadastro = ?",
                    (new_value, codigo)
                )
                conn.commit()

            if column == 4:  # Coluna de data
                try:
                    if "-" in new_value:  # Formato ISO (YYYY-MM-DD)
                        dt = datetime.strptime(new_value, "%Y-%m-%d")
                    else:  # Formato esperado (DD/MM/YYYY)
                        dt = datetime.strptime(new_value, "%d/%m/%Y")
                    db_value = dt.strftime("%Y-%m-%d")
                    formatted_date = dt.strftime("%d/%m/%Y")
                    item.setText(formatted_date)
                    cursor.execute(
                        f"UPDATE pagamentos SET {column_name} = ? WHERE codigo_cadastro = ?",
                        (db_value, codigo)
                    )

                except ValueError:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Erro",
                        "Formato de data inválido. Use DD/MM/YYYY.",
                        buttons=QtWidgets.QMessageBox.Ok
                    )
                    self.load_data2()
                    return
            elif column == 5:  # Coluna de status
                color = self.get_status_color2(new_value)
                item.setForeground(color)
                font = QtGui.QFont()
                font.setBold(True)
                item.setFont(font)

        except ValueError as ve:
            QtWidgets.QMessageBox.warning(
                self,
                "Erro",
                f"Erro de valor: {ve}",
                buttons=QtWidgets.QMessageBox.Ok
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao atualizar o banco: {e}",
                buttons=QtWidgets.QMessageBox.Ok
            )
        finally:
            # Garantir que a ordenação permaneça desativada
            self.tableWidget3.setSortingEnabled(False)
            if 'cursor' in locals() and cursor:
                cursor.close()
                conn.commit()
                try:
                    self.widget_dashboard.atualizar_dashboard()
                except:
                    pass

    def delete_order3(self):
        """Exclui o(s) pagamento(s) selecionado(s) do banco de dados e atualiza a tabela."""
        selected_rows = sorted(
            set(item.row() for item in self.tableWidget3.selectedItems()), reverse=True
        )

        if not selected_rows:
            QtWidgets.QMessageBox.warning(
                None, "Aviso", "Nenhum pagamento selecionado!")
            return

            # Criar caixa de diálogo de confirmação
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Question)
        msg_box.setWindowTitle("Confirmação")
        msg_box.setText(
            "Tem certeza que deseja excluir o(s) pagamento(s) selecionado(s)?")

        # Criar botões personalizados
        btn_sim = msg_box.addButton("Sim", QtWidgets.QMessageBox.YesRole)
        btn_cancelar = msg_box.addButton(
            "Cancelar", QtWidgets.QMessageBox.RejectRole)

        msg_box.exec()  # Exibir a caixa de diálogo

        # Se o usuário pressionar "Cancelar", interrompe a função
        if msg_box.clickedButton() == btn_cancelar:
            return

        conn = connect_db2()
        if not conn:
            QtWidgets.QMessageBox.critical(
                None, "Erro", "Falha ao conectar ao banco de dados.")
            return

        try:
            cursor = conn.cursor()
            fazer_backup(DB_PATH, tipo="diario")
            for row in selected_rows:
                # Obtenha o nome do cliente para exclusão
                # Assumindo que o nome está na coluna 0
                codigo_pagamento = self.tableWidget3.item(row, 0).text()
                cursor.execute(
                    "DELETE FROM pagamentos WHERE codigo_cadastro = ?", (codigo_pagamento,))

            conn.commit()
            try:
                self.widget_dashboard.atualizar_dashboard()
            except:
                pass
            QtWidgets.QMessageBox.information(
                None, "Sucesso", "Pagamento(s) excluído(s) com sucesso!")

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                None, "Erro", f"Erro ao excluir pagamento(s): {e}")
        finally:
            conn.close()

        # Recarregar a tabela para garantir consistência
        self.load_data3()

    def clear_fields3(self):
        """Limpa os campos do formulário."""
        self.Nome3.clear()
        self.Total2.clear()
        # Resetar ComboBoxes para o primeiro item
        if self.Opções.count() > 0:
           self.Opções.setCurrentIndex(0)
        if self.Status2.count() > 0:
           self.Status2.setCurrentIndex(0)
           # Resetar Data para hoje
        self.Data2.setDate(QtCore.QDate.currentDate())

    def resetar_tabela_e_ids3(self):
        from datetime import datetime, date

        msg_box3 = QMessageBox()
        msg_box3.setWindowTitle("Confirmar Reset")
        msg_box3.setText("Quer apagar TODOS os pagamentos e resetar os IDs clique em 'Yes', "
                        "quer apenas gerar relatorio clique em 'No'")
        msg_box3.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

        # Aumentar tamanho da fonte
        font = QFont()
        font.setPointSize(14)  # Aqui você pode aumentar ainda mais
        msg_box3.setFont(font)
        resposta = msg_box3.exec()

        if resposta == QMessageBox.Cancel:
            return  # Sai da função

        conn = connect_db2()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT codigo_cadastro, nome_cliente, forma_pagamento, total, data_pagamento, status_pagamento
            FROM pagamentos
        """)
        dados = cursor.fetchall()

        if not dados:
            QMessageBox.information(None, "Aviso", "Não há dados para gerar o relatório.")
        else:
            # === 1️⃣ Formatar datas no padrão dd/mm/aaaa ===
            dados_formatados = []
            for linha in dados:
                codigo_cadastro, nome_cliente, forma_pagamento, total, data_pagamento, status_pagamento = linha

                # Converter "2000-05-14" → "14/05/2000"
                if isinstance(data_pagamento, (datetime, date)):
                    data_pagamento = data_pagamento.strftime("%d/%m/%Y")
                else:
                    try:
                        data_pagamento = datetime.strptime(str(data_pagamento), "%Y-%m-%d").strftime("%d/%m/%Y")
                    except Exception:
                        data_pagamento = str(data_pagamento)  # Se já estiver formatada

                dados_formatados.append([
                    codigo_cadastro, nome_cliente, forma_pagamento, total, data_pagamento, status_pagamento
                ])
            # === 2️⃣ Criar o relatório (imagem .png) ===
            from datetime import datetime
            import pandas as pd
            import os
            from PyQt5.QtGui import QDesktopServices
            from PyQt5.QtCore import QUrl
            from openpyxl.styles import Font, Alignment, Border, Side
            from openpyxl.utils import get_column_letter


            meses = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
            agora = datetime.now()
            mes_atual = f"{meses[agora.month]} de {agora.year}"

            colunas = ["Codigo_Cadastro", "Nome_Cliente", "Forma_Pagamento", "Total", "Data_Pagamento", "Status_Pagamento"]

            # === 🔧 Quebrar textos muito longos (endereços, emails, etc.) ===
            dados_ajustados = []
            for linha in dados_formatados:
                codigo_cadastro, nome_cliente, forma_pagamento, total, data_pagamento, status_pagamento = linha

                dados_ajustados.append([
                    codigo_cadastro,
                    "\n".join(textwrap.wrap(str(nome_cliente), 40)),
                    forma_pagamento,
                    total,
                    data_pagamento,
                    status_pagamento
                ])
            df = pd.DataFrame(dados_ajustados, columns=colunas)

            # === 3️⃣ Criar pasta "Relatórios" na Área de Trabalho ===
            desktop = os.path.join(os.environ["USERPROFILE"], "OneDrive", "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")

            pasta = os.path.join(desktop, "Relatórios")
            os.makedirs(pasta, exist_ok=True)
            caminho_arquivo = os.path.join(pasta, f"Relatorio_Pagamentos_{mes_atual}.xlsx")
            df = pd.DataFrame(dados_ajustados, columns=colunas)

            # === 3️⃣ Criar pasta "Relatórios" na Área de Trabalho ===
            desktop = os.path.join(os.environ["USERPROFILE"], "OneDrive", "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")

            pasta = os.path.join(desktop, "Relatórios")
            os.makedirs(pasta, exist_ok=True)
            caminho_arquivo = os.path.join(pasta, f"Relatorio_Pagamentos_{mes_atual}.xlsx"
            )

            with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Pagamentos")

                workbook = writer.book
                worksheet = writer.sheets["Pagamentos"]
                # Estilos
                header_font = Font(bold=True)
                center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
                text_align = Alignment(vertical="top", wrap_text=True)

                thin_border = Border(
                    left=Side(style="thin"),
                    right=Side(style="thin"),
                    top=Side(style="thin"),
                    bottom=Side(style="thin")
                )
                # Cabeçalho
                for col_num, coluna in enumerate(colunas, start=1):
                    cell = worksheet.cell(row=1, column=col_num)
                    cell.value = coluna
                    cell.font = header_font
                    cell.alignment = center_align
                    cell.border = thin_border

                    # largura da coluna
                    worksheet.column_dimensions[get_column_letter(col_num)].width = 25

                                    # Dados
                for row in worksheet.iter_rows(
                    min_row=2,
                    max_row=worksheet.max_row,
                    min_col=1,
                    max_col=len(colunas)
                ):
                    for cell in row:
                        cell.alignment = text_align
                        cell.border = thin_border

                # Congelar cabeçalho
                worksheet.freeze_panes = "A2"
                # Autofiltro
                worksheet.auto_filter.ref = f"A1:{get_column_letter(len(colunas))}{worksheet.max_row}"

            QDesktopServices.openUrl(QUrl.fromLocalFile(caminho_arquivo))

            QMessageBox.information(
                None,
                "Relatório Gerado",
                f"Relatório gerado e aberto no Excel:\n\n{caminho_arquivo}"
            )

        # === 4️⃣ Resetar a tabela e IDs ===
        if resposta == QMessageBox.Yes:
            try:
                conn.commit()
                conn.close()

                fazer_backup(DB_PATH, tipo="reset")

                conn = connect_db2()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM pagamentos;")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='pagamentos';")
                conn.commit()
                QMessageBox.information(None, "Resetado com Sucesso",
                                        "Todos os dados foram apagados e os IDs resetados para 1.")
            except Exception as e:
                QMessageBox.critical(None, "Erro", f"Ocorreu um erro ao resetar os dados: {str(e)}")
            finally:
                cursor.close()
                conn.close()
                self.load_data3()
                self.tableWidget3.setRowCount(0)
                try:
                    self.widget_dashboard.atualizar_dashboard()
                except:
                    pass


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
