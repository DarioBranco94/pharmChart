import sys
import sqlite3
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QListWidget, QTabWidget, QCheckBox, QSplitter, QGroupBox, QSizePolicy,
    QFrame, QListWidgetItem
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt

DB_PATH = "carrello.db"

def get_or_create_giro():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id FROM Giri WHERE completato = 0 ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        conn.close()
        return row[0]
    cur.execute("INSERT INTO Giri (data, completato) VALUES (?, 0)", (date.today().isoformat(),))
    conn.commit()
    gid = cur.lastrowid
    conn.close()
    return gid

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Carrello Farmaci - GUI Qt + SQLite")
        self.resize(1600, 900)

        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute("DELETE FROM GiroPazienti")
        self.cursor.execute("DELETE FROM Prescrizioni")
        self.cursor.execute("DELETE FROM Giri")
        self.conn.commit()
        self.giro_id = get_or_create_giro()

        self.allocazioni = {}
        self.farmaci_da_somministrare = []
        self.farmaco_corrente_index = 0

        self.view = QWebEngineView()
        self.view.load(QUrl("http://localhost:3000"))
        self.web_frame = QFrame()
        web_layout = QVBoxLayout()
        web_layout.setContentsMargins(0, 0, 0, 0)
        web_layout.setSpacing(0)
        web_layout.addWidget(self.view)
        self.web_frame.setLayout(web_layout)
        self.web_frame.setMinimumHeight(600)
        self.web_frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 8px; background-color: #ffffff; }")

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 6px;
                background: #fafafa;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #ccc;
                padding: 8px 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                font-weight: bold;
                color: #000;
            }
        """)
        self.tabs.setStyleSheet(""" /* identico */ """)
        self.tabs.addTab(self._create_caricamento_tab(), "1. Caricamento")
        self.tabs.addTab(self._create_somministrazione_tab(), "2. Somministrazione")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.web_frame)
        splitter.setSizes([1000, 600])
        self.setCentralWidget(splitter)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 14px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QGroupBox {
                border: 1px solid lightgray;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
                font-weight: bold;
                color: #333;
            }
            QListWidget, QComboBox {
                padding: 6px;
                border: 1px solid lightgray;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox {
                padding: 5px;
            }
            QLabel {
                font-size: 13px;
                color: #222;
            }
        """)

    def _create_caricamento_tab(self):
        layout = QHBoxLayout()
        sx_group = QGroupBox("Seleziona Pazienti del Giro")
        sx = QVBoxLayout()

        self.dropdown_pazienti = QComboBox()
        self.dropdown_pazienti.addItems(["Mario Rossi", "Lucia Verdi", "Anna Bianchi", "Giuseppe Neri"])
        sx.addWidget(self.dropdown_pazienti)

        self.btn_aggiungi_paziente = QPushButton("Aggiungi Paziente")
        self.btn_aggiungi_paziente.clicked.connect(self.aggiungi_paziente)
        sx.addWidget(self.btn_aggiungi_paziente)

        self.lista_pazienti = QListWidget()
        sx.addWidget(self.lista_pazienti)

        self.btn_carica = QPushButton("Recupera Farmaci da API")
        self.btn_carica.clicked.connect(self.carica_medicinali)
        sx.addWidget(self.btn_carica)

        sx_group.setLayout(sx)

        dx_group = QGroupBox("Inserimento Farmaci")
        dx = QVBoxLayout()
        self.box_medicinali = QListWidget()
        dx.addWidget(self.box_medicinali)

        self.checkbox_caricato = QCheckBox("Farmaco inserito")
        self.checkbox_caricato.setEnabled(False)
        self.checkbox_caricato.stateChanged.connect(self.conferma_caricamento_farmaco)
        dx.addWidget(self.checkbox_caricato)

        self.btn_prossimo_farmaco = QPushButton("→ Prossimo Farmaco")
        self.btn_prossimo_farmaco.setEnabled(False)
        self.btn_prossimo_farmaco.clicked.connect(self.prossimo_farmaco)
        dx.addWidget(self.btn_prossimo_farmaco)

        dx_group.setLayout(dx)
        layout.addWidget(sx_group, 2)
        layout.addWidget(dx_group, 3)
        container = QWidget()
        container.setLayout(layout)
        return container

    def _create_somministrazione_tab(self):
        layout = QVBoxLayout()
        group = QGroupBox("Somministrazione Farmaci")
        group_layout = QVBoxLayout()

        form_layout = QHBoxLayout()
        label_paz = QLabel("Paziente:")
        label_paz.setFixedWidth(80)
        self.combo_pazienti = QComboBox()
        self.combo_pazienti.currentIndexChanged.connect(self.avvia_somministrazione)
        form_layout.addWidget(label_paz)
        form_layout.addWidget(self.combo_pazienti)

        self.label_farmaco_corrente = QLabel("Farmaco da somministrare:")
        self.label_farmaco_corrente.setStyleSheet("font-size: 15px; font-weight: bold; margin-top: 10px;")

        self.lista_farmaci_stato = QListWidget()
        self.lista_farmaci_stato.setFixedHeight(200)
        self.lista_farmaci_stato.itemClicked.connect(self.visualizza_farmaco_da_lista)
        self.cassetto_aperto_corrente = None

        self.btn_conferma_somministrazione = QPushButton("✓ Somministrato")
        self.btn_conferma_somministrazione.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_conferma_somministrazione.setFixedHeight(40)
        self.btn_conferma_somministrazione.clicked.connect(self.prossimo_farmaco_da_somministrare)

        group_layout.addLayout(form_layout)
        group_layout.addWidget(self.label_farmaco_corrente)
        group_layout.addWidget(self.lista_farmaci_stato)
        group_layout.addWidget(self.btn_conferma_somministrazione)

        group.setLayout(group_layout)
        layout.addWidget(group)

        container = QWidget()
        container.setLayout(layout)
        return container

    def aggiungi_paziente(self):
        nome = self.dropdown_pazienti.currentText()
        self.cursor.execute("INSERT OR IGNORE INTO Pazienti(nome) VALUES (?)", (nome,))
        self.conn.commit()
        self.cursor.execute("SELECT id FROM Pazienti WHERE nome = ?", (nome,))
        pid = self.cursor.fetchone()[0]
        self.cursor.execute("INSERT OR IGNORE INTO GiroPazienti (giro_id, paziente_id) VALUES (?, ?)", (self.giro_id, pid))
        self.conn.commit()
        self.lista_pazienti.addItem(nome)
        self.combo_pazienti.addItem(nome)


    def visualizza_farmaco_da_lista(self, item):
        nome_farmaco = item.text().strip("✅⏳ ").strip()
        self.label_farmaco_corrente.setText(f"Farmaco da somministrare: {nome_farmaco}")

        info = self.allocazioni.get(nome_farmaco)
        if not info:
            return

        cassetto_target = f"Cassetto{info['cassetto']}"

        # 🔁 Se si sta cambiando cassetto, chiudi quello precedente
        if self.cassetto_aperto_corrente and self.cassetto_aperto_corrente != cassetto_target:
            script_chiudi = f'window.chiudiCassetto("{self.cassetto_aperto_corrente}");'
            self.view.page().runJavaScript(script_chiudi)

        # 🧼 Spegni sempre lo scomparto attivo prima di illuminarne uno nuovo
        if self.cassetto_aperto_corrente:
            script_spegni = f'window.spegniScompartoAssociato("{self.cassetto_aperto_corrente}");'
            self.view.page().runJavaScript(script_spegni)

        # ✅ Apri il cassetto e illumina lo scomparto corretto
        script_apri = f'window.apriScomparto({info["cassetto"]}, {info["scomparto"]});'
        self.view.page().runJavaScript(script_apri)

        # 🔁 Aggiorna stato cassetto aperto
        self.cassetto_aperto_corrente = cassetto_target

            
    def carica_medicinali(self):
        from random import sample
        farmaci_possibili = ["Paracetamolo", "Ibuprofene", "Amoxicillina", "Aspirina", "Omeprazolo", "Metformina"]
        self.box_medicinali.clear()
        farmaci_giro = []
        scomparto_id = 1

        for i in range(self.lista_pazienti.count()):
            nome = self.lista_pazienti.item(i).text()
            self.cursor.execute("SELECT id FROM Pazienti WHERE nome = ?", (nome,))
            pid = self.cursor.fetchone()[0]
            farmaci = sample(farmaci_possibili, 3)

            for f in farmaci:
                self.cursor.execute("INSERT OR IGNORE INTO Farmaci(nome) VALUES (?)", (f,))
                self.cursor.execute("SELECT id FROM Farmaci WHERE nome = ?", (f,))
                fid = self.cursor.fetchone()[0]

                cassetto = ((scomparto_id - 1) // 6) + 1
                scomparto = scomparto_id
                scomparto_id += 1

                self.cursor.execute("""
                    INSERT OR IGNORE INTO Prescrizioni
                    (giro_id, paziente_id, farmaco_id, caricato, somministrato, cassetto, scomparto)
                    VALUES (?, ?, ?, 0, 0, ?, ?)
                """, (self.giro_id, pid, fid, cassetto, scomparto))

                self.allocazioni[f] = {"cassetto": cassetto, "scomparto": scomparto}
                farmaci_giro.append(f)

        self.conn.commit()
        self.box_medicinali.addItems(farmaci_giro)
        if self.box_medicinali.count() > 0:
            self.box_medicinali.setCurrentRow(0)
            self.visualizza_farmaco_corrente()  # ✅ abilita checkbox e disegna

    def visualizza_farmaco_corrente(self):
        farmaco = self.box_medicinali.currentItem().text()
        if farmaco in self.allocazioni:
            info = self.allocazioni[farmaco]
            script = f'window.apriScomparto({info["cassetto"]}, {info["scomparto"]});'
            self.view.page().runJavaScript(script)

            # ✅ Riattiva il checkbox ogni volta che si seleziona un farmaco
            self.checkbox_caricato.setEnabled(True)
            self.checkbox_caricato.setChecked(False)
            self.btn_prossimo_farmaco.setEnabled(False)

    def conferma_caricamento_farmaco(self):
        if self.checkbox_caricato.isChecked():
            farmaco = self.box_medicinali.currentItem().text()
            self.btn_prossimo_farmaco.setEnabled(True)

            # Ottieni ID farmaco
            self.cursor.execute("SELECT id FROM Farmaci WHERE nome = ?", (farmaco,))
            farmaco_id = self.cursor.fetchone()[0]

            for i in range(self.lista_pazienti.count()):
                nome = self.lista_pazienti.item(i).text()
                self.cursor.execute("SELECT id FROM Pazienti WHERE nome = ?", (nome,))
                paziente_id = self.cursor.fetchone()[0]

                self.cursor.execute("""
                    UPDATE Prescrizioni 
                    SET caricato = 1, caricato_timestamp = CURRENT_TIMESTAMP
                    WHERE giro_id = ? AND paziente_id = ? AND farmaco_id = ?
                """, (self.giro_id, paziente_id, farmaco_id))

            self.conn.commit()

            # 🔒 Chiudi cassetto nel modello 3D
            info = self.allocazioni.get(farmaco)
            if info:
                script = f'window.chiudiCassetto("Cassetto{info["cassetto"]}");'
                self.view.page().runJavaScript(script)

    def prossimo_farmaco(self):
        row = self.box_medicinali.currentRow()
        if row < self.box_medicinali.count() - 1:
            self.box_medicinali.setCurrentRow(row + 1)
            self.visualizza_farmaco_corrente()
        else:
            self.checkbox_caricato.setEnabled(False)
            self.btn_prossimo_farmaco.setEnabled(False)

    def avvia_somministrazione(self):
        paziente = self.combo_pazienti.currentText()
        self.cursor.execute("SELECT id FROM Pazienti WHERE nome = ?", (paziente,))
        self.pid_corrente = self.cursor.fetchone()[0]
        self.cursor.execute("""
            SELECT f.nome FROM Prescrizioni p
            JOIN Farmaci f ON f.id = p.farmaco_id
            WHERE p.giro_id = ? AND p.paziente_id = ?
        """, (self.giro_id, self.pid_corrente))
        self.farmaci_da_somministrare = [r[0] for r in self.cursor.fetchall()]
        self.farmaco_corrente_index = 0
        self.mostra_farmaco_corrente()
        self.aggiorna_lista_farmaci_stato(paziente)

    def mostra_farmaco_corrente(self):
        if self.farmaco_corrente_index < len(self.farmaci_da_somministrare):
            farmaco = self.farmaci_da_somministrare[self.farmaco_corrente_index]
            info = self.allocazioni.get(farmaco)
            if not info:
                return

            cassetto_target = f"Cassetto{info['cassetto']}"

            if self.cassetto_aperto_corrente and self.cassetto_aperto_corrente != cassetto_target:
                script_chiudi = f'window.chiudiCassetto("{self.cassetto_aperto_corrente}");'
                self.view.page().runJavaScript(script_chiudi)

            if self.cassetto_aperto_corrente:
                script_spegni = f'window.spegniScompartoAssociato("{self.cassetto_aperto_corrente}");'
                self.view.page().runJavaScript(script_spegni)

            script_apri = f'window.apriScomparto({info["cassetto"]}, {info["scomparto"]});'
            self.view.page().runJavaScript(script_apri)
            self.cassetto_aperto_corrente = cassetto_target

            self.label_farmaco_corrente.setText(f"Farmaco da somministrare: {farmaco}")
                
    def prossimo_farmaco_da_somministrare(self):
        if self.farmaco_corrente_index >= len(self.farmaci_da_somministrare):
            return

        farmaco = self.farmaci_da_somministrare[self.farmaco_corrente_index]
        self.cursor.execute("SELECT id FROM Farmaci WHERE nome = ?", (farmaco,))
        farmaco_id = self.cursor.fetchone()[0]

        self.cursor.execute("""
            UPDATE Prescrizioni 
            SET somministrato = 1, timestamp = CURRENT_TIMESTAMP
            WHERE giro_id = ? AND paziente_id = ? AND farmaco_id = ?
        """, (self.giro_id, self.pid_corrente, farmaco_id))
        self.conn.commit()

        # 🔒 Chiudi cassetto attuale
        if self.cassetto_aperto_corrente:
            script_chiudi = f'window.chiudiCassetto("{self.cassetto_aperto_corrente}");'
            self.view.page().runJavaScript(script_chiudi)
            self.cassetto_aperto_corrente = None

        self.farmaco_corrente_index += 1
        self.mostra_farmaco_corrente()
        self.aggiorna_lista_farmaci_stato(self.combo_pazienti.currentText())

    def aggiorna_lista_farmaci_stato(self, paziente):
        self.lista_farmaci_stato.clear()
        for i, f in enumerate(self.farmaci_da_somministrare):
            stato = "✅" if i < self.farmaco_corrente_index else "⏳"
            item = QListWidgetItem(f"{stato} {f}")
            self.lista_farmaci_stato.addItem(item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())