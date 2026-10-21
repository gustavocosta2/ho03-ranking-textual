import os
import time
from pathlib import Path
import streamlit as st
from elasticsearch import Elasticsearch

# Configuração da Página
st.set_page_config(
    page_title="COVID-19 Search Engine | BM-25 & ElasticSearch",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada para visual profissional
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .result-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }
    .result-card:hover {
        border-color: #3B82F6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .badge-rank {
        background-color: #2563EB;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .badge-score {
        background-color: #10B981;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .badge-id {
        background-color: #6B7280;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

NOME_INDICE = "cord19-bm25"

# Conexão com o ElasticSearch com Cache do Streamlit
@st.cache_resource
def conectar_elasticsearch():
    # Permite ler tanto de st.secrets (Streamlit Cloud) quanto de os.environ
    es_url = "http://localhost:9200"
    es_api_key = None
    es_user = "elastic"
    es_pass = None

    try:
        if "ELASTICSEARCH_URL" in st.secrets:
            es_url = st.secrets["ELASTICSEARCH_URL"]
            es_api_key = st.secrets.get("ELASTICSEARCH_API_KEY", None)
            es_user = st.secrets.get("ELASTICSEARCH_USER", "elastic")
            es_pass = st.secrets.get("ELASTICSEARCH_PASSWORD", None)
    except Exception:
        pass

    es_url = os.environ.get("ELASTICSEARCH_URL", es_url)
    es_api_key = os.environ.get("ELASTICSEARCH_API_KEY", es_api_key)
    es_user = os.environ.get("ELASTICSEARCH_USER", es_user)
    es_pass = os.environ.get("ELASTICSEARCH_PASSWORD", es_pass)

    try:
        if es_api_key:
            es = Elasticsearch(es_url, api_key=es_api_key, request_timeout=30)
        elif es_pass:
            es = Elasticsearch(es_url, basic_auth=(es_user, es_pass), request_timeout=30)
        else:
            es = Elasticsearch(es_url, request_timeout=30)
        if es.ping():
            return es, None
        return None, "Não foi possível conectar ao ElasticSearch no endereço configurado."
    except Exception as e:
        return None, str(e)


# Consultas padrão do TREC-COVID Round 1 para conveniência
CONSULTAS_TREC = [
    "--- Digitar consulta livre ---",
    "coronavirus origin",
    "coronavirus response to weather changes",
    "coronavirus immunity",
    "how do people die from the coronavirus",
    "animal models of COVID-19",
    "coronavirus remdesivir",
    "coronavirus treatment with chloroquine",
    "coronavirus social distancing impact",
    "incubation period of coronavirus",
    "symptoms of COVID-19",
    "coronavirus mutations and variants",
    "coronavirus spike protein vaccine targets",
    "asymptomatic transmission of COVID-19",
    "coronavirus mask efficacy"
]


def executar_busca_bm25(es, termo_busca, top_k=10):
    """Executa a consulta BM-25 no ElasticSearch sobre os campos de título e resumo."""
    corpo_consulta = {
        "size": top_k,
        "query": {
            "multi_match": {
                "query": termo_busca,
                "fields": ["titulo^3", "resumo^1", "texto_completo"],
                "type": "best_fields"
            }
        },
        "highlight": {
            "fields": {
                "titulo": {},
                "resumo": {"number_of_fragments": 2, "fragment_size": 250}
            }
        }
    }

    inicio = time.time()
    resposta = es.search(index=NOME_INDICE, body=corpo_consulta)
    latencia_ms = (time.time() - inicio) * 1000

    total_hits = resposta["hits"]["total"]["value"]
    documentos_retornados = []

    for hit in resposta["hits"]["hits"]:
        fonte = hit["_source"]
        score = hit["_score"]
        destaques = hit.get("highlight", {})

        titulo = destaques.get("titulo", [fonte.get("titulo", "(Sem título)")])[0]
        resumo = destaques.get("resumo", [fonte.get("resumo", "(Sem resumo disponível)")])[0]

        documentos_retornados.append({
            "id": hit["_id"],
            "score": score,
            "titulo": titulo,
            "resumo": resumo,
            "resumo_original": fonte.get("resumo", "")
        })

    return documentos_retornados, total_hits, latencia_ms


def main():
    # Cabeçalho
    st.markdown('<div class="main-title">🔬 Motor de Busca COVID-19</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Recuperação de Informação sobre <b>51.045 artigos científicos</b> do CORD-19 utilizando <b>ElasticSearch & BM-25</b>.<br>'
        'Desenvolvido por <b>Gustavo Costa</b> | PUC Minas — Processamento de Linguagem Natural (HO03)</div>',
        unsafe_allow_html=True
    )

    # Conexão com o banco
    es, erro = conectar_elasticsearch()

    # Barra Lateral
    with st.sidebar:
        st.header("⚙️ Configurações da Busca")

        if es:
            try:
                total_docs = es.count(index=NOME_INDICE)["count"]
                st.success(f"🟢 **ElasticSearch Conectado**\n\n📄 **{total_docs:,}** artigos indexados.")
            except Exception:
                st.warning("Índice 'cord19-bm25' ainda não indexado.")
        else:
            st.error(f"🔴 **Erro de Conexão com ElasticSearch:**\n{erro}")

        st.markdown("---")
        st.subheader("Sugestões (TREC-COVID)")
        consulta_selecionada = st.selectbox(
            "Selecione uma consulta oficial para testar:",
            CONSULTAS_TREC
        )

        top_k = st.slider("Resultados por página (Top K):", min_value=5, max_value=50, value=10, step=5)

        st.markdown("---")
        with st.expander("ℹ️ Sobre o Modelo BM-25"):
            st.markdown("""
            - **Motor:** ElasticSearch 8 (Lucene).
            - **Similaridade:** BM-25 ($k_1 = 1.5, b = 0.75$).
            - **Coleção:** CORD-19 Round 1 (10/04/2020).
            - **Campos buscados:** Título (peso 3x), Resumo (peso 1x) e Texto Completo.
            """)

    # Campo de Busca Principal
    termo_inicial = "" if consulta_selecionada == CONSULTAS_TREC[0] else consulta_selecionada

    col_busca, col_botao = st.columns([5, 1])
    with col_busca:
        termo_busca = st.text_input(
            "Digite sua pesquisa ou pergunta médica:",
            value=termo_inicial,
            placeholder="Ex: coronavirus remdesivir, origin of COVID-19, chloroquine efficacy...",
            label_visibility="collapsed"
        )
    with col_botao:
        botao_buscar = st.button("🔍 Pesquisar", use_container_width=True, type="primary")

    # Execução da Busca
    if (botao_buscar or termo_busca) and es:
        if not termo_busca.strip():
            st.warning("Por favor, digite uma consulta para pesquisar.")
            return

        with st.spinner("Executando busca probabilística BM-25 no ElasticSearch..."):
            try:
                resultados, total_hits, latencia = executar_busca_bm25(es, termo_busca, top_k=top_k)

                st.markdown(f"**{total_hits:,}** artigos encontrados em **{latencia:.1f} ms** (exibindo os {len(resultados)} mais relevantes):")

                if not resultados:
                    st.info("Nenhum artigo encontrado com esses termos. Tente palavras mais gerais.")
                    return

                # Renderização dos Cards de Artigos
                for idx, art in enumerate(resultados, start=1):
                    with st.container():
                        st.markdown(f"""
                        <div class="result-card">
                            <div style="display: flex; gap: 8px; margin-bottom: 8px; align-items: center;">
                                <span class="badge-rank">{idx}º Lugar</span>
                                <span class="badge-score">Score BM25: {art['score']:.4f}</span>
                                <span class="badge-id">ID: {art['id']}</span>
                            </div>
                            <h3 style="margin-top: 0; color: #0F172A; font-size: 1.15rem;">{art['titulo']}</h3>
                            <p style="color: #334155; font-size: 0.95rem; line-height: 1.5;">{art['resumo']}</p>
                        </div>
                        """, unsafe_allow_html=True)

            except Exception as ex:
                st.error(f"Erro ao executar busca: {str(ex)}")


if __name__ == "__main__":
    main()
