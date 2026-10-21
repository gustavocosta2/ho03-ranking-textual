#!/usr/bin/env python3
"""
Script de indexação do CORD-19 Round 1 no ElasticSearch utilizando o modelo BM-25.
Compatível tanto com Elasticsearch local (Docker) quanto com Elastic Cloud.
"""

import os
import sys
import json
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Diretórios
PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_DADOS = PASTA_PROJETO / "data" / "round1"
PASTA_COLECAO = PASTA_DADOS / "2020-04-10"

NOME_INDICE = "cord19-bm25"


def obter_cliente_elasticsearch():
    """Conecta ao ElasticSearch via variáveis de ambiente ou localhost padrão."""
    es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
    es_api_key = os.environ.get("ELASTICSEARCH_API_KEY", None)
    es_user = os.environ.get("ELASTICSEARCH_USER", "elastic")
    es_pass = os.environ.get("ELASTICSEARCH_PASSWORD", None)

    if es_api_key:
        es = Elasticsearch(es_url, api_key=es_api_key, request_timeout=60)
    elif es_pass:
        es = Elasticsearch(es_url, basic_auth=(es_user, es_pass), request_timeout=60)
    else:
        es = Elasticsearch(es_url, request_timeout=60)

    if not es.ping():
        raise ConnectionError(f"Não foi possível conectar ao ElasticSearch em {es_url}")

    print(f"✓ Conectado com sucesso ao ElasticSearch: {es_url}")
    return es


def criar_indice(es: Elasticsearch):
    """Cria o índice no ElasticSearch com BM-25 explícito (k1=1.5, b=0.75)."""
    if es.indices.exists(index=NOME_INDICE):
        print(f"Índice '{NOME_INDICE}' já existe. Excluindo para reindexação limpa...")
        es.indices.delete(index=NOME_INDICE)

    config_indice = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "similarity": {
                "bm25_custom": {
                    "type": "BM25",
                    "k1": 1.5,
                    "b": 0.75
                }
            }
        },
        "mappings": {
            "properties": {
                "id_documento": {"type": "keyword"},
                "titulo": {
                    "type": "text",
                    "similarity": "bm25_custom",
                    "analyzer": "english"
                },
                "resumo": {
                    "type": "text",
                    "similarity": "bm25_custom",
                    "analyzer": "english"
                },
                "texto_completo": {
                    "type": "text",
                    "similarity": "bm25_custom",
                    "analyzer": "english"
                }
            }
        }
    }

    es.indices.create(index=NOME_INDICE, body=config_indice)
    print(f"✓ Índice '{NOME_INDICE}' criado com BM-25 (k1=1.5, b=0.75)!")


def carregar_documentos():
    """Lê o metadata.csv consolidado por cord_uid."""
    print("Carregando metadados dos artigos...")
    metadados = pd.read_csv(
        PASTA_COLECAO / "metadata.csv",
        usecols=["cord_uid", "title", "abstract"],
        dtype=str,
        keep_default_na=False
    ).rename(columns={"cord_uid": "id_documento", "title": "titulo", "abstract": "resumo"})

    # Agrupa duplicatas pelo primeiro preenchido
    documentos = metadados.groupby("id_documento", sort=False, as_index=False).agg({
        "titulo": lambda vals: next((v.strip() for v in vals if v.strip()), ""),
        "resumo": lambda vals: next((v.strip() for v in vals if v.strip()), "")
    })

    print(f"✓ Total de documentos únicos prontos para indexação: {len(documentos):,}")
    return documentos


def gerar_acoes_bulk(documentos: pd.DataFrame):
    """Gera ações de indexação em streaming para a API bulk."""
    for row in documentos.itertuples(index=False):
        doc_id = row.id_documento
        titulo = row.titulo or ""
        resumo = row.resumo or ""
        texto_completo = f"{titulo} {resumo}".strip()

        yield {
            "_index": NOME_INDICE,
            "_id": doc_id,
            "_source": {
                "id_documento": doc_id,
                "titulo": titulo,
                "resumo": resumo,
                "texto_completo": texto_completo
            }
        }


from elasticsearch.helpers import streaming_bulk

def indexar():
    es = obter_cliente_elasticsearch()
    criar_indice(es)
    documentos = carregar_documentos()

    print("Iniciando indexação em lote no ElasticSearch...")
    sucessos, falhas = 0, 0

    for ok, info in tqdm(streaming_bulk(es, gerar_acoes_bulk(documentos), chunk_size=1000, raise_on_error=False),
                         total=len(documentos), desc="Indexando no ElasticSearch"):
        if ok:
            sucessos += 1
        else:
            falhas += 1

    # Atualiza o índice para disponibilizar as buscas imediatamente
    es.indices.refresh(index=NOME_INDICE)
    contagem = es.count(index=NOME_INDICE)["count"]
    print(f"\n✓ Indexação finalizada com sucesso!")
    print(f"Total indexado no ElasticSearch: {contagem:,} artigos.")


if __name__ == "__main__":
    indexar()
