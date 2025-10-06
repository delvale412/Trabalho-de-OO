import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QRadioButton, QButtonGroup,
    QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from docx import Document
import fitz  # PyMuPDF

# ================================
# Funções de leitura
# ================================
def read_txt(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='latin1', errors='ignore') as f:
            return f.read()

def read_docx(path):
    doc = Document(path)
    return "\n".join([para.text for para in doc.paragraphs])

def read_pdf(path):
    text = ""
    pdf = fitz.open(path)
    for page in pdf:
        text += page.get_text("text") + "\n"
    return text

def load_document(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":
        return read_txt(path)
    elif ext == ".docx":
        return read_docx(path)
    elif ext == ".pdf":
        return read_pdf(path)
    else:
        return "Tipo de arquivo não suportado."

# ================================
# Funções de resumo usando subprocess
# ================================
MODEL_NAME = "llama3:8b"

def summarize_text_chunk(chunk, detail_level="Médio"):
    if detail_level == "Curto":
        detalhe_extra = "Resuma em no máximo 5 frases claras."
    elif detail_level == "Médio":
        detalhe_extra = "Resuma em 5 a 8 parágrafos, incluindo Introdução, Métodos, Resultados e Conclusão."
    else:
        detalhe_extra = (
            "Produza uma análise detalhada, com pelo menos 2500 palavras. "
            "Divida em seções com subtítulos claros, 3 a 6 parágrafos por seção, "
            "incluindo exemplos e comparações sem omitir informações."
        )

    prompt = f"{detalhe_extra}\n\nTrecho:\n{chunk}"

    try:
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME],
            input=prompt.encode("utf-8"),
            capture_output=True,
            check=True
        )
        return result.stdout.decode("utf-8").strip()
    except subprocess.CalledProcessError as e:
        return f"Erro ao gerar resumo: {e.stderr.decode('utf-8')}"

def summarize_final(partial_summaries):
    combined_text = "\n\n".join(partial_summaries)
    prompt = f"Combine e organize os seguintes resumos parciais em um resumo final detalhado:\n\n{combined_text}"
    try:
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME],
            input=prompt.encode("utf-8"),
            capture_output=True,
            check=True
        )
        return result.stdout.decode("utf-8").strip()
    except subprocess.CalledProcessError as e:
        return f"Erro ao gerar resumo final: {e.stderr.decode('utf-8')}"

def chunk_text(text, max_lines=500):
    lines = text.splitlines()
    for i in range(0, len(lines), max_lines):
        yield "\n".join(lines[i:i+max_lines])

