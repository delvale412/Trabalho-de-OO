import sys
import fitz
import re
import html
from collections import Counter, defaultdict
from docx import Document
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QTextBrowser, QFileDialog, QMessageBox, QSplitter, QLabel,
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor

# =========================
# Funções de Leitura e Extração
# =========================
def read_pdf_full_with_pages(path):
    pdf = fitz.open(path)
    all_blocks_text = []
    pages_map = []
    for pno, page in enumerate(pdf, start=1):
        tables = page.find_tables()
        table_bboxes = [fitz.Rect(t.bbox) for t in tables]
        blocks = page.get_text("blocks", sort=True)
        for b in blocks:
            block_rect = fitz.Rect(b[:4])
            is_in_table = False
            for bbox in table_bboxes:
                if bbox.intersects(block_rect):
                    is_in_table = True
                    break
            if not is_in_table:
                block_text = b[4].strip()
                if block_text:
                    all_blocks_text.append(block_text)
                    for line in block_text.split('\n'):
                        clean_line = line.strip()
                        if clean_line:
                            pages_map.append((clean_line, pno))
    pdf.close()
    full_text = "\n".join(all_blocks_text)
    return full_text, pages_map

def read_docx_full_with_pages(path):
    doc = Document(path)
    text = ""
    pages = []
    for idx, para in enumerate(doc.paragraphs, start=1):
        line = para.text.strip()
        if line:
            text += line + "\n\n"
            pages.append((line, idx))
    return text, pages

def extract_pdf_metadata(path):
    pdf = fitz.open(path)
    info = pdf.metadata
    year = info.get("creationDate", "") or info.get("modDate", "")
    process = info.get("title", "")
    pdf.close()
    return year, process

def extract_header_info(full_text):
    try:
        end_of_header_match = re.search(r'I- IDENTIFICAÇÃO DO MEDICAMENTO|1\.?\s+PARA QUE ESTE MEDICAMENTO', full_text, re.IGNORECASE)
        if end_of_header_match:
            header_text = full_text[:end_of_header_match.start()]
        else:
            header_text = full_text[:400]
        lines = [line.strip() for line in header_text.splitlines() if line.strip()]
        return "\n".join(lines[:6])
    except Exception:
        return "Informações da bula não encontradas."

# =========================
# Funções de Processamento de Texto
# =========================
STOPWORDS = set(['a', 'o', 'e', 'em', 'de', 'do', 'da', 'dos', 'das', 'um', 'uma', 'uns', 'umas','com', 'para', 'por', 'no', 'na', 'nos', 'nas', 'ou', 'se', 'é'])
title_pattern = re.compile(r'^\s*(\d+[\.,\)]?)\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 \-\,\./\(\)]+$', re.IGNORECASE)
SECTION_TITLES = [
    "1. PARA QUE ESTE MEDICAMENTO É INDICADO?", "2. COMO ESTE MEDICAMENTO FUNCIONA?", "3. QUANDO NÃO DEVO USAR ESTE MEDICAMENTO?",
    "4. O QUE DEVO SABER ANTES DE USAR ESTE MEDICAMENTO?", "5. ONDE, COMO E POR QUANTO TEMPO POSSO GUARDAR ESTE MEDICAMENTO?",
    "6. COMO DEVO USAR ESTE MEDICAMENTO?", "7. O QUE DEVO FAZER QUANDO EU ME ESQUECER DE USAR ESTE MEDICAMENTO?",
    "8. QUAIS OS MALES QUE ESTE MEDICAMENTO PODE ME CAUSAR?", "9. O QUE FAZER SE ALGUÉM USAR UMA QUANTIDADE MAIOR DO QUE A INDICADA DESTE MEDICAMENTO?",
    "DIZERES LEGAIS"
]

def normalize_text(text):
    text = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)
    tokens = [t.lower() for t in text.split() if t.lower() not in STOPWORDS]
    tokens = [t[:-1] if t.endswith('s') else t for t in tokens]
    return " ".join(tokens)

def normalize_title(title):
    title = re.sub(r'[^\w\s]', '', title).strip().lower()
    return " ".join([t[:-1] if t.endswith('s') else t for t in title.split()])

