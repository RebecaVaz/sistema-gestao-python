# Sistema de Gestão Comercial em Python

<p align="center">
  **🇧🇷 Português | 🇺🇸 English**
</p>

---

# 🇧🇷 Português

Sistema desktop desenvolvido em Python com banco de dados relacional SQLite, iniciado como projeto acadêmico no começo da graduação e evoluído até se tornar um sistema completo de gestão comercial.

Projeto desenvolvido com foco em evolução prática em Python, abrangendo desde conceitos iniciais até a construção de uma aplicação completa com interface gráfica, banco de dados e geração de relatórios.
---
📷 Demonstração:

### 📊 Gráficos do Sistema

<video src="SEU_VIDEO_AQUI.mp4" controls width="800"></video>

Os gráficos são atualizados em tempo real com base nas informações registradas nas tabelas do sistema.
Qualquer alteração nos dados impacta automaticamente as visualizações, garantindo consistência e análise dinâmica.

#### 📌 Tipos de análise disponíveis:

* **Gráfico de Barras:**
  Apresenta os produtos cadastrados e a quantidade de pedidos associados, permitindo identificar os itens mais e menos vendidos.

* **Gráfico de Linhas:**
  Exibe a relação entre pagamentos realizados e não realizados ao longo do tempo, possibilitando uma análise de desempenho financeiro mensal.

* **Gráfico de Pizza:**
  Mostra a distribuição dos métodos de pagamento utilizados pelos clientes.

* **Indicadores em Tabela:**
  Exibe a quantidade de pedidos concluídos e cancelados, permitindo uma análise de desistências.

https://github.com/user-attachments/assets/4c30de85-1691-4a08-b181-4e96cbfcc473

https://github.com/user-attachments/assets/d9ffbea6-3d83-4901-b4d1-f7e9e4ee855f

### 📋 Cadastro de Clientes, Pedidos, Pagamentos e Edição de Tabelas

* Em todas as abas de cadastro, é possível utilizar a tecla **Enter** para avançar automaticamente para o próximo campo.

* No cadastro de pedidos, é possível adicionar ou remover produtos por meio dos botões:

  * ✔️ Adicionar produto
  * ❌ Remover produto
    A configuração escolhida é mantida mesmo após fechar o sistema ou desligar o computador.

* Nos campos de data, ao selecionar um dia diferente do atual, após a finalização do cadastro o sistema redefine automaticamente para a data atual.
  O mesmo ocorre com os **ComboBox**, que retornam para a opção padrão.

* No cadastro de pagamentos, basta inserir apenas números que o sistema realiza a formatação automática (ex: valores monetários).
  O mesmo se aplica à edição de datas diretamente nas tabelas.

* Ao editar valores nas tabelas, recomenda-se utilizar a vírgula para evitar erros de interpretação.
  Exemplo: `85,00` em vez de `8500`.

* As barras de pesquisa permitem localizar registros por **nome** e **data**.

* O código de cadastro é único e não pode ser alterado.
  As tabelas exibem dois números:

  * Índice da linha (posição atual)
  * Código de cadastro (identificador único)

  Por isso, nem sempre os valores coincidem.
  Exemplo: um registro pode ter código **3**, mas estar na **linha 1**, caso registros anteriores tenham sido removidos.


https://github.com/user-attachments/assets/847f693d-3ce8-4fb7-8e49-2d3fe5730b1c

https://github.com/user-attachments/assets/789c6c93-cac8-47fc-806b-eccba1a88baa

https://github.com/user-attachments/assets/f40f448c-ed14-407d-989a-2c2d93f12d8f


### 🧾 Geração de Relatórios e Backups 

Ao clicar no botão "Resetar IDs", o sistema permite ao usuário definir como deseja proceder após a geração de relatórios, oferecendo maior controle sobre os dados armazenados.

⚙️ Opções disponíveis:
Gerar o relatório e manter os dados cadastrados
Gerar o relatório e resetar completamente a tabela

💾 Armazenamento dos arquivos:

Backups:
Salvos automaticamente em:

AppData\Local\EmpresaApp\backups\

Relatórios:
Salvos na área de trabalho do usuário:

C:\Users\SEU_USUARIO\Desktop\Relatórios

ou

C:\Users\SEU_USUARIO\OneDrive\Desktop\Relatórios

Essa funcionalidade proporciona mais segurança e flexibilidade na gestão das informações, permitindo ao usuário controlar tanto a geração de relatórios quanto a persistência dos dados.

<img width="1911" height="1040" alt="Captura de tela 2026-04-07 114401" src="https://github.com/user-attachments/assets/756aa26e-0a46-4136-9e47-13b0bc930828" />