# ================================
# Interface PyQt6
# ================================
class AnvisaInsightApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anvisa Insight - LLaMA3 8B")
        self.setGeometry(100, 100, 1000, 750)
        self.setStyleSheet("background-color:#f0f6f5; color:#012a36; font-family: 'Inter';")
        self.file_path = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15,15,15,15)
        main_layout.setSpacing(15)

        # ========================
        # Parte superior (20%)
        # ========================
        top_container = QVBoxLayout()
        top_container.setSpacing(10)

        # Upload
        self.upload_btn = QPushButton("Abrir arquivo")
        self.upload_btn.clicked.connect(self.open_file)
        self.upload_btn.setStyleSheet(self.button_style())
        self.upload_btn.setMinimumHeight(40)
        top_container.addWidget(self.upload_btn)
        top_container.addWidget(self.separator())

        # Nível de detalhe
        detail_layout = QVBoxLayout()
        lbl_detail = QLabel("Nível de detalhe:")
        lbl_detail.setStyleSheet("font-weight:bold;")
        detail_layout.addWidget(lbl_detail)
        self.detail_group = QButtonGroup()
        for i, level in enumerate(["Curto", "Médio", "Detalhado"]):
            btn = QRadioButton(level)
            btn.setStyleSheet("QRadioButton { padding:3px; } QRadioButton::indicator { width:15px; height:15px; }")
            if level == "Médio":
                btn.setChecked(True)
            self.detail_group.addButton(btn, i)
            detail_layout.addWidget(btn)
        top_container.addLayout(detail_layout)

        top_widget = QWidget()
        top_widget.setLayout(top_container)

        # ========================
        # Parte inferior (80%)
        # ========================
        bottom_container = QVBoxLayout()
        bottom_container.setSpacing(12)

        # Botão gerar resumo
        self.gen_btn = QPushButton("Gerar Resumo")
        self.gen_btn.clicked.connect(self.generate_summary)
        self.gen_btn.setStyleSheet(self.button_style())
        self.gen_btn.setMinimumHeight(40)
        bottom_container.addWidget(self.gen_btn)

        # Botão ver resumo
        self.view_btn = QPushButton("Ver Resumo")
        self.view_btn.setCheckable(True)
        self.view_btn.clicked.connect(self.toggle_summary)
        self.view_btn.setStyleSheet(self.button_style())
        self.view_btn.setMinimumHeight(35)
        self.view_btn.setVisible(False)
        bottom_container.addWidget(self.view_btn)

        # Scroll para o resumo
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("""
            background-color:#e1f0ef; color:#012a36; 
            border-radius:8px; padding:12px; font-size:14px;
        """)
        self.scroll_area.setWidget(self.text_area)
        self.scroll_area.setMaximumHeight(0)
        bottom_container.addWidget(self.scroll_area)


        # Botões copiar / salvar
        h_save = QHBoxLayout()
        h_save.setSpacing(15)
        self.copy_btn = QPushButton("Copiar para Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setStyleSheet(self.button_style())
        self.copy_btn.setMinimumHeight(35)
        h_save.addWidget(self.copy_btn)

        self.save_btn = QPushButton("Salvar Resumo")
        self.save_btn.clicked.connect(self.save_summary)
        self.save_btn.setStyleSheet(self.button_style())
        self.save_btn.setMinimumHeight(35)
        h_save.addWidget(self.save_btn)
        bottom_container.addLayout(h_save)

        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_container)

        main_layout.addWidget(top_widget, stretch=2)
        main_layout.addWidget(bottom_widget, stretch=8)

    # ==========================
    # Estilo e separadores
    # ==========================
    def button_style(self):
        return """
        QPushButton {
            background-color:#00796b; color:#ffffff; border-radius:10px; padding:8px 15px; font-weight:bold;
        }
        QPushButton:hover {
            background-color:#004d40;
        }
        """

    def separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color:#00796b;")
        return line

    # ==========================
    # Toggle resumo
    # ==========================
    def toggle_summary(self):
        if self.view_btn.isChecked():
            self.text_area.setMaximumHeight(int(self.height() * 0.7))
        else:
            self.text_area.setMaximumHeight(0)


    # ==========================
    # Ações do app
    # ==========================
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar arquivo", "", 
            "Documentos (*.txt *.docx *.pdf)"
        )
        if path:
            self.file_path = path
            QMessageBox.information(self, "Arquivo Selecionado", f"{os.path.basename(path)} selecionado com sucesso.")

    def generate_summary(self):
        if not self.file_path:
            QMessageBox.warning(self, "Atenção", "Selecione um arquivo primeiro.")
            return
        detail_id = self.detail_group.checkedId()
        detail_level = ["Curto","Médio","Detalhado"][detail_id]

        self.text_area.setText("Gerando resumo, aguarde...")
        QApplication.processEvents()
        content = load_document(self.file_path)

        # Chunking e resumos parciais
        chunks = list(chunk_text(content, max_lines=500))
        full_output = ""
        partial_summaries = []

        for idx, chunk in enumerate(chunks):
            resumo_parcial = summarize_text_chunk(chunk, detail_level)
            partial_summaries.append(resumo_parcial)
            full_output += f"\n\n### Resumo do Bloco {idx+1} ###\n{resumo_parcial}\n"

        # Resumo final consolidado
        final_summary = summarize_final(partial_summaries)

        full_output += "\n\n===========================\n### RESUMO FINAL CONSOLIDADO ###\n"
        full_output += final_summary

        self.text_area.setPlainText(full_output)
        self.view_btn.setVisible(True)
        self.view_btn.setChecked(True)
        self.toggle_summary()

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_area.toPlainText())
        QMessageBox.information(self, "Copiado", "Resumo copiado para a área de transferência!")

    def save_summary(self):
        if not self.text_area.toPlainText().strip():
            QMessageBox.warning(self, "Aviso", "Nenhum resumo disponível para salvar.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Salvar resumo", "resumo.txt", "Text Files (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_area.toPlainText())
            QMessageBox.information(self, "Salvo", f"Resumo salvo em {path}")


# ================================
# Execução
# ================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnvisaInsightApp()
    window.show()
    sys.exit(app.exec())
