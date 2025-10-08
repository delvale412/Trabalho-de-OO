# Anvisa Insight - Aplicativo Desktop

## Descrição do Projeto
O **Anvisa Insight** é um aplicativo desktop desenvolvido para gerar **resumos automáticos de documentos técnicos ou regulatórios**.  
Ele permite ao usuário selecionar um arquivo (.txt, .docx, .pdf), definir o nível de detalhe e gerar um resumo consolidado usando o modelo **LLaMA3** via Ollama.

O sistema foi desenvolvido em **Python**, utilizando **PyQt6** para a interface e bibliotecas como **PyMuPDF** e **python-docx** para manipulação de documentos.

---

## 1️⃣ Casos de Uso

| Elemento | Descrição |
|----------|-----------|
| **Nome do caso de uso** | Gerar resumo de documento |
| **Escopo** | Aplicativo Desktop Anvisa Insight |
| **Nível** | Objetivo do Usuário |
| **Ator principal** | Usuário do sistema |
| **Atores coadjuvantes** | Sistema Operacional, Modelo LLaMA3 via Ollama, Biblioteca PyMuPDF, Biblioteca python-docx |
| **Interessados** | Usuários que precisam de resumos técnicos rápidos e organizados de documentos |
| **Pré-condições** | O aplicativo deve estar instalado e o modelo LLaMA3 disponível no Ollama; deve existir um arquivo compatível |
| **Garantia de sucesso** | Resumo exibido, copiado ou salvo com sucesso |
| **Cenário de sucesso (good flow)** | 1. Usuário abre o aplicativo.<br>2. Seleciona o arquivo (.txt, .docx, .pdf).<br>3. Define o nível de detalhe.<br>4. Clica em 'Gerar Resumo'.<br>5. O sistema processa o texto, gera resumos parciais e o resumo final consolidado.<br>6. Exibe o resultado e oferece opções de copiar ou salvar. |
| **Cenários alternativos (bad flow)** | 1. Arquivo incompatível ou corrompido → mensagem de erro.<br>2. Erro de subprocesso → exibe erro retornado pelo modelo.<br>3. Nenhum arquivo selecionado → alerta ao usuário. |
| **Requisitos especiais (não funcionais)** | 1. Execução offline via Ollama.<br>2. Interface PyQt6 intuitiva e responsiva.<br>3. Suporte a arquivos PDF, DOCX e TXT. |
| **Lista de variantes tecnológicas e de dados** | Entrada: .txt, .docx, .pdf <br>Saída: texto, clipboard, arquivo salvo <br>Interface: PyQt6 (QPushButton, QLabel, QTextEdit, QFileDialog) |
| **Comentários diversos** | O sistema faz chunking de 500 linhas para garantir processamento estável e usa subprocessos para modularidade. |

---

## 2️⃣ Diagrama de Classes (UML)

```plantuml
@startuml
class DocumentProcessor {
  +load_document(file_path)
  +split_text(text)
  +summarize_chunk(chunk, level)
  +summarize_final(list_of_summaries)
}

class GUIApp {
  +open_file_dialog()
  +display_summary(summary)
  +copy_to_clipboard()
  +save_summary(file_path)
}

class ModelLLaMA3 {
  +process_text(text_chunk, level)
}

DocumentProcessor --> ModelLLaMA3
GUIApp --> DocumentProcessor
@enduml

