import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página e tema
st.set_page_config(layout="wide", page_title="Sistema ERP Integrado")

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
    .stExpander, .stTabs {
        border: 1px solid #e0e4e8;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        background-color: #ffffff;
        margin-bottom: 15px;
        padding: 10px;
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

st.markdown('<p class="title-text">🏢 Sistema ERP Integrado</p>', unsafe_allow_html=True)

# Inicialização do Session State
if 'estoque' not in st.session_state:
    st.session_state.estoque = pd.DataFrame(
        columns=['Produto', 'Categoria', 'Quantidade', 'Limite Mínimo', 'Valor Unitário']
    )
if 'vendas' not in st.session_state:
    st.session_state.vendas = pd.DataFrame(
        columns=['Data', 'Produto', 'Quantidade', 'Valor Total']
    )
if 'financeiro' not in st.session_state:
    st.session_state.financeiro = pd.DataFrame(
        columns=['Data', 'Descrição', 'Tipo', 'Valor']
    )
if 'fornecedores' not in st.session_state:
    st.session_state.fornecedores = pd.DataFrame(
        columns=['Nome', 'Contato', 'Categoria de Produto']
    )

tab_estoque, tab_vendas, tab_financeiro, tab_fornecedores = st.tabs(["Estoque", "Vendas", "Financeiro", "Fornecedores"])

with tab_estoque:
    st.subheader("📦 Gestão de Estoque")
    with st.expander("Adicionar Novo Produto"):
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

    with st.expander("Atualizar Estoque e Preço"):
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

    with st.expander("Remover Produto"):
        if not st.session_state.estoque.empty:
            produtos_disponiveis_remover = st.session_state.estoque['Produto'].tolist()
            produto_remover = st.selectbox("Selecione o produto para remover:", produtos_disponiveis_remover, key="select_remove")
            if st.button("Excluir Produto"):
                st.session_state.estoque = st.session_state.estoque[st.session_state.estoque['Produto'] != produto_remover]
                st.success(f"Produto '{produto_remover}' removido com sucesso!")
                st.rerun()
        else:
            st.info("Nenhum produto cadastrado para remover.")

    dados_est = st.session_state.estoque.copy()
    if not dados_est.empty:
        dados_est['Valor Total'] = dados_est['Quantidade'] * dados_est['Valor Unitário']
        st.subheader("Estoque Atual")
        st.dataframe(dados_est.style.format({'Valor Unitário': 'R$ {:.2f}', 'Valor Total': 'R$ {:.2f}'}), hide_index=True)

with tab_vendas:
    st.subheader("🛒 Registro de Vendas")
    with st.form("form_venda"):
        if not st.session_state.estoque.empty:
            prod_venda = st.selectbox("Produto Vendido", st.session_state.estoque['Produto'].tolist())
            qtd_venda = st.number_input("Quantidade Vendida", min_value=1, step=1)
            btn_venda = st.form_submit_button("Registrar Venda")
            
            if btn_venda:
                idx = st.session_state.estoque[st.session_state.estoque['Produto'] == prod_venda].index[0]
                estoque_atual = st.session_state.estoque.at[idx, 'Quantidade']
                if qtd_venda <= estoque_atual:
                    st.session_state.estoque.at[idx, 'Quantidade'] = estoque_atual - qtd_venda
                    valor_unit = st.session_state.estoque.at[idx, 'Valor Unitário']
                    vlr_total = qtd_venda * valor_unit
                    
                    nova_venda = pd.DataFrame({
                        'Data': [datetime.now().strftime("%Y-%m-%d %H:%M")],
                        'Produto': [prod_venda],
                        'Quantidade': [qtd_venda],
                        'Valor Total': [vlr_total]
                    })
                    st.session_state.vendas = pd.concat([st.session_state.vendas, nova_venda], ignore_index=True)
                    
                    # Registra no financeiro
                    novo_fin = pd.DataFrame({
                        'Data': [datetime.now().strftime("%Y-%m-%d %H:%M")],
                        'Descrição': [f"Venda: {prod_venda}"],
                        'Tipo': ["Entrada"],
                        'Valor': [vlr_total]
                    })
                    st.session_state.financeiro = pd.concat([st.session_state.financeiro, novo_fin], ignore_index=True)
                    
                    st.success("Venda registrada com sucesso!")
                    st.rerun()
                else:
                    st.error("Quantidade em estoque insuficiente!")
        else:
            st.info("Cadastre produtos no estoque antes de registrar vendas.")

    st.subheader("Histórico de Vendas")
    st.dataframe(st.session_state.vendas.style.format({'Valor Total': 'R$ {:.2f}'}), hide_index=True)

with tab_financeiro:
    st.subheader("💰 Controle Financeiro")
    with st.expander("Registrar Transação Manual"):
        with st.form("form_fin"):
            desc = st.text_input("Descrição")
            tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            btn_fin = st.form_submit_button("Registrar Transação")
            if btn_fin and desc:
                transacao = pd.DataFrame({
                    'Data': [datetime.now().strftime("%Y-%m-%d %H:%M")],
                    'Descrição': [desc],
                    'Tipo': [tipo],
                    'Valor': [valor]
                })
                st.session_state.financeiro = pd.concat([st.session_state.financeiro, transacao], ignore_index=True)
                st.success("Transação registrada!")
                st.rerun()

    dados_fin = st.session_state.financeiro.copy()
    if not dados_fin.empty:
        st.dataframe(dados_fin.style.format({'Valor': 'R$ {:.2f}'}), hide_index=True)
        entradas = dados_fin[dados_fin['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = dados_fin[dados_fin['Tipo'] == 'Saída']['Valor'].sum()
        saldo = entradas - saidas
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", f"R$ {entradas:.2f}")
        c2.metric("Total Saídas", f"R$ {saidas:.2f}")
        c3.metric("Saldo Atual", f"R$ {saldo:.2f}")

with tab_fornecedores:
    st.subheader("🤝 Cadastro de Fornecedores")
    with st.expander("Adicionar Forncedor"):
        with st.form("form_forn"):
            nome_forn = st.text_input("Nome do Fornecedor")
            contato_forn = st.text_input("Contato (Telefone/Email)")
            cat_forn = st.text_input("Categoria de Produtos Fornecidos")
            btn_forn = st.form_submit_button("Cadastrar Fornecedor")
            if btn_forn and nome_forn:
                novo_forn = pd.DataFrame({
                    'Nome': [nome_forn],
                    'Contato': [contato_forn],
                    'Categoria de Produto': [cat_forn]
                })
                st.session_state.fornecedores = pd.concat([st.session_state.fornecedores, novo_forn], ignore_index=True)
                st.success("Fornecedor cadastrado com sucesso!")
                st.rerun()

    st.dataframe(st.session_state.fornecedores, hide_index=True)