def split_full_text_into_sections(full_text):
    lines = full_text.splitlines()
    sections = {title: [] for title in SECTION_TITLES}
    current = None
    norm_titles = {normalize_title(t): t for t in SECTION_TITLES}
    for raw_line in lines:
        line = raw_line.strip()
        if not line: continue
        lnorm = normalize_title(line)
        found_title = None
        match = title_pattern.match(line)
        if match:
            after_num_text = re.sub(r'^\s*\d+[\.,\)]?\s*', '', line).strip()
            n_after = normalize_title(after_num_text)
            best_match = None
            highest_score = 0
            for nt, orig in norm_titles.items():
                if n_after and (n_after in nt or nt in n_after):
                    score = len(set(n_after.split()) & set(nt.split()))
                    if score > highest_score:
                        highest_score = score
                        best_match = orig
            if best_match: found_title = best_match
        if not found_title:
            for nt, orig in norm_titles.items():
                if nt in lnorm:
                    found_title = orig
                    break
        if found_title:
            current = found_title
        elif current:
            sections[current].append(line)
    for k in sections:
        sections[k] = "\n".join(sections[k]).strip()
    return sections

def compare_content(base_lines, comp_lines):
    def tokens_from_lines(lines):
        tokens = []
        for pno, lno, line in lines:
            for m in re.finditer(r'\w+', line, flags=re.UNICODE):
                w = m.group(0)
                tokens.append({'text': w, 'norm': normalize_text(w), 'pno': pno})
        return tokens
    base_tokens, comp_tokens = tokens_from_lines(base_lines), tokens_from_lines(comp_lines)
    common_tokens = set(t['norm'] for t in base_tokens) & set(t['norm'] for t in comp_tokens)
    base_html_parts, comp_html_parts = [], []
    removed_words, added_words = [], []
    for t in base_tokens:
        if t['norm'] in common_tokens: base_html_parts.append(html.escape(t['text']))
        else:
            base_html_parts.append(f"<span style='background-color:#ffcccc;'>{html.escape(t['text'])}</span>")
            removed_words.append((t['text'], t['norm'], t['pno']))
    for t in comp_tokens:
        if t['norm'] in common_tokens: comp_html_parts.append(html.escape(t['text']))
        else:
            comp_html_parts.append(f"<span style='background-color:#ccffcc;'>{html.escape(t['text'])}</span>")
            added_words.append((t['text'], t['norm'], t['pno']))
    return " ".join(base_html_parts), " ".join(comp_html_parts), removed_words, added_words

def build_section_htmls(base_full_text, comp_full_text, base_pages_list, comp_pages_list):
    base_sections, comp_sections = split_full_text_into_sections(base_full_text), split_full_text_into_sections(comp_full_text)
    base_html_full, comp_html_full, aggregate_summary = "", "", []
    for sec in SECTION_TITLES:
        base_text, comp_text = base_sections.get(sec, ""), comp_sections.get(sec, "")
        base_lines = [(1, i, line) for i, line in enumerate(base_text.splitlines()) if line.strip()]
        comp_lines = [(1, i, line) for i, line in enumerate(comp_text.splitlines()) if line.strip()]
        b_html_cmp, c_html_cmp, removed, added = compare_content(base_lines, comp_lines)
        base_html_full += f"<h3>{sec}</h3>{b_html_cmp}<br><hr>"
        comp_html_full += f"<h3>{sec}</h3>{c_html_cmp}<br><hr>"
        base_norm_to_pages = defaultdict(set)
        for line, pno in base_pages_list:
            for m in re.finditer(r'\w+', line): base_norm_to_pages[normalize_text(m.group(0))].add(pno)
        comp_norm_to_pages = defaultdict(set)
        for line, pno in comp_pages_list:
            for m in re.finditer(r'\w+', line): comp_norm_to_pages[normalize_text(m.group(0))].add(pno)
        for _, norm, __ in removed: 
            aggregate_summary.append((sec, norm, "Removido", tuple(sorted(base_norm_to_pages.get(norm, [1])))))
        for _, norm, __ in added: 
            aggregate_summary.append((sec, norm, "Adicionado", tuple(sorted(comp_norm_to_pages.get(norm, [1])))))
    return base_html_full, comp_html_full, aggregate_summary

