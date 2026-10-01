import io
import os
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# Importações do ReportLab para Geração de PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="Gestão de Produtos & Controle",
    page_icon="📦",
    layout="wide"
)

# ----------------------------------------------------
# CONEXÃO COM O SUPABASE
# ----------------------------------------------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("As credenciais do Supabase (SUPABASE_URL e SUPABASE_KEY) não foram encontradas nos Secrets ou variáveis de ambiente.")
    st.stop()

@st.cache_resource
def init_connection() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# Função auxiliar para carregar dados de uma tabela
def carregar_dados(tabela):
    try:
        response = supabase.table(tabela).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao carregar dados da tabela {tabela}: {e}")
        return pd.DataFrame()

# ----------------------------------------------------
# FUNÇÃO DE RELATÓRIO DE ESTOQUE (COM TOTAIS)
# ----------------------------------------------------
def gerar_relatorio_estoque_pdf(df_estoque):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#1f2937'), spaceAfter=15, alignment=1
    )
    th_style = ParagraphStyle('THStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.whitesmoke, alignment=1)
    td_style = ParagraphStyle('TDStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#374151'), alignment=1)
    td_left = ParagraphStyle('TDLeft', parent=td_style, alignment=0)

    elements.append(Paragraph("Relatório Geral de Estoque e Custos", title_style))
    elements.append(Spacer(1, 10))

    if df_estoque.empty:
        elements.append(Paragraph("Nenhum produto cadastrado no estoque.", td_style))
    else:
        df_estoque['quantidade'] = pd.to_numeric(df_estoque['quantidade'], errors='coerce').fillna(0)
        df_estoque['preco_custo'] = pd.to_numeric(df_estoque['preco_custo'], errors='coerce').fillna(0.0)
        df_estoque['valor_unitario'] = pd.to_numeric(df_estoque['valor_unitario'], errors='coerce').fillna(0.0)

        df_estoque['total_custo'] = df_estoque['quantidade'] * df_estoque['preco_custo']
        df_estoque['total_venda'] = df_estoque['quantidade'] * df_estoque['valor_unitario']

        table_data = [[
            Paragraph("Produto", th_style),
            Paragraph("Cat.", th_style),
            Paragraph("Qtd", th_style),
            Paragraph("Custo Unit.", th_style),
            Paragraph("Venda Unit.", th_style),
            Paragraph("Total Custo", th_style),
            Paragraph("Total Venda", th_style)
        ]]

        total_qtd = 0
        total_geral_custo = 0.0
        total_geral_venda = 0.0

        for _, row in df_estoque.iterrows():
            q = row['quantidade']
            pc = row['preco_custo']
            pv = row['valor_unitario']
            tc = row['total_custo']
            tv = row['total_venda']

            total_qtd += q
            total_geral_custo += tc
            total_geral_venda += tv

            table_data.append([
                Paragraph(str(row.get('produto', '')), td_left),
                Paragraph(str(row.get('categoria', '')), td_style),
                Paragraph(str(int(q)), td_style),
                Paragraph(f"R$ {pc:.2f}", td_style),
                Paragraph(f"R$ {pv:.2f}", td_style),
                Paragraph(f"R$ {tc:.2f}", td_style),
                Paragraph(f"R$ {tv:.2f}", td_style)
            ])

        th_total_style = ParagraphStyle('THTotals', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#111827'), alignment=1)
        
        table_data.append([
            Paragraph("TOTAIS GERAIS", th_total_style),
            Paragraph("-", th_total_style),
            Paragraph(str(int(total_qtd)), th_total_style),
            Paragraph("-", th_total_style),
            Paragraph("-", th_total_style),
            Paragraph(f"R$ {total_geral_custo:.2f}", th_total_style),
            Paragraph(f"R$ {total_geral_venda:.2f}", th_total_style)
        ])

        col_widths = [132, 70, 45, 65, 65, 87, 88]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563eb')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#d1d5db')),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#e5e7eb')),
            ('LINEABOVE', (0,-1), (-1,-1), 1.5, colors.HexColor('#2563eb')),
            ('BOTTOMPADDING', (0,-1), (-1,-1), 6),
            ('TOPPADDING', (0,-1), (-1,-1), 6),
        ]))
        
        elements.append(t)
        elements.append(Spacer(1, 15))
        resumo_style = ParagraphStyle('ResumoStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#1f2937'))
        elements.append(Paragraph("Resumo do Inventário:", resumo_style))
        elements.append(Paragraph(f"• Capital Total Investido (Custo): R$ {total_geral_custo:.2f}", td_left))
        elements.append(Paragraph(f"• Valor Potencial de Retorno (Venda): R$ {total_geral_venda:.2f}", td_left))
        lucro_estimado = total_geral_venda - total_geral_custo
        elements.append(Paragraph(f"• Lucro Bruto Estimado: R$ {lucro_estimado:.2f}", td_left))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ----------------------------------------------------
