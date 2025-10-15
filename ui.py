# Salve este arquivo como: ui.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QLabel, QLineEdit, QMessageBox, QDialog, QTextEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from utils import carregar_placares
from game import Game

class PlacaresDialog(QDialog):
    """Janela de diálogo para exibir os placares."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Placares - Top 10")
        self.setFixedSize(360, 420)
        self.setStyleSheet("background-color: #0A0A0A; color: #FFD700;")
        layout = QVBoxLayout()
        title = QLabel("🏆 Placar de Líderes")
        title.setFont(QFont("Impact", 20))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        entries = carregar_placares()
        
        if not entries:
            txt = QLabel("Nenhum placar registado ainda.")
            txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(txt)
        else:
            entries_sorted = sorted(entries, key=lambda x: x[1], reverse=True)[:10]
            text_edit = QTextEdit(); text_edit.setReadOnly(True)
            text_edit.setStyleSheet("background-color: #111; color: #FFD700; font-family: 'Courier New', monospace; border: 1px solid #FFD700; padding: 5px;")
            content = "\n".join([f"{i+1:2d}. {n:<12}  {p:6d}" for i, (n, p) in enumerate(entries_sorted)])
            text_edit.setText(content); layout.addWidget(text_edit)
            
        btn_close = QPushButton("Fechar")
        btn_close.setStyleSheet("background-color:#222; color: yellow; border:1px solid yellow; padding:8px;")
        btn_close.clicked.connect(self.accept); layout.addWidget(btn_close)
        self.setLayout(layout)

class MenuPrincipal(QWidget):
    """A janela principal do menu do jogo (DEPENDÊNCIA de Game)."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pac-Man Jason"); self.setFixedSize(420, 380)
        self.layout = QVBoxLayout(); self.setStyleSheet("background-color: #0A0A0A; color: white;")
        self._setup_ui()
        self.btn_jogar.clicked.connect(self.on_jogar)
        self.btn_placares.clicked.connect(self.on_placares)
        self.btn_sair.clicked.connect(self.close)

    def _setup_ui(self):
        titulo = QLabel("PAC-MAN"); titulo.setFont(QFont("Impact", 48, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter); titulo.setStyleSheet("color: #FFD700;")
        self.layout.addWidget(titulo)
        
        subtitle = QLabel("A Vingança de Jason"); subtitle.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter); subtitle.setStyleSheet("color: #FF4444; margin-bottom: 15px;")
        self.layout.addWidget(subtitle)
        
        self.nome_input = QLineEdit(); self.nome_input.setPlaceholderText("Digite o seu nome")
        self.nome_input.setMaxLength(12); self.nome_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nome_input.setStyleSheet("padding:10px; font-size:16px; background:#111; color:#FFD700; border:1px solid #444; border-radius: 5px;")
        self.layout.addWidget(self.nome_input)
        
        btn_container = QHBoxLayout()
        self.btn_jogar = QPushButton("🎮 Jogar"); self.btn_placares = QPushButton("🏆 Placares"); self.btn_sair = QPushButton("❌ Sair")
        button_style = "QPushButton { background-color: #FFD700; color: black; border: none; padding: 12px; font-size: 16px; font-weight: bold; border-radius: 5px; } QPushButton:hover { background-color: #FFFF44; }"
        for btn in (self.btn_jogar, self.btn_placares, self.btn_sair):
            btn.setStyleSheet(button_style); btn.setFixedHeight(50); btn_container.addWidget(btn)
        
        self.layout.addLayout(btn_container); self.setLayout(self.layout)

    def on_jogar(self):
        nome = self.nome_input.text().strip()
        if not nome:
            QMessageBox.warning(self, "Aviso", "Digite o seu nome antes de jogar!")
            return
            
        self.hide()
        
        game_instance = Game(nome)
        score = game_instance.run()
        
        QMessageBox.information(self, "Fim de jogo", f"{nome}, a sua pontuação final foi: {score}")
        self.show()

    def on_placares(self):
        dlg = PlacaresDialog(self); dlg.exec()

