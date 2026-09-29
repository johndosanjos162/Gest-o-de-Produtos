import streamlit as st
import pandas as pd

# Configuração da página e tema
st.set_page_config(layout="wide", page_title="Gestão de Estoque Elegante")

st.markdown("""
<style>
    /* Estilização Geral */
    .main {
        background-color: #f5f7fb;
        padding: 20px;
    }
    
    /* Cabeçalho */
    .title-text {
        color: #1f2937;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 20px;
        text-align: center;
    }

    /* Cards e Expanders */
    .stExpander {
        border: 1px solid #e0e4e8;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        background-color: #ffffff;
        margin-bottom: 15px;
    }

    /* Botões */
    .stButton>button {
        background-color: #4f46e5;
        color: white;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        padding: 10px 20px;
        transition: background-color 0.2s;
    }
    .stButton>button:hover {
        background-color: #4338ca;
    }

    /* Tabelas */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="title-text">📦 Sistema de Gestão de Comércio</p>', unsafe_allow_html=True)

if 'estoque' not in st.session_state:
    st.session_state.estoque = pd.DataFrame(
        columns=['Produto', 'Categoria', 'Quantidade', 'Limite Mínimo', 'Valor Unitário']
    )

with st.expander("➕ Adicionar Novo Produto"):
    with st.form("form_produto"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Produto")
            categoria = st.selectbox(
                "Categoria",
                ["Grãos", "Massas", "Óleos e Condimentos", "Bebidas", "Outros"]
            )
            preco = st.number_input("Valor Unitário (R$)", min_value=0.0, step=0.01)
        with col2:
            qtd = st.number_input("Quantidade Inicial", min_value=0, step=1)
            limite = st.number_input("Limite Mínimo de Alerta", min_value=0, step=1)
        
        btn_adicionar = st.form_submit_button("Cadastrar Produto")
        if btn_adicionar and nome:
            novo_item = pd.DataFrame({
                'Produto': [nome],
                'Categoria': [categoria],
                'Quantidade': [qtd],
                'Limite Mínimo': [limite],
                'Valor Unitário': [preco]
            })
            st.session_state.estoque = pd.concat([st.session_state.estoque, novo_item], ignore_index=True)
            st.success("Produto cadastrado com sucesso!")
            st.rerun()

with st.expander("🔄 Atualizar Estoque e Preço"):
    if not st.session_state.estoque.empty:
        produtos_disponiveis = st.session_state.estoque['Produto'].tolist()
        produto_selecionado = st.selectbox("Selecione o produto para atualizar:", produtos_disponiveis, key="select_update")
        
        indice_atual = st.session_state.estoque[st.session_state.estoque['Produto'] == produto_selecionado].index[0]
        quantidade_atual = st.session_state.estoque.at[indice_atual, 'Quantidade']
        preco_atual = st.session_state.estoque.at[indice_atual, 'Valor Unitário']
        
        nova_quantidade = st.number_input("Nova Quantidade em Estoque", value=int(quantidade_atual), min_value=0, step=1)
        novo_preco = st.number_input("Novo Valor Unitário (R$)", value=float(preco_atual), min_value=0.0, step=0.01)
        
        if st.button("Atualizar Dados"):
            st.session_state.estoque.at[indice_atual, 'Quantidade'] = nova_quantidade
            st.session_state.estoque.at[indice_atual, 'Valor Unitário'] = novo_preco
            st.success("Dados atualizados com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum produto cadastrado para atualizar.")

with st.expander("🗑️ Remover Produto"):
    if not st.session_state.estoque.empty:
        produtos_disponiveis_remover = st.session_state.estoque['Produto'].tolist()
        produto_remover = st.selectbox("Selecione o produto para remover:", produtos_disponiveis_remover, key="select_remove")
        if st.button("Excluir Produto"):
            st.session_state.estoque = st.session_state.estoque[st.session_state.estoque['Produto'] != produto_remover]
            st.success(f"Produto '{produto_remover}' removido com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum produto cadastrado para remover.")

dados = st.session_state.estoque.copy()
if not dados.empty:
    dados['Valor Total'] = dados['Quantidade'] * dados['Valor Unitário']
    
    aba_geral, aba_categorias = st.tabs(["Visão Geral", "Por Categoria"])
    with aba_geral:
        alertas = dados[dados['Quantidade'] <= dados['Limite Mínimo']]
        if not alertas.empty:
            st.warning("⚠️ Alerta: Produtos abaixo ou no limite mínimo!")
            st.dataframe(alertas[['Produto', 'Quantidade', 'Limite Mínimo']], hide_index=True)
            
        st.subheader("📊 Estoque Atual")
        st.dataframe(
            dados.style.format(
                subset=['Valor Unitário', 'Valor Total'],
                formatter="R$ {:.2f}"
            ),
            hide_index=True,
            use_container_width=True
        )
        
        total_estoque = dados['Valor Total'].sum()
        total_itens = dados['Quantidade'].sum()
        
        m1, m2 = st.columns(2)
        m1.metric("Valor Total em Estoque", f"R$ {total_estoque:.2f}")
        m2.metric("Quantidade Total de Itens", total_itens)
        
    with aba_categorias:
        categoria_selecionada = st.selectbox("Selecione a Categoria", dados['Categoria'].unique())
        dados_filtrados = dados[dados['Categoria'] == categoria_selecionada]
        
        st.subheader(f"🏷️ Produtos - {categoria_selecionada}")
        st.dataframe(
            dados_filtrados.style.format(
                subset=['Valor Unitário', 'Valor Total'],
                formatter="R$ {:.2f}"
            ),
            hide_index=True,
            use_container_width=True
        )
else:
    st.info("Nenhum produto cadastrado no sistema.")