# FUNÇÃO DE RELATÓRIO DE CAIXA EM PDF
# ----------------------------------------------------
def gerar_relatorio_caixa_pdf(df_caixa):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#1f2937'), spaceAfter=15, alignment=1)
    th_style = ParagraphStyle('THStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.whitesmoke, alignment=1)
    td_style = ParagraphStyle('TDStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#374151'), alignment=1)
    td_left = ParagraphStyle('TDLeft', parent=td_style, alignment=0)

    elements.append(Paragraph("Relatório de Fechamento de Caixa & Sangria", title_style))
    elements.append(Spacer(1, 10))

    if df_caixa.empty:
        elements.append(Paragraph("Nenhum registro de caixa encontrado.", td_style))
    else:
        df_caixa['valor'] = pd.to_numeric(df_caixa['valor'], errors='coerce').fillna(0.0)

        table_data = [[
            Paragraph("Data", th_style),
            Paragraph("Tipo", th_style),
            Paragraph("Responsável", th_style),
            Paragraph("Valor (R$)", th_style),
            Paragraph("Observação", th_style)
        ]]

        total_entradas = 0.0
        total_saidas = 0.0

        for _, row in df_caixa.iterrows():
            tipo = str(row.get('tipo_registro', ''))
            val = row['valor']
            
            if tipo in ["Abertura", "Suprimento", "Fechamento"]:
                total_entradas += val
            elif tipo in ["Sangria", "Retirada"]:
                total_saidas += val

            table_data.append([
                Paragraph(str(row.get('data', '')), td_style),
                Paragraph(tipo, td_style),
                Paragraph(str(row.get('responsavel', '')), td_style),
                Paragraph(f"R$ {val:.2f}", td_style),
                Paragraph(str(row.get('observacao', '')), td_left)
            ])

        col_widths = [80, 90, 100, 80, 202]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#059669')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
        ]))
        
        elements.append(t)
        elements.append(Spacer(1, 15))
        
        # Resumo do Caixa
        saldo_caixa = total_entradas - total_saidas
        resumo_style = ParagraphStyle('ResumoStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#1f2937'))
        elements.append(Paragraph("Balanço do Período:", resumo_style))
        elements.append(Paragraph(f"• Total Entradas / Suprimentos: R$ {total_entradas:.2f}", td_left))
        elements.append(Paragraph(f"• Total Sangrias / Saídas: R$ {total_saidas:.2f}", td_left))
        elements.append(Paragraph(f"• Saldo Final em Caixa: R$ {saldo_caixa:.2f}", td_left))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ----------------------------------------------------
# NAVEGAÇÃO LATERAL (SIDEBAR)
# ----------------------------------------------------
st.sidebar.title("Navegação")
menu = st.sidebar.selectbox(
    "Escolha o Módulo",
    ["Estoque", "Vendas", "Financeiro", "Fornecedores", "Pedidos de Compra", "Clientes", "Fechamento de Caixa"]
)

st.sidebar.markdown("---")
st.sidebar.info("Sistema integrado ao Supabase com relatórios em PDF atualizados.")