<img width="1078" height="297" alt="Captura de tela 2026-04-07 221536" src="https://github.com/user-attachments/assets/1e3d0f2d-7460-4775-b5a1-5c753322d27b" />


<img width="1151" height="488" alt="Captura de tela 2026-04-07 221753" src="https://github.com/user-attachments/assets/a50eaf33-3e51-414f-9ff1-aeb169ee2849" />


https://github.com/user-attachments/assets/2be8e5d0-97a8-48e1-a907-590f56a8bed7


---
## 💼 O que este projeto demonstra

- Desenvolvimento de aplicação completa (interface + lógica + banco de dados)
- Integração com banco de dados relacional (SQLite)
- Criação de interfaces gráficas com PyQt5
- Manipulação e análise de dados com Pandas
- Geração de gráficos e relatórios com Matplotlib
- Implementação de rotinas automatizadas (backup)
- Organização de código seguindo boas práticas

---

## 🎯 Problema Resolvido

Pequenos negócios frequentemente enfrentam dificuldades para organizar clientes, pedidos e informações financeiras básicas de forma eficiente.

Este sistema foi desenvolvido para centralizar essas informações, permitindo:

- Controle de clientes e pedidos
- Visualização clara de dados
- Geração de relatórios e gráficos
- Apoio à tomada de decisão

---

## 🚀 Funcionalidades

- Cadastro de clientes
- Cadastro de pedidos
- Controle de pagamentos
- Tabelas dinâmicas para visualização de dados
- Barra de pesquisa
- Exclusão de registros
- Criação de relatórios
- Geração de 3 tipos de gráficos
- Sistema de backup automático na nuvem

---

## 🛠 Tecnologias Utilizadas

- Python
- SQLite
- PyQt5 (interface gráfica)
- Pandas (manipulação de dados)
- OpenPyXL (geração/exportação de planilhas Excel)
- Matplotlib (geração de gráficos)

---

## 💾 Estrutura do Projeto

O sistema foi estruturado seguindo separação de responsabilidades entre:
- Interface gráfica
- Lógica de negócio
- Banco de dados
- Sistema de backup automático
  
---

## ▶️ Como Executar o Projeto

1. Clone o repositório:
   git clone https://github.com/RebecaVaz/sistema-gestao-python.git

2. Instale as dependências:
   pip install -r requirements.txt

3. Execute o sistema:
   python main.py
   
## 🚀 Diferenciais
- Aplicação completa com interface gráfica funcional
- Integração entre múltiplas tecnologias
- Geração automatizada de relatórios e gráficos
- Estrutura organizada e escalável
- Implementação de backup automático

---

## 📌 Status 

✔ Concluído e funcional
🔄 Em melhorias contínuas

---

## 📌 Projeto

Desenvolvido entre Setembro de 2024 e Fevereiro de 2026, como parte da minha evolução prática em Python.

---

# 🇺🇸 English

# Python-Based Business Management System

A desktop application developed in Python using SQLite as its relational database. Initially created as an academic project at the beginning of my undergraduate studies, it gradually evolved into a fully functional business management system.

The project was developed with a strong emphasis on hands-on Python experience, covering everything from fundamental programming concepts to building a complete application featuring a graphical user interface, database integration, and automated report generation.

---

📷 **Application Showcase**

### 📊 System Analytics and Charts

<video src="SEU_VIDEO_AQUI.mp4" controls width="800"></video>

The charts are updated in real time based on the information recorded in the system's database tables.

Any changes to the underlying data are automatically reflected in the visualizations, ensuring data consistency and enabling dynamic analysis.

#### 📌 Available Analytical Visualizations:

* **Bar Chart:**
  Displays registered products and their associated order quantities, making it possible to identify the best-selling and least-selling items.

* **Line Chart:**
  Illustrates the relationship between completed and outstanding payments over time, enabling monthly financial performance analysis.

* **Pie Chart:**
  Shows the distribution of payment methods used by customers.

* **Tabular Indicators:**
  Displays the number of completed and canceled orders, providing insights into order cancellations and customer drop-offs.

https://github.com/user-attachments/assets/4c30de85-1691-4a08-b181-4e96cbfcc473

https://github.com/user-attachments/assets/d9ffbea6-3d83-4901-b4d1-f7e9e4ee855f

### 📋 Customer, Order, and Payment Registration & Table Editing

* Across all registration tabs, pressing the **Enter** key automatically moves the cursor to the next input field.

* In the order registration section, products can be added or removed using the following buttons:

  * ✔️ Add Product
  * ❌ Remove Product

  The selected configuration is preserved even after closing the application or shutting down the computer.