# =========================
# Aplicativo PyQt
# =========================
class PDFComparerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Comparador de Bulas")
        self.setGeometry(50, 50, 1400, 900)
        self.setStyleSheet("background-color:#f0f6f5; color:#012a36; font-family:'Inter';")
        self.base_full_text, self.comp_full_text = "", ""
        self.base_pages_list, self.comp_pages_list = [], []
        self.sync_scroll = True
        main_layout = QVBoxLayout(self)
        btn_layout = QHBoxLayout()
        self.btn_base = QPushButton("Abrir Bula Base")
        self.btn_base.clicked.connect(self.load_base)
        self.btn_base.setStyleSheet(self.button_style("#007476", "#ffffff"))
        self.btn_comp = QPushButton("Abrir Bula Comparação")
        self.btn_comp.clicked.connect(self.load_comp)
        self.btn_comp.setStyleSheet(self.button_style("#007476", "#ffffff"))
        self.btn_compare = QPushButton("Comparar")
        self.btn_compare.clicked.connect(self.run_comparison)
        self.btn_compare.setStyleSheet(self.button_style("#007476", "#ffffff"))
        self.btn_sync = QPushButton("Desativar Sincronização")
        self.btn_sync.clicked.connect(self.toggle_sync)
        self.btn_sync.setStyleSheet(self.button_style("#007476", "#ffffff"))
        self.btn_help = QPushButton("Ajuda")
        self.btn_help.clicked.connect(self.show_help_dialog)
        self.btn_help.setStyleSheet(self.button_style("#007476", "#ffffff"))
        btn_layout.addWidget(self.btn_base)
        btn_layout.addWidget(self.btn_comp)
        btn_layout.addWidget(self.btn_compare)
        btn_layout.addWidget(self.btn_sync)
        btn_layout.addWidget(self.btn_help)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.separator())
        comp_split = QSplitter(Qt.Orientation.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.label_base_info = QLabel("<b>Bula Base</b><br><i>Nenhum arquivo carregado.</i>")
        self.label_base_info.setStyleSheet("background-color:#e1f0ef; color:#012a36; border-radius:8px; padding:8px; font-size:14px; border: 1px solid #cde5e1;")
        self.label_base_info.setWordWrap(True)
        self.base_area = QTextEdit()
        self.base_area.setReadOnly(True)
        self.base_area.setStyleSheet("background-color:#fef7f7; color:#012a36; border-radius:8px; padding:8px; font-size:14px;")
        self.base_area.verticalScrollBar().valueChanged.connect(self.sync_base_scroll)
        left_layout.addWidget(self.label_base_info)
        left_layout.addWidget(self.base_area)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.label_comp_info = QLabel("<b>Bula para Comparação</b><br><i>Nenhum arquivo carregado.</i>")
        self.label_comp_info.setStyleSheet("background-color:#e1f0ef; color:#012a36; border-radius:8px; padding:8px; font-size:14px; border: 1px solid #cde5e1;")
        self.label_comp_info.setWordWrap(True)
        self.comp_area = QTextEdit()
        self.comp_area.setReadOnly(True)
        self.comp_area.setStyleSheet("background-color:#f7fff0; color:#012a36; border-radius:8px; padding:8px; font-size:14px;")
        self.comp_area.verticalScrollBar().valueChanged.connect(self.sync_comp_scroll)
        right_layout.addWidget(self.label_comp_info)
        right_layout.addWidget(self.comp_area)
        comp_split.addWidget(left_widget)
        comp_split.addWidget(right_widget)
        main_layout.addWidget(comp_split, 8)
        self.summary_area = QTextBrowser()
        self.summary_area.setStyleSheet("background-color:#fff7e6; color:#012a36; border-radius:8px; padding:8px; font-size:14px;")
        main_layout.addWidget(self.summary_area, 2)

    def button_style(self, bg, txt): return f"QPushButton {{ background-color: {bg}; color: {txt}; padding: 6px; border-radius: 6px; font-weight: bold; font-family: 'Inter'; }} QPushButton:hover {{ background-color: #cde5e1; }} QPushButton:pressed {{ background-color: #a3d0ca; }}"
    def separator(self):
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setFrameShadow(QFrame.Shadow.Sunken); return sep

    def load_base(self):
        file, _ = QFileDialog.getOpenFileName(self, "Selecionar Bula Base", "", "Arquivos Suportados (*.pdf *.docx);;Todos os Arquivos (*)")
        if not file: return
        text, pages = read_pdf_full_with_pages(file) if file.lower().endswith(".pdf") else read_docx_full_with_pages(file)
        self.base_full_text = text
        self.base_pages_list = pages
        header_info = extract_header_info(text)
        meta_info = ""
        if file.lower().endswith(".pdf"):
            year, process = extract_pdf_metadata(file)
            meta_info = f"<br><i>Ano/Processo: {year} / {process}</i>"
        self.label_base_info.setText(f"<b>{html.escape(header_info).replace('\n', '<br>')}</b>{meta_info}")

    def load_comp(self):
        file, _ = QFileDialog.getOpenFileName(self, "Selecionar Bula Comparação", "", "Arquivos Suportados (*.pdf *.docx);;Todos os Arquivos (*)")
        if not file: return
        text, pages = read_pdf_full_with_pages(file) if file.lower().endswith(".pdf") else read_docx_full_with_pages(file)
        self.comp_full_text = text
        self.comp_pages_list = pages
        header_info = extract_header_info(text)
        meta_info = ""
        if file.lower().endswith(".pdf"):
            year, process = extract_pdf_metadata(file)
            meta_info = f"<br><i>Ano/Processo: {year} / {process}</i>"
        self.label_comp_info.setText(f"<b>{html.escape(header_info).replace('\n', '<br>')}</b>{meta_info}")

    def show_help_dialog(self):
        help_title = "Ajuda - Comparador de Bulas"
        help_text = """
        <p>Este aplicativo compara duas versões de uma bula de medicamento (PDF ou DOCX) para destacar as diferenças textuais.</p>
        <b>Como usar:</b>
        <ol>
            <li>Clique em "Abrir Bula Base" para carregar o documento original.</li>
            <li>Clique em "Abrir Bula Comparação" para carregar o documento novo ou modificado.</li>
            <li>Clique em "Comparar" para ver as diferenças.</li>
        </ol>
        <b>Significado das Cores:</b>
        <ul>
            <li><b>Texto com fundo <font color='#d9534f'>vermelho</font></b>: Indica palavras que existiam na <b>Bula Base</b> (esquerda) mas foram <u>removidas</u> na bula de comparação.</li>
            <li><b>Texto com fundo <font color='#5cb85c'>verde</font></b>: Indica palavras que foram <u>adicionadas</u> à <b>Bula de Comparação</b> (direita) e não existiam na Bula Base.</li>
        </ul>
        <p>O painel de "Resumo das Alterações" na parte inferior lista todas as palavras modificadas, agrupadas por seção, para uma análise rápida.</p>
        """
        QMessageBox.information(self, help_title, help_text)

    def toggle_sync(self):
        self.sync_scroll = not self.sync_scroll
        self.btn_sync.setText("Desativar Sincronização" if self.sync_scroll else "Ativar Sincronização")

    def sync_base_scroll(self):
        if self.sync_scroll: self.comp_area.verticalScrollBar().setValue(self.base_area.verticalScrollBar().value())
    def sync_comp_scroll(self):
        if self.sync_scroll: self.base_area.verticalScrollBar().setValue(self.comp_area.verticalScrollBar().value())

    def run_comparison(self):
        if not self.base_full_text or not self.comp_full_text:
            QMessageBox.warning(self, "Erro", "Selecione as duas bulas antes de comparar.")
            return
        base_html, comp_html, summary = build_section_htmls(self.base_full_text, self.comp_full_text, self.base_pages_list, self.comp_pages_list)
        self.base_area.setHtml(base_html)
        self.comp_area.setHtml(comp_html)
        self.make_summary_interactive(summary)

    # <<< MÉTODO RESTAURADO E MELHORADO >>>
    def make_summary_interactive(self, summary_data):
        self.summary_area.clear()
        if not summary_data:
            self.summary_area.insertHtml("<i>Nenhuma diferença encontrada.</i>")
            return

        self.summary_area.insertHtml("<h2>Resumo das Alterações</h2><br>")

        grouped = defaultdict(lambda: defaultdict(list))
        # Usa set para remover duplicatas e depois sorted para garantir uma ordem consistente
        unique_summary = sorted(list(set(summary_data)))

        for sec, word, tipo, pages in unique_summary:
            grouped[sec][tipo].append((word, pages))

        for sec in SECTION_TITLES:
            if sec in grouped:
                self.summary_area.insertHtml(f"<h3>{sec}</h3>")
                
                if "Removido" in grouped[sec]:
                    self.summary_area.insertHtml("<b>Removidos:</b><br>")
                    # Ordena as palavras alfabeticamente para uma exibição consistente
                    for word, pages in sorted(grouped[sec]["Removido"]):
                        pages_str = ", ".join(map(str, pages))
                        self.summary_area.insertHtml(
                            f"&nbsp;&nbsp;&nbsp;• <span style='color:red;'>{html.escape(word)}</span> (página(s): {pages_str})<br>"
                        )
                
                if "Adicionado" in grouped[sec]:
                    self.summary_area.insertHtml("<b>Adicionados:</b><br>")
                    # Ordena as palavras alfabeticamente
                    for word, pages in sorted(grouped[sec]["Adicionado"]):
                        pages_str = ", ".join(map(str, pages))
                        self.summary_area.insertHtml(
                            f"&nbsp;&nbsp;&nbsp;• <span style='color:green;'>{html.escape(word)}</span> (página(s): {pages_str})<br>"
                        )
                
                self.summary_area.insertHtml("<br>")


# =========================
# Main
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFComparerApp()
    window.show()
    sys.exit(app.exec())