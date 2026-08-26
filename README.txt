Estrutura sugerida:

fpa_multinacional/
├── app.py
├── dashboard.py
├── analytics.py
├── database.py
├── processing.py
├── data_upload.py
├── presentation.py
├── requirements.txt
├── data/
│   ├── base_dados_ficticia_FX_.csv
│   ├── base_dados_ficticia_Summary.csv
│   └── base_dados_ficticia_Timecards.csv
└── database/
    └── fpa.db

Como usar:
1. Copie os arquivos .py para a raiz do seu projeto.
2. Mantenha suas pastas data/ e database/ existentes.
3. Instale dependências: pip install -r requirements.txt
4. Rode: streamlit run app.py

Novas abas:
- Carregar Dados: CSV/Excel -> validação -> SQLite -> dashboard
- Apresentação: responde às 6 perguntas obrigatórias do case

Observação sobre FX:
A atualização de FX substitui a tabela inteira porque a base original é uma matriz mensal.
Use o arquivo FX completo ao atualizar.