* In date fields, if a date other than the current date is selected, the system automatically resets it to the current date once the registration process is completed.

  The same behavior applies to **ComboBoxes**, which automatically revert to their default selections.

* In the payment registration section, users only need to enter numeric values, as the system automatically applies the appropriate formatting (e.g., currency values).

  The same functionality applies when editing dates directly within the tables.

* When editing values directly in the tables, using a comma as the decimal separator is recommended to prevent incorrect value interpretation.

  Example: `85,00` instead of `8500`.

* Search bars allow users to locate records by **name** and **date**.

* Each registration code is unique and cannot be modified.

  The tables display two separate numerical references:

  * Row index (current position in the table)
  * Registration code (unique record identifier)

  Therefore, these values do not necessarily match.

  Example: a record may have registration code **3** while appearing in **row 1**, if previous records have been deleted.

https://github.com/user-attachments/assets/847f693d-3ce8-4fb7-8e49-2d3fe5730b1c

https://github.com/user-attachments/assets/789c6c93-cac8-47fc-806b-eccba1a88baa

https://github.com/user-attachments/assets/f40f448c-ed14-407d-989a-2c2d93f12d8f

### 🧾 Report Generation and Backups

When clicking the **"Reset IDs"** button, the system allows users to choose how they want to proceed after generating reports, providing greater control over stored data.

⚙️ **Available Options:**

- Generate the report while retaining all registered data.
- Generate the report and completely reset the table.

💾 **File Storage Locations:**

**Backups:**

Automatically saved to:

`AppData\Local\EmpresaApp\backups\`

**Reports:**

Saved to the user's desktop:

`C:\Users\YOUR_USERNAME\Desktop\Reports`

or

`C:\Users\YOUR_USERNAME\OneDrive\Desktop\Reports`

This functionality provides greater security and flexibility in information management, allowing users to control both report generation and data retention.

<img width="1911" height="1040" alt="Screenshot 2026-04-07 114401" src="https://github.com/user-attachments/assets/756aa26e-0a46-4136-9e47-13b0bc930828" />

<img width="1078" height="297" alt="Screenshot 2026-04-07 221536" src="https://github.com/user-attachments/assets/1e3d0f2d-7460-4775-b5a1-5c753322d27b" />

<img width="1151" height="488" alt="Screenshot 2026-04-07 221753" src="https://github.com/user-attachments/assets/a50eaf33-3e51-414f-9ff1-aeb169ee2849" />

https://github.com/user-attachments/assets/2be8e5d0-97a8-48e1-a907-590f56a8bed7

---

## 💼 What This Project Demonstrates

- End-to-end application development (user interface, business logic, and database integration).
- Relational database integration using SQLite.
- Graphical user interface development with PyQt5.
- Data manipulation and analysis using Pandas.
- Data visualization and report generation with Matplotlib.
- Implementation of automated processes, including database backups.
- Code organization and maintainability following software development best practices.

---

## 🎯 Problem Addressed

Small businesses often face challenges in efficiently organizing customer records, orders, and basic financial information.

This system was developed to centralize these operations, providing:

- Customer and order management.
- Clear and accessible data visualization.
- Automated report and chart generation.
- Support for informed business decision-making.

---

## 🚀 Features

- Customer registration and management.
- Order registration and management.
- Payment tracking and management.
- Dynamic tables for data visualization.
- Search functionality.
- Record deletion.
- Automated report generation.
- Three types of data visualizations.
- Automated cloud backup system.

---

## 🛠 Technologies Used

- **Python** — Core programming language.
- **SQLite** — Relational database management.
- **PyQt5** — Graphical user interface development.
- **Pandas** — Data manipulation and analysis.
- **OpenPyXL** — Excel spreadsheet generation and export.
- **Matplotlib** — Data visualization and chart generation.

---

## 💾 Project Architecture

The application was structured around a separation of responsibilities, encompassing:

- Graphical user interface.
- Business logic.
- Database management.
- Automated backup system.

---

## ▶️ How to Run the Project

1. Clone the repository:

   ```bash
   git clone https://github.com/RebecaVaz/sistema-gestao-python.git
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   python main.py
   ```

## 🚀 Key Highlights

- Fully functional desktop application with a graphical user interface.
- Integration of multiple technologies.
- Automated report and chart generation.
- Well-structured and scalable architecture.
- Automated backup implementation.

---

## 📌 Status

✔ Completed and functional.

🔄 Continuously evolving through ongoing improvements.

---

## 📌 Project

Developed between September 2024 and February 2026 as part of my hands-on learning journey and practical development experience with Python.
