import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página e tema
st.set_page_config(layout="wide", page_title="Sistema ERP Integrado")

st.markdown("""
<style>
    /* Estilização Geral */
    .main { background-color: #f5f7fb; padding: 20px; }
    .title-text { color: #1f2937; font-weight: 700; font-size: 2.2rem; margin-bottom: 20px; text-align: center; }
    .stExpander, .stTabs { border: 1px solid #e0e4e8; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); background-color: #ffffff; margin-bottom: 15px; padding: 10px; }
    .stButton>button { background-color: #4f46e5; color: white; border-radius: 6px; font-weight: 600; border: none; padding: 10px 20px; transition: background-color 0.2s; }
    .stButton>button:hover { background-color: #4338ca; }
    .dataframe { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="title-text">🏢 Sistema ERP Integrado</p>', unsafe_allow_html=True)

# Inicialização do Session State
if 'estoque' not in st.session_state:
    st.session_state.estoque = pd.DataFrame(columns=['Produto', 'Categoria', 'Quantidade', 'Limite Mínimo', 'Valor Unitário'])
if 'vendas' not in st.session_state:
    st.session_state.vendas = pd.DataFrame(columns=['Data', 'Produto', 'Quantidade', 'Valor Total'])
if 'financeiro' not in st.session_state:
    st.session_state.financeiro = pd.DataFrame(columns=['Data', 'Descrição', 'Tipo', 'Valor'])
if 'fornecedores' not in st.session_state:
    st.session_state.fornecedores = pd.DataFrame(columns=['Nome', 'Contato', 'Categoria de Produto'])

# Criação das 4 Abas principais
tab_estoque, tab_vendas, tab_financeiro, tab_fornecedores = st.tabs(["📦 Estoque", "🛒 Vendas", "💰 Financeiro", "🤝 Fornecedores"])

# ==========================================
# ABA 1: ESTOQUE
# ==========================================
with tab_estoque:
    st.subheader("📦 Gestão de Estoque")
    
    with st.expander("Adicionar Novo Produto"):
        with st.form("form_produto"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Produto")
                categoria = st.selectbox("Categoria", ["Grãos", "Massas", "Óleos e Condimentos", "Bebidas", "Outros"])
                preco = st.number_input("Valor Unitário (R$)", min_value=0.0, step=0.01)
            with col2:
                qtd = st.number_input("Quantidade Inicial", min_value=0, step=1)
                limite = st.number_input("Limite Mínimo de Alerta", min_value=0, step=1)
            
            btn_adicionar = st.form_submit_button("Cadastrar Produto")
            
            if btn_adicionar and nome:
                produto_existe = st.session_state.estoque['Produto'].str.lower().eq(nome.lower()).any()
                
                if produto_existe:
                    st.error(f"⚠ Erro: O produto '{nome}' já está cadastrado no estoque!")
                else:
                    novo_item = pd.DataFrame({
                        'Produto': [nome.strip()],
                        'Categoria': [categoria],
                        'Quantidade': [qtd],
                        'Limite Mínimo': [limite],
                        'Valor Unitário': [preco]
                    })
                    st.session_state.estoque = pd.concat([st.session_state.estoque, novo_item], ignore_index=True)
                    st.success("✅ Produto cadastrado com sucesso!")
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
                st.session_state.estoque = st.session_state.estoque[st.session_state.estoque['Produto'] != produto_remover].reset_index(drop=True)
                st.success(f"Produto '{produto_remover}' removido com sucesso!")
                st.rerun()
        else:
            st.info("Nenhum produto cadastrado para remover.")

    dados_est = st.session_state.estoque.copy()
    
    # SISTEMA DE ALERTA DE ESTOQUE
    if not dados_est.empty:
        produtos_em_alerta = dados_est[dados_est['Quantidade'] <= dados_est['Limite Mínimo']]
        if not produtos_em_alerta.empty:
            st.warning("⚠️ **Atenção: Os seguintes produtos estão com estoque baixo!**")
            for _, row in produtos_em_alerta.iterrows():
                st.error(f"📉 **{row['Produto']}**: Restam apenas {row['Quantidade']} unidades (Limite: {row['Limite Mínimo']})")
    
    # EXIBIÇÃO DA TABELA
    if not dados_est.empty:
        dados_est['Valor Total'] = dados_est['Quantidade'] * dados_est['Valor Unitário']
        st.subheader("Estoque Atual")
        st.dataframe(dados_est.style.format({'Valor Unitário': 'R$ {:.2f}', 'Valor Total': 'R$ {:.2f}'}), hide_index=True)
    else:
        st.info("Seu estoque está vazio no momento.")

# ==========================================
# ABA 2: VENDAS
# ==========================================
with tab_vendas:
    st.subheader("🛒 Registro de Vendas")
    
    # REGISTRAR NOVA VENDA
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
                    
                    novo_fin = pd.DataFrame({
                        'Data': [datetime.now().strftime("%Y-%m-%d %H:%M")],
                        'Descrição': [f"Venda: {prod_venda}"],
                        'Tipo': ["Entrada"],
                        'Valor': [vlr_total]
                    })
                    st.session_state.financeiro = pd.concat([st.session_state.financeiro, novo_fin], ignore_index=True)
                    
                    st.success("Venda registrada com sucesso! Estoque e financeiro atualizados.")
                    st.rerun()
                else:
                    st.error(f"Quantidade em estoque insuficiente! (Disponível: {estoque_atual})")
        else:
            st.info("Cadastre produtos no estoque antes de registrar vendas.")
            btn_venda = st.form_submit_button("Registrar Venda", disabled=True)

    # NOVO: EDITAR OU CANCELAR VENDA
    with st.expander("✏️ Editar ou Cancelar Venda (Corrigir Erros)"):
        if not st.session_state.vendas.empty:
            df_vendas = st.session_state.vendas.copy()
            opcoes_venda = []
            
            # Cria lista para seleção
            for i, row in df_vendas.iterrows():
                texto = f"ID: {i} | {row['Data']} | {row['Produto']} | Qtd: {row['Quantidade']} | R$ {row['Valor Total']:.2f}"
                opcoes_venda.append(texto)
                
            venda_selecionada = st.selectbox("Selecione a venda para corrigir:", opcoes_venda)
            idx_venda = int(venda_selecionada.split("|")[0].replace("ID:", "").strip())
            
            # Pega os dados atuais da venda selecionada
            venda_atual = st.session_state.vendas.loc[idx_venda]
            old_prod = venda_atual['Produto']
            old_qtd = venda_atual['Quantidade']
            old_date = venda_atual['Data']
            old_total = venda_atual['Valor Total']
            
            # Verifica se o produto antigo ainda existe na lista do estoque
            lista_produtos = st.session_state.estoque['Produto'].tolist()
            index_prod = lista_produtos.index(old_prod) if old_prod in lista_produtos else 0
            
            with st.form("form_editar_venda"):
                st.write("**Novos dados da venda:**")
                novo_prod = st.selectbox("Produto Correto", lista_produtos, index=index_prod)
                nova_qtd = st.number_input("Quantidade Correta", min_value=1, step=1, value=int(old_qtd))
                
                col1, col2 = st.columns(2)
                btn_salvar_venda = col1.form_submit_button("Salvar Alteração")
                btn_cancelar_venda = col2.form_submit_button("Cancelar Venda (Estornar tudo)")
                
                if btn_cancelar_venda:
                    # 1. Devolve ao estoque
                    if old_prod in st.session_state.estoque['Produto'].values:
                        idx_est = st.session_state.estoque[st.session_state.estoque['Produto'] == old_prod].index[0]
                        st.session_state.estoque.at[idx_est, 'Quantidade'] += old_qtd
                    
                    # 2. Remove do financeiro
                    filtro_fin = (st.session_state.financeiro['Data'] == old_date) & \
                                 (st.session_state.financeiro['Descrição'] == f"Venda: {old_prod}") & \
                                 (st.session_state.financeiro['Valor'] == old_total)
                    st.session_state.financeiro = st.session_state.financeiro[~filtro_fin].reset_index(drop=True)
                    
                    # 3. Remove da tabela de vendas
                    st.session_state.vendas = st.session_state.vendas.drop(idx_venda).reset_index(drop=True)
                    
                    st.success("Venda cancelada! O produto voltou para o estoque e o valor saiu do financeiro.")
                    st.rerun()
                    
                if btn_salvar_venda:
                    # Simula o estoque para ver se a troca é possível
                    estoque_temp = st.session_state.estoque.copy()
                    
                    # Devolve o estoque antigo virtualmente
                    if old_prod in estoque_temp['Produto'].values:
                        idx_est_old = estoque_temp[estoque_temp['Produto'] == old_prod].index[0]
                        estoque_temp.at[idx_est_old, 'Quantidade'] += old_qtd
                        
                    # Verifica se tem saldo do novo produto
                    idx_est_new = estoque_temp[estoque_temp['Produto'] == novo_prod].index[0]
                    estoque_disponivel = estoque_temp.at[idx_est_new, 'Quantidade']
                    
                    if nova_qtd <= estoque_disponivel:
                        # 1. Efetiva devolução do antigo
                        if old_prod in st.session_state.estoque['Produto'].values:
                            idx_real_old = st.session_state.estoque[st.session_state.estoque['Produto'] == old_prod].index[0]
                            st.session_state.estoque.at[idx_real_old, 'Quantidade'] += old_qtd
                            
                        # 2. Efetiva retirada do novo
                        idx_real_new = st.session_state.estoque[st.session_state.estoque['Produto'] == novo_prod].index[0]
                        st.session_state.estoque.at[idx_real_new, 'Quantidade'] -= nova_qtd
                        
                        novo_valor_unit = st.session_state.estoque.at[idx_real_new, 'Valor Unitário']
                        novo_total = nova_qtd * novo_valor_unit
                        
                        # 3. Atualiza tabela de vendas
                        st.session_state.vendas.at[idx_venda, 'Produto'] = novo_prod
                        st.session_state.vendas.at[idx_venda, 'Quantidade'] = nova_qtd
                        st.session_state.vendas.at[idx_venda, 'Valor Total'] = novo_total
                        
                        # 4. Atualiza financeiro
                        filtro_fin = (st.session_state.financeiro['Data'] == old_date) & \
                                     (st.session_state.financeiro['Descrição'] == f"Venda: {old_prod}") & \
                                     (st.session_state.financeiro['Valor'] == old_total)
                        idx_fin = st.session_state.financeiro[filtro_fin].index
                        
                        if not idx_fin.empty:
                            st.session_state.financeiro.at[idx_fin[0], 'Descrição'] = f"Venda: {novo_prod}"
                            st.session_state.financeiro.at[idx_fin[0], 'Valor'] = novo_total
                            
                        st.success("Venda atualizada com sucesso! Estoque e financeiro foram corrigidos automaticamente.")
                        st.rerun()
                    else:
                        st.error(f"Estoque insuficiente para '{novo_prod}'! (Disponível: {estoque_disponivel})")
        else:
            st.info("Nenhuma venda para editar.")

    st.subheader("Histórico de Vendas")
    if not st.session_state.vendas.empty:
        st.dataframe(st.session_state.vendas.style.format({'Valor Total': 'R$ {:.2f}'}), hide_index=True)
    else:
        st.info("Nenhuma venda registrada ainda.")

# ==========================================
# ABA 3: FINANCEIRO
# ==========================================
with tab_financeiro:
    st.subheader("💰 Controle Financeiro")
    
    with st.expander("Registrar Transação Manual (Despesas etc.)"):
        with st.form("form_fin"):
            desc = st.text_input("Descrição (Ex: Conta de Luz, Material, Fornecedor)")
            tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
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
                
    with st.expander("🗑️ Remover Transação Manual (Corrigir Erro)"):
        st.warning("Nota: Para cancelar Vendas, use a aba de Vendas. Use este espaço para corrigir despesas ou entradas manuais.")
        if not st.session_state.financeiro.empty:
            df_fin = st.session_state.financeiro.copy()
            opcoes_exclusao = []
            
            for i, row in df_fin.iterrows():
                texto = f"ID: {i} | {row['Data']} | {row['Tipo']} | {row['Descrição']} | R$ {row['Valor']:.2f}"
                opcoes_exclusao.append(texto)
                
            transacao_excluir = st.selectbox("Selecione a transação que deseja apagar:", opcoes_exclusao)
            
            if st.button("Apagar Registro Selecionado"):
                idx_excluir = int(transacao_excluir.split("|")[0].replace("ID:", "").strip())
                st.session_state.financeiro = st.session_state.financeiro.drop(idx_excluir).reset_index(drop=True)
                st.success("Transação apagada com sucesso!")
                st.rerun()
        else:
            st.info("Não há transações financeiras para remover.")

    dados_fin = st.session_state.financeiro.copy()
    if not dados_fin.empty:
        entradas = dados_fin[dados_fin['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = dados_fin[dados_fin['Tipo'] == 'Saída']['Valor'].sum()
        saldo = entradas - saidas
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", f"R$ {entradas:.2f}")
        c2.metric("Total Saídas", f"R$ {saidas:.2f}")
        c3.metric("Saldo Atual", f"R$ {saldo:.2f}")
        
        st.subheader("Extrato")
        st.dataframe(dados_fin.style.format({'Valor': 'R$ {:.2f}'}), hide_index=True)
    else:
        st.info("Nenhuma movimentação financeira registrada.")

# ==========================================
# ABA 4: FORNECEDORES
# ==========================================
with tab_fornecedores:
    st.subheader("🤝 Cadastro de Fornecedores")
    with st.expander("Adicionar Fornecedor"):
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

    if not st.session_state.fornecedores.empty:
        st.dataframe(st.session_state.fornecedores, hide_index=True)
    else:
        st.info("Nenhum fornecedor cadastrado.")