# ----------------------------------------------------
# MÓDULO 1: ESTOQUE & RELATÓRIO PDF
# ----------------------------------------------------
if menu == "Estoque":
    st.header("📦 Gestão de Estoque")
    df_estoque = carregar_dados("estoque")

    with st.expander("➕ Adicionar Novo Produto"):
        with st.form("form_novo_produto"):
            col1, col2 = st.columns(2)
            with col1:
                p_nome = st.text_input("Nome do Produto")
                p_cat = st.text_input("Categoria")
                p_qtd = st.number_input("Quantidade", min_value=0, step=1)
            with col2:
                p_min = st.number_input("Limite Mínimo", min_value=0, step=1)
                p_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, format="%.2f")
                p_venda = st.number_input("Valor Unitário / Venda (R$)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("Salvar Produto"):
                if p_nome:
                    try:
                        supabase.table("estoque").insert({
                            "produto": p_nome, "categoria": p_cat, "quantidade": p_qtd,
                            "limite_minimo": p_min, "preco_custo": p_custo, "valor_unitario": p_venda
                        }).execute()
                        st.success("Produto cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                else:
                    st.warning("O nome do produto é obrigatório.")

    st.subheader("Produtos Cadastrados")
    if not df_estoque.empty:
        st.dataframe(df_estoque, use_container_width=True)
        st.markdown("---")
        st.subheader("Gerar Relatório em PDF")
        if st.button("📄 Baixar Relatório de Estoque (PDF com Totais)"):
            pdf_bytes = gerar_relatorio_estoque_pdf(df_estoque)
            st.download_button("📥 Clique aqui para salvar o PDF", data=pdf_bytes, file_name="relatorio_estoque.pdf", mime="application/pdf")
    else:
        st.info("Nenhum produto encontrado no banco de dados.")

# ----------------------------------------------------
# MÓDULO 2: VENDAS
# ----------------------------------------------------
elif menu == "Vendas":
    st.header("🛒 Gestão de Vendas")
    df_vendas = carregar_dados("vendas")
    
    with st.expander("Registrar Nova Venda"):
        with st.form("form_venda"):
            v_data = st.text_input("Data (AAAA-MM-DD)", value=str(pd.Timestamp.today().date()))
            v_prod = st.text_input("Produto")
            v_qtd = st.number_input("Quantidade", min_value=1, step=1)
            v_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
            v_lucro = st.number_input("Lucro (R$)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("Registrar Venda"):
                try:
                    supabase.table("vendas").insert({
                        "data": v_data, "produto": v_prod, "quantidade": v_qtd,
                        "valor_total": v_total, "lucro": v_lucro
                    }).execute()
                    st.success("Venda registrada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    if not df_vendas.empty:
        st.dataframe(df_vendas, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada.")

# ----------------------------------------------------
# MÓDULO 3: FINANCEIRO
# ----------------------------------------------------
elif menu == "Financeiro":
    st.header("💰 Controle Financeiro")
    df_fin = carregar_dados("financeiro")
    
    with st.expander("Adicionar Lançamento"):
        with st.form("form_fin"):
            f_data = st.text_input("Data (AAAA-MM-DD)", value=str(pd.Timestamp.today().date()))
            f_tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            f_cat = st.text_input("Categoria")
            f_desc = st.text_input("Descrição")
            f_val = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("Salvar Lançamento"):
                try:
                    supabase.table("financeiro").insert({
                        "data": f_data, "tipo": f_tipo, "categoria": f_cat,
                        "descricao": f_desc, "valor": f_val
                    }).execute()
                    st.success("Lançamento salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    if not df_fin.empty:
        st.dataframe(df_fin, use_container_width=True)
    else:
        st.info("Nenhum registro financeiro encontrado.")

# ----------------------------------------------------
# MÓDULO 4: FORNECEDORES
# ----------------------------------------------------
elif menu == "Fornecedores":
    st.header("🏢 Fornecedores")
    df_forn = carregar_dados("fornecedores")
    
    with st.expander("Cadastrar Fornecedor"):
        with st.form("form_forn"):
            fn_nome = st.text_input("Nome da Empresa")
            fn_cnpj = st.text_input("CNPJ")
            fn_contato = st.text_input("Contato")
            fn_tel = st.text_input("Telefone")
            fn_email = st.text_input("E-mail")
            fn_obs = st.text_area("Observações")
            
            if st.form_submit_button("Salvar Fornecedor"):
                try:
                    supabase.table("fornecedores").insert({
                        "nome_empresa": fn_nome, "cnpj": fn_cnpj, "contato": fn_contato,
                        "telefone": fn_tel, "email": fn_email, "observacoes": fn_obs
                    }).execute()
                    st.success("Fornecedor cadastrado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    if not df_forn.empty:
        st.dataframe(df_forn, use_container_width=True)
    else:
        st.info("Nenhum fornecedor cadastrado.")

# ----------------------------------------------------
# MÓDULO 5: PEDIDOS DE COMPRA
# ----------------------------------------------------
elif menu == "Pedidos de Compra":
    st.header("📋 Pedidos de Compra")
    df_ped = carregar_dados("pedidos_compra")
    
    with st.expander("Novo Pedido de Compra"):
        with st.form("form_ped"):
            p_data = st.text_input("Data (AAAA-MM-DD)", value=str(pd.Timestamp.today().date()))
            p_forn = st.text_input("Fornecedor")
            p_prod = st.text_input("Produto")
            p_qtd = st.number_input("Quantidade", min_value=1, step=1)
            p_custo_u = st.number_input("Preço Custo Unitário (R$)", min_value=0.0, format="%.2f")
            p_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
            p_status = st.selectbox("Status", ["Pendente", "Aprovado", "Entregue", "Cancelado"])
            
            if st.form_submit_button("Salvar Pedido"):
                try:
                    supabase.table("pedidos_compra").insert({
                        "data": p_data, "fornecedor": p_forn, "produto": p_prod,
                        "quantidade": p_qtd, "preco_custo_unitario": p_custo_u,
                        "valor_total": p_total, "status": p_status
                    }).execute()
                    st.success("Pedido salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    if not df_ped.empty:
        st.dataframe(df_ped, use_container_width=True)
    else:
        st.info("Nenhum pedido de compra registrado.")

# ----------------------------------------------------
# MÓDULO 6: CLIENTES
# ----------------------------------------------------
elif menu == "Clientes":
    st.header("👥 Gestão de Clientes")
    df_cli = carregar_dados("clientes")
    
    with st.expander("Cadastrar Cliente"):
        with st.form("form_cli"):
            c_nome = st.text_input("Nome")
            c_doc = st.text_input("CPF/CNPJ")
            c_tel = st.text_input("Telefone")
            c_email = st.text_input("E-mail")
            c_end = st.text_input("Endereço")
            c_obs = st.text_area("Observações")
            
            if st.form_submit_button("Salvar Cliente"):
                try:
                    supabase.table("clientes").insert({
                        "nome": c_nome, "cpf_cnpj": c_doc, "telefone": c_tel,
                        "email": c_email, "endereco": c_end, "observacoes": c_obs
                    }).execute()
                    st.success("Cliente cadastrado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    if not df_cli.empty:
        st.dataframe(df_cli, use_container_width=True)
    else:
        st.info("Nenhum cliente cadastrado.")

# ----------------------------------------------------
# MÓDULO 7: FECHAMENTO DE CAIXA & SANGRIA (ATUALIZADO)
# ----------------------------------------------------
elif menu == "Fechamento de Caixa":
    st.header("🔐 Fechamento de Caixa & Sangria")
    df_cx = carregar_dados("fechamento_caixa")
    
    # Exibição de métricas rápidas de caixa se houver dados
    if not df_cx.empty:
        df_cx['valor'] = pd.to_numeric(df_cx['valor'], errors='coerce').fillna(0.0)
        t_abertura = df_cx[df_cx['tipo_registro'].isin(['Abertura', 'Suprimento'])]['valor'].sum()
        t_sangria = df_cx[df_cx['tipo_registro'].isin(['Sangria', 'Retirada'])]['valor'].sum()
        saldo_atual = t_abertura - t_sangria
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Entradas / Suprimentos", f"R$ {t_abertura:.2f}")
        col_m2.metric("Total Sangrias / Saídas", f"R$ {t_sangria:.2f}")
        col_m3.metric("Saldo Estimado em Caixa", f"R$ {saldo_atual:.2f}")
        st.markdown("---")

    with st.expander("➕ Novo Registro de Caixa (Abertura, Fechamento, Sangria, Suprimento)"):
        with st.form("form_cx"):
            cx_data = st.text_input("Data (AAAA-MM-DD)", value=str(pd.Timestamp.today().date()))
            cx_tipo = st.selectbox("Tipo de Operação", ["Abertura", "Fechamento", "Sangria", "Suprimento"])
            cx_val = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            cx_resp = st.text_input("Responsável")
            cx_obs = st.text_area("Observação / Motivo")
            
            if st.form_submit_button("Registrar Operação de Caixa"):
                try:
                    supabase.table("fechamento_caixa").insert({
                        "data": cx_data,
                        "tipo_registro": cx_tipo,
                        "valor": cx_val,
                        "responsavel": cx_resp,
                        "observacao": cx_obs
                    }).execute()
                    st.success("Operação de caixa registrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar registro de caixa: {e}")

    st.subheader("Histórico de Operações de Caixa")
    if not df_cx.empty:
        st.dataframe(df_cx, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Gerar Relatório de Caixa em PDF")
        if st.button("📄 Baixar Relatório de Fechamento de Caixa (PDF)"):
            pdf_caixa_bytes = gerar_relatorio_caixa_pdf(df_cx)
            st.download_button(
                label="📥 Clique aqui para salvar o PDF do Caixa",
                data=pdf_caixa_bytes,
                file_name="relatorio_fechamento_caixa.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Nenhum registro de caixa encontrado.")
