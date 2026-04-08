# Sistema de Gestão Comercial em Python

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

O sistema permite ao usuário definir como deseja proceder após a geração de relatórios, oferecendo maior controle sobre os dados armazenados.

⚙️ Opções disponíveis:
* Gerar o relatório e manter os dados cadastrados
* Gerar o relatório e resetar completamente a tabela

💾 Armazenamento dos arquivos:
- Backups:
Salvos automaticamente em:
AppData\Local\EmpresaApp\backups\
- Relatórios:
Salvos na área de trabalho do usuário:
C:\Users\SEU_USUARIO\Desktop\Relatórios
ou
C:\Users\SEU_USUARIO\OneDrive\Desktop\Relatórios

Essa funcionalidade proporciona mais segurança e flexibilidade na gestão das informações, permitindo ao usuário controlar tanto a geração de relatórios quanto a persistência dos dados.

<img width="1911" height="1040" alt="Captura de tela 2026-04-07 114401" src="https://github.com/user-attachments/assets/756aa26e-0a46-4136-9e47-13b0bc930828" />


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

## 📌 Status do Projeto

✔ Concluído e funcional
🔄 Em melhorias contínuas

---

## 👩‍💻 Autora

Rebeca Vaz  
Projeto desenvolvido entre Setembro de 2024 e Fevereiro de 2026, como parte da minha evolução prática em Python.

---

📄 Licença

Este projeto está sob a licença MIT.
