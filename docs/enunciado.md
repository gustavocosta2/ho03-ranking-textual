# **HO03: Ranking Textual**

Esta é a tarefa HO03: Ranking Textual, uma atividade prática que estimula o aluno a desenvolver habilidades de programação em linguagem Python para processamento textual.

***

## **Problema**

Comparar 2 funções de ranking (Vetorial e BM-25) para a tarefa **TREC COVID**

- Coleção: Utilizar a coleção (somente round 1) TREC-COVID disponível em: `https://github.com/allenai/cord19`

- Consultas: disponíveis em `https://ir-datasets.com/beir.html#beir/trec-covid` (somente round 1)

- Julgamentos de Relevância: disponíveis em `https://ir-datasets.com/beir.html#beir/trec-covid` (somente round 1)

- Implementação: é possível utilizar qualquer mecanismo de indexação (como ElasticSearch) para indexar a coleção e processar as consultas.

- Métricas: Computar MAP e nDCG geral (no ranking todo) e nos pontos @1, @3, @5 e @10.

Apresentar um relatório com o que e como foi feito e uma tabela comparativa das 2 funções usando cada uma das métricas. Apresentar uma conclusão.

***

## **Produto**

Deverá ser entregue um notebook Python com o código de implementação, outputs e explicações em texto dos resultados, etc.