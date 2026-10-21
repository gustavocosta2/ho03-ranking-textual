# HO03 — Ranking Textual

Comparação entre modelo vetorial e BM25 no TREC-COVID, somente round 1.
O [enunciado original](docs/enunciado.md) foi preservado.
A carga, a inspeção e o pré-processamento textual inicial estão implementados.

## Estrutura

- `notebooks/ho03_ranking_textual.ipynb`: todo o código da atividade, incluindo a carga dos dados.
- `data/round1/2020-04-10/`: metadados e todos os JSONs de artigos do round 1.
- `data/round1/topics-rnd1.xml` e `qrels-rnd1.txt`: consultas e julgamentos.
- `data/round1/sources.json`: URLs originais e checksums registrados na obtenção.
- `data/round1/inventory.json`: inventário da coleção mantida.

## Executar

Selecione o kernel da `.venv` e execute as células do notebook na ordem.
As dependências estão em `requirements.txt`.

Os imports ficam no início. A carga é dividida em subseções Markdown, com
variáveis e funções em português e comentários sobre as decisões de leitura.
As tabelas resultantes são `documentos`, `consultas` e `julgamentos`.
A função `ler_artigo(caminho_json)` lê um artigo integralmente sob demanda.
Todos os dados são locais; não há dependência de scripts externos.

## Dados mantidos

Aproximadamente **7,14 GB** de dados: 51.078 registros, 30 consultas,
8.691 julgamentos e 59.311 JSONs (40.144 PDF e 19.167 PMC).
Todos os JSONs foram lidos e vinculados aos metadados; 38.882 registros possuem
texto completo disponível. Registros sem texto completo, IDs repetidos e
julgamentos sem documento correspondente foram preservados.

Arquivos compactados, marcadores de extração, embeddings pré-calculados,
mapeamento MAG e caches antigos foram removidos. Nenhum JSON de artigo foi
removido. O notebook não baixa os arquivos novamente.

## Fontes

- [CORD-19](https://github.com/allenai/cord19): pacote completo de 10/04/2020,
  identificado como round 1 na tabela de versões do repositório.
- [NIST, seção Round 1 Data](https://ir.nist.gov/covidSubmit/data.html):
  consultas e julgamentos originais do round 1.

O link do enunciado para BEIR descreve a versão completa. Os arquivos específicos
do round 1 foram obtidos na página dos organizadores, sem usar ir_datasets.

O pré-processamento inicial está documentado no notebook. Ranking, métricas e conclusão ficam para as próximas etapas do estudo.
