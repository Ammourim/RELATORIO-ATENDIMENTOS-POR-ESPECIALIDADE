# Relatório Automatizado de Classificação de Risco Hospitalar

## Visão Geral do Projeto

Este projeto apresenta um software desenvolvido em **Python** com interface gráfica (**Tkinter**) para automatizar a geração de relatórios de classificação de risco de pacientes por especialidade. A iniciativa surgiu da necessidade de otimizar um processo manual existente em uma unidade hospitalar, que era suscetível a inconsistências e demandava tempo significativo da equipe de enfermagem e TI.

O principal desafio técnico superado foi a extração e o processamento de dados relevantes que estavam armazenados de forma não estruturada dentro de uma única coluna de texto (`RCL_TXT`) em um banco de dados **MaxDB**.

## Problema Resolvido

Anteriormente, a geração de relatórios de atendimentos por especialidade e classificação de risco era realizada manualmente, com anotações em papel. Isso resultava em:

* Alta inconsistência e imprecisão dos dados.

* Demora na obtenção de informações para análise gerencial.

* Sobrecarga de trabalho para a equipe.

## Solução Implementada

O software desenvolvido oferece:

* **Extração Automatizada:** Conecta-se diretamente ao banco de dados MaxDB para extrair a coluna `RCL_TXT` e a data/hora do registro.

* **Processamento Inteligente de Dados:** Utiliza **expressões regulares (RegEx)** para parsear e estruturar as informações de classificação de risco e especialidade contidas na string `RCL_TXT`.

* **Interface Gráfica Intuitiva (GUI):** Desenvolvida com **Tkinter**, permite que o usuário selecione um período de data/hora e filtre por usuários específicos, facilitando a geração de relatórios sob demanda.

* **Geração de Relatórios Detalhados:** Apresenta um resumo claro dos atendimentos por especialidade e suas respectivas classificações (Verde, Amarelo, Vermelho, Azul, Outras).

## Tecnologias Utilizadas

* **Python:** Linguagem de programação principal.

* **Tkinter:** Para a construção da interface gráfica do usuário (GUI).

* **pyodbc:** Biblioteca para conexão com o banco de dados MaxDB.

* **re (Regex):** Para o processamento e extração de padrões de texto da coluna `RCL_TXT`.

* **datetime:** Para manipulação de datas e horários.

* **os, sys, threading, queue:** Para funcionalidades do sistema, multithreading e comunicação entre threads.

* **python-dotenv:** Para gerenciamento seguro de variáveis de ambiente (credenciais do banco de dados).

* **Git:** Para controle de versão do código.

## Como Executar o Projeto

1. **Pré-requisitos:**

   * Python 3.x instalado.

   * Driver ODBC para MaxDB configurado no seu sistema.

   * Bibliotecas Python: `pip install pyodbc python-dotenv`

2. **Configuração do Banco de Dados:**

   * Crie um arquivo na raiz do projeto chamado `.env`.

   * Adicione as seguintes variáveis de ambiente, substituindo pelos seus dados reais:

     ```
     DB_DRIVER=
     DB_SERVER=
     DB_PORT=
     DB_DATABASE=
     DB_UID=
     DB_PWD=
     RCL_COD_FILTER=
     ```


3. **Execução:**

   * Navegue até o diretório do projeto no terminal.

   * Execute o script principal: `python gui_relat_class.py`

   * **Alternativa (Executável):** Se você gerou o executável com PyInstaller (na pasta `dist`), você pode executar o programa diretamente clicando duas vezes no arquivo `.exe` (no Windows) ou equivalente no seu sistema operacional, sem a necessidade de usar o terminal. Certifique-se de que o arquivo `.env` esteja na mesma pasta do executável.

## Contribuições

Sinta-se à vontade para explorar o código, sugerir melhorias ou relatar problemas.

## Autor

**Alan Amorim Porto**


