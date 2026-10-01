import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from supabase import create_client, Client
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# ==========================================
# CONFIGURAÇÕES INICIAIS E TEMA
# ==========================================
st.set_page_config(layout="wide", page_title="Sistema ERP Integrado", page_icon="📦")

st.markdown("""
<style>
    .main { padding: 20px; }
    .title-text { font-weight: 700; font-size: 2.2rem; margin-bottom: 20px; text-align: center; }
    .stExpander, .stTabs { 
        border-radius: 8px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); 
        margin-bottom: 15px; 
        padding: 10px; 
    }
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
    .dataframe { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONEXÃO COM O SUPABASE
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Erro ao conectar com o Supabase. Verifique as secrets. Erro: {e}")
    st.stop()

# ==========================================
# CONTROLE DE SESSÃO / AUTENTICAÇÃO
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

def tela_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<p class="title-text">🔐 Acesso Restrito</p>', unsafe_allow_html=True)
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            botao_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if botao_login:
                if usuario == "JOHN" and senha == "fgxv4VP0":
                    st.session_state.autenticado = True
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

if not st.session_state.autenticado:
    tela_login()
    st.stop()

with st.sidebar:
    st.write(f"Logado como: **Administrador**")
    if st.button("🚪 Sair do Sistema"):
        st.session_state.autenticado = False
        st.rerun()
    st.markdown("---")
    st.success("🟢 Conectado ao Supabase")

st.markdown('<p class="title-text">📦 Sistema ERP Integrado (Nuvem)</p>', unsafe_allow_html=True)

# ==========================================
# FUNÇÕES DE BUSCA DO BANCO DE DADOS
# ==========================================
def carregar_dados_tabela(nome_tabela):
    try:
        resposta = supabase.table(nome_tabela).select("*").execute()
        df = pd.DataFrame(resposta.data)
        if not df.empty and 'id' in df.columns:
            df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        return pd.DataFrame()

# Carregamento inicial
df_estoque = carregar_dados_tabela("estoque")
df_vendas = carregar_dados_tabela("vendas")
df_financeiro = carregar_dados_tabela("financeiro")
df_fornecedores = carregar_dados_tabela("fornecedores")
df_pedidos_compra = carregar_dados_tabela("pedidos_compra")
df_clientes = carregar_dados_tabela("clientes")
df_caixa = carregar_dados_tabela("fechamento_caixa")

# ==========================================
# NORMALIZAÇÃO DE COLUNAS
# ==========================================
if df_estoque.empty:
    df_estoque = pd.DataFrame(columns=['id', 'Produto', 'Categoria', 'Quantidade', 'Limite Mínimo', 'Valor Unitário', 'Preço de Custo'])
else:
    col_map_est = {}
    for col in df_estoque.columns:
        c_lower = col.lower().strip()
        if c_lower in ['produto', 'nome']: col_map_est[col] = 'Produto'
        elif c_lower in ['categoria']: col_map_est[col] = 'Categoria'
        elif c_lower in ['quantidade', 'qtd']: col_map_est[col] = 'Quantidade'
        elif c_lower in ['limite_minimo', 'limiteminimo', 'limite']: col_map_est[col] = 'Limite Mínimo'
        elif c_lower in ['valor_unitario', 'valorunitario', 'preco', 'valor']: col_map_est[col] = 'Valor Unitário'
        elif c_lower in ['preco_custo', 'precocusto', 'custo']: col_map_est[col] = 'Preço de Custo'
    df_estoque = df_estoque.rename(columns=col_map_est)

if df_vendas.empty:
    df_vendas = pd.DataFrame(columns=['id', 'Data', 'Produto', 'Quantidade', 'Valor Total', 'Lucro'])
else:
    col_map_vendas = {}
    for col in df_vendas.columns:
        c_lower = col.lower().strip()
        if c_lower == 'data': col_map_vendas[col] = 'Data'
        elif c_lower == 'produto': col_map_vendas[col] = 'Produto'
        elif c_lower == 'quantidade': col_map_vendas[col] = 'Quantidade'
        elif c_lower in ['valor_total', 'valortotal']: col_map_vendas[col] = 'Valor Total'
        elif c_lower == 'lucro': col_map_vendas[col] = 'Lucro'
    df_vendas = df_vendas.rename(columns=col_map_vendas)

if df_financeiro.empty:
    df_financeiro = pd.DataFrame(columns=['id', 'Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])
else:
    col_map_fin = {}
    for col in df_financeiro.columns:
        c_lower = col.lower().strip()
        if c_lower == 'data': col_map_fin[col] = 'Data'
        elif c_lower in ['descricao', 'descrição']: col_map_fin[col] = 'Descrição'
        elif c_lower == 'tipo': col_map_fin[col] = 'Tipo'
        elif c_lower == 'categoria': col_map_fin[col] = 'Categoria'
        elif c_lower == 'valor': col_map_fin[col] = 'Valor'
    df_financeiro = df_financeiro.rename(columns=col_map_fin)

if df_fornecedores.empty:
    df_fornecedores = pd.DataFrame(columns=['id', 'nome_empresa', 'cnpj', 'contato', 'telefone', 'email', 'observacoes'])
if df_pedidos_compra.empty:
    df_pedidos_compra = pd.DataFrame(columns=['id', 'data', 'fornecedor', 'produto', 'quantidade', 'preco_custo_unitario', 'valor_total', 'status'])
if df_clientes.empty:
    df_clientes = pd.DataFrame(columns=['id', 'nome', 'cpf_cnpj', 'telefone', 'email', 'endereco', 'observacoes'])
if df_caixa.empty:
    df_caixa = pd.DataFrame(columns=['id', 'data', 'tipo_registro', 'valor', 'responsavel', 'observacao'])

# Garante colunas de apoio
if 'Preço de Custo' not in df_estoque.columns: df_estoque['Preço de Custo'] = 0.00
if 'Limite Mínimo' not in df_estoque.columns: df_estoque['Limite Mínimo'] = 0
if 'Valor Unitário' not in df_estoque.columns: df_estoque['Valor Unitário'] = 0.00
if 'Categoria' not in df_estoque.columns: df_estoque['Categoria'] = 'Geral'
if 'Quantidade' not in df_estoque.columns: df_estoque['Quantidade'] = 0

# ==========================================
# FUNÇÃO DE GERAÇÃO DE RELATÓRIO PDF
# ==========================================
def gerar_relatorio_pdf():
    """Gera um PDF completo com todas as seções do ERP integrado ao Supabase."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=1 * cm, rightMargin=1 * cm,
        topMargin=1 * cm, bottomMargin=1 * cm
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'Titulo', parent=styles['Heading1'], fontSize=18,
        alignment=1, spaceAfter=10, textColor=colors.HexColor('#4f46e5')
    )
    sub_style = ParagraphStyle(
        'Sub', parent=styles['Heading2'], fontSize=13,
        spaceAfter=6, spaceBefore=10, textColor=colors.HexColor('#4338ca')
    )
    normal = styles['Normal']

    elementos = []
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    elementos.append(Paragraph("📦 Sistema ERP Integrado - Relatório Geral", titulo_style))
    elementos.append(Paragraph(f"Gerado em: {agora}", normal))
    elementos.append(Spacer(1, 0.5 * cm))

    # ---------- 1. ESTOQUE ----------
    elementos.append(Paragraph("1. Estoque (com Custo Total e Venda Total)", sub_style))
    if not df_estoque.empty:
        dados = [['Produto', 'Categoria', 'Qtd',
                  'Preço Custo (R$)', 'Valor Unit. (R$)',
                  'Valor Custo Total (R$)', 'Valor Venda Total (R$)']]
        total_qtd = 0
        total_custo = 0.0
        total_venda = 0.0

        for _, row in df_estoque.iterrows():
            q = int(pd.to_numeric(row['Quantidade'], errors='coerce') or 0)
            pc = float(pd.to_numeric(row['Preço de Custo'], errors='coerce') or 0)
            pv = float(pd.to_numeric(row['Valor Unitário'], errors='coerce') or 0)
            vct = q * pc
            vvt = q * pv
            total_qtd += q
            total_custo += vct
            total_venda += vvt
            dados.append([
                str(row['Produto'])[:35],
                str(row['Categoria'])[:20],
                str(q),
                f"{pc:.2f}",
                f"{pv:.2f}",
                f"{vct:.2f}",
                f"{vvt:.2f}",
            ])

        # Linha de TOTAIS GERAIS
        dados.append([
            'TOTAIS GERAIS', '', str(total_qtd), '', '',
            f"R$ {total_custo:.2f}", f"R$ {total_venda:.2f}"
        ])

        t = Table(dados, repeatRows=1,
                  colWidths=[6*cm, 3.2*cm, 1.6*cm, 2.7*cm, 2.7*cm, 3.4*cm, 3.4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('SPAN', (0, -1), (1, -1)),
        ]))
        elementos.append(t)

        elementos.append(Spacer(1, 0.2 * cm))
        elementos.append(Paragraph(
            f"<b>Resumo do Inventário:</b> "
            f"Total de itens em estoque: <b>{total_qtd}</b> | "
            f"Capital Investido (Custo): <b>R$ {total_custo:.2f}</b> | "
            f"Potencial de Venda: <b>R$ {total_venda:.2f}</b> | "
            f"Lucro Potencial: <b>R$ {total_venda - total_custo:.2f}</b>",
            normal
        ))
    else:
        elementos.append(Paragraph("Nenhum produto cadastrado no estoque.", normal))
    elementos.append(Spacer(1, 0.4 * cm))

    # ---------- 2. VENDAS ----------
    elementos.append(Paragraph("2. Vendas", sub_style))
    if not df_vendas.empty:
        dados = [['ID', 'Data', 'Produto', 'Qtd', 'Valor Total (R$)', 'Lucro (R$)']]
        for _, row in df_vendas.iterrows():
            dados.append([
                str(row['id']),
                str(row['Data'])[:19],
                str(row['Produto'])[:35],
                str(int(row['Quantidade'])),
                f"{float(row['Valor Total']):.2f}",
                f"{float(row['Lucro']):.2f}"
            ])
        total_fat = df_vendas['Valor Total'].sum()
        total_luc = df_vendas['Lucro'].sum()
        dados.append(['', '', 'TOTAIS', '', f"R$ {total_fat:.2f}", f"R$ {total_luc:.2f}"])

        t = Table(dados, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('SPAN', (0, -1), (2, -1)),
        ]))
        elementos.append(t)
    else:
        elementos.append(Paragraph("Nenhuma venda registrada.", normal))
    elementos.append(Spacer(1, 0.4 * cm))

    # ---------- 3. FINANCEIRO ----------
    elementos.append(Paragraph("3. Financeiro", sub_style))
    if not df_financeiro.empty:
        dados = [['ID', 'Data', 'Tipo', 'Categoria', 'Descrição', 'Valor (R$)']]
        for _, row in df_financeiro.iterrows():
            dados.append([
                str(row['id']),
                str(row['Data'])[:19],
                str(row['Tipo']),
                str(row['Categoria'])[:25],
                str(row['Descrição'])[:40],
                f"{float(row['Valor']):.2f}"
            ])
        ent = df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor'].sum()
        sai = df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor'].sum()
        dados.append(['', '', '', '', f'Entradas: R$ {ent:.2f} | Saídas: R$ {sai:.2f} | Saldo: R$ {ent - sai:.2f}', ''])

        t = Table(dados, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('SPAN', (0, -1), (4, -1)),
        ]))
        elementos.append(t)
    else:
        elementos.append(Paragraph("Nenhum registro financeiro.", normal))
    elementos.append(Spacer(1, 0.4 * cm))

    # ---------- 4. CLIENTES ----------
    elementos.append(Paragraph("4. Clientes", sub_style))
    if not df_clientes.empty:
        dados = [['Nome', 'CPF/CNPJ', 'Telefone', 'E-mail', 'Endereço']]
        for _, row in df_clientes.iterrows():
            dados.append([
                str(row['nome'])[:30],
                str(row['cpf_cnpj'] or ''),
                str(row['telefone'] or ''),
                str(row['email'] or '')[:30],
                str(row['endereco'] or '')[:35]
            ])
        t = Table(dados, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ]))
        elementos.append(t)
    else:
        elementos.append(Paragraph("Nenhum cliente cadastrado.", normal))
    elementos.append(Spacer(1, 0.4 * cm))

    # ---------- 5. FORNECEDORES ----------
    elementos.append(Paragraph("5. Fornecedores", sub_style))
    if not df_fornecedores.empty:
        dados = [['Empresa', 'CNPJ', 'Contato', 'Telefone', 'E-mail']]
        for _, row in df_fornecedores.iterrows():
            dados.append([
                str(row['nome_empresa'])[:30],
                str(row['cnpj'] or ''),
                str(row['contato'] or ''),
                str(row['telefone'] or ''),
                str(row['email'] or '')
            ])
        t = Table(dados, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ]))
        elementos.append(t)
    else:
        elementos.append(Paragraph("Nenhum fornecedor cadastrado.", normal))
    elementos.append(Spacer(1, 0.4 * cm))

    # ---------- 6. PEDIDOS DE COMPRA ----------
    elementos.append(Paragraph("6. Pedidos de Compra", sub_style))
    if not df_pedidos_compra.empty:
        dados = [['ID', 'Data', 'Fornecedor', 'Produto', 'Qtd',
                  'Custo Unit. (R$)', 'Total (R$)', 'Status']]
        for _, row in df_pedidos_compra.iterrows():
            dados.append([
                str(row['id']),
                str(row['data'])[:19],
                str(row['fornecedor'])[:25],
                str(row['produto'])[:25],
                str(int(row['quantidade'])),
                f"{float(row['preco_custo_unitario']):.2f}",
                f"{float(row['valor_total']):.2f}",
                str(row['status'])
            ])
        total_ped = df_pedidos_compra['valor_total'].sum()
        dados.append(['', '', '', 'TOTAL', '', '', f"R$ {total_ped:.2f}", ''])
        t = Table(dados, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('SPAN', (0, -1), (3, -1)),
        ]))
        elementos.append(t)
    else:
        elementos.append(Paragraph("Nenhum pedido de compra registrado.", normal))
    elementos.append(Spacer(1, 0.4 * cm))

    # ---------- 7. FECHAMENTO DE CAIXA ----------
    elementos.append(Paragraph("7. Fechamento de Caixa", sub_style))
    if not df_caixa.empty:
        dados = [['ID', 'Data', 'Tipo', 'Valor (R$)', 'Responsável', 'Observação']]
        for _, row in df_caixa.iterrows():
            dados.append([
                str(row['id']),
                str(row['data'])[:19],
                str(row['tipo_registro']),
                f"{float(row['valor']):.2f}",
                str(row['responsavel'])[:25],
                str(row['observacao'] or '')[:35]
            ])
        t = Table(dados, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ]))
        elementos.append(t)
    else:
        elementos.append(Paragraph("Nenhuma operação de caixa registrada.", normal))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# ABAS PRINCIPAIS DO ERP
# ==========================================
tab_estoque, tab_planilhas_prod, tab_vendas, tab_despesas, tab_financeiro, tab_clientes, tab_fornecedores, tab_etiquetas, tab_curva_abc, tab_caixa, tab_dashboard, tab_relatorio = st.tabs([
    "📦 Estoque", 
    "📑 Fichas por Produto",
    "🛒 Vendas", 
    "💡 Despesas",
    "💰 Financeiro", 
    "👥 Clientes",
    "🤝 Fornecedores & Compras",
    "🏷 Etiquetas",
    "📊 Curva ABC & Vendas",
    "💵 Caixa & Sangria",
    "📈 Dashboard",
    "📄 Relatório PDF"
])

# ==========================================
# 1. ESTOQUE
# ==========================================
with tab_estoque:
    st.subheader("📦 Gestão de Estoque & Capital Investido")
    
    if not df_estoque.empty and 'Quantidade' in df_estoque.columns and 'Preço de Custo' in df_estoque.columns:
        total_investido_custo = (df_estoque['Quantidade'] * df_estoque['Preço de Custo']).sum()
        total_valor_venda = (df_estoque['Quantidade'] * df_estoque['Valor Unitário']).sum()
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("💰 Capital Total Investido (Custo)", f"R$ {total_investido_custo:.2f}")
        c_m2.metric("🏷 Valor Potencial de Venda", f"R$ {total_valor_venda:.2f}")
        c_m3.metric("📈 Lucro Potencial Estimado", f"R$ {total_valor_venda - total_investido_custo:.2f}")
        st.markdown("---")
        
    sub_est_cad, sub_est_ger = st.tabs(["➕ Cadastrar Produto", "✏️ Gerenciar, Editar e Excluir"])
    
    with sub_est_cad:
        with st.form("form_produto"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Produto")
                categoria = st.selectbox("Categoria", ["Grãos", "Massas", "Óleos e Condimentos", "Bebidas", "Outros"])
                preco_custo = st.number_input("Preço de Mercado / Custo Unitário (R$)", min_value=0.0, step=0.01)
                preco = st.number_input("Valor de Venda / Revenda Unitário (R$)", min_value=0.0, step=0.01)
            with col2:
                qtd = st.number_input("Quantidade Inicial em Estoque", min_value=0, step=1)
                limite = st.number_input("Limite Mínimo de Alerta", min_value=0, step=1)
            
            if st.form_submit_button("Cadastrar Produto") and nome:
                try:
                    supabase.table("estoque").insert({
                        "produto": nome.strip(), "categoria": categoria, "quantidade": int(qtd),
                        "limite_minimo": int(limite), "valor_unitario": float(preco), "preco_custo": float(preco_custo)
                    }).execute()
                    st.success("✅ Produto cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    with sub_est_ger:
        if not df_estoque.empty and 'Produto' in df_estoque.columns:
            prod_sel_ed = st.selectbox("Selecione o produto para Editar ou Excluir:", df_estoque['Produto'].tolist(), key="sel_ed_est")
            item_e = df_estoque[df_estoque['Produto'] == prod_sel_ed].iloc[0]
            
            with st.form("form_edit_est"):
                e_nome = st.text_input("Nome do Produto", value=str(item_e['Produto']))
                e_cat = st.text_input("Categoria", value=str(item_e['Categoria']))
                e_qtd = st.number_input("Quantidade", value=int(item_e['Quantidade']), min_value=0, step=1)
                e_lim = st.number_input("Limite Mínimo", value=int(item_e['Limite Mínimo']), min_value=0, step=1)
                e_custo = st.number_input("Preço de Mercado / Custo (R$)", value=float(item_e['Preço de Custo']), min_value=0.0, step=0.01)
                e_venda = st.number_input("Valor de Venda / Revenda (R$)", value=float(item_e['Valor Unitário']), min_value=0.0, step=0.01)
                
                col_b1, col_b2 = st.columns(2)
                salvar_ed = col_b1.form_submit_button("💾 Salvar Alterações do Produto")
                excluir_prod = col_b2.form_submit_button("🗑️ Excluir Produto Definitivamente")
                
                if salvar_ed:
                    supabase.table("estoque").update({
                        "produto": e_nome, "categoria": e_cat, "quantidade": int(e_qtd),
                        "limite_minimo": int(e_lim), "preco_custo": float(e_custo), "valor_unitario": float(e_venda)
                    }).eq("id", int(item_e['id'])).execute()
                    st.success("Produto atualizado com sucesso!")
                    st.rerun()
                    
                if excluir_prod:
                    supabase.table("estoque").delete().eq("id", int(item_e['id'])).execute()
                    st.success("Produto excluído!")
                    st.rerun()
                    
            st.markdown("---")
            dados_est = df_estoque.copy()
            dados_est['Valor Custo Total'] = dados_est['Quantidade'] * dados_est['Preço de Custo']
            dados_est['Valor Venda Total'] = dados_est['Quantidade'] * dados_est['Valor Unitário']
            st.dataframe(dados_est[['Produto', 'Categoria', 'Quantidade', 'Preço de Custo', 'Valor Unitário', 'Valor Custo Total', 'Valor Venda Total']].style.format({'Preço de Custo': 'R$ {:.2f}', 'Valor Unitário': 'R$ {:.2f}', 'Valor Custo Total': 'R$ {:.2f}', 'Valor Venda Total': 'R$ {:.2f}'}), hide_index=True)
        else:
            st.info("Nenhum produto no estoque.")

# ==========================================
# 2. PLANILHAS ESPECÍFICAS POR PRODUTO
# ==========================================
with tab_planilhas_prod:
    st.subheader("📑 Ficha e Simulação Individual por Produto")
    st.write("Visualize de forma isolada as especificações de mercado, preço de revenda e o faturamento total projetado para cada item.")
    
    if not df_estoque.empty and 'Produto' in df_estoque.columns:
        produto_escolhido = st.selectbox("Escolha o produto para ver a ficha detalhada:", df_estoque['Produto'].tolist(), key="sel_ficha_prod")
        
        p_info = df_estoque[df_estoque['Produto'] == produto_escolhido].iloc[0]
        
        qtd_atual = int(p_info['Quantidade'])
        preco_mercado = float(p_info['Preço de Custo'])
        preco_revenda_atual = float(p_info['Valor Unitário'])
        
        st.markdown("---")
        st.markdown(f"### 📋 Ficha Técnica: **{produto_escolhido}** ({p_info['Categoria']})")
        
        with st.form(f"form_ficha_{p_info['id']}"):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                st.metric("📦 Estoque Atual", f"{qtd_atual} un")
            with col_f2:
                novo_preco_revenda = st.number_input("Valor de Venda / Revenda (R$)", value=preco_revenda_atual, min_value=0.0, step=0.01)
            with col_f3:
                st.metric("🏷️ Valor de Mercado (Custo)", f"R$ {preco_mercado:.2f}")
                
            atualizar_preco_isolado = st.form_submit_button("Atualizar Valor de Revenda deste Produto")
            if atualizar_preco_isolado:
                supabase.table("estoque").update({"valor_unitario": float(novo_preco_revenda)}).eq("id", int(p_info['id'])).execute()
                st.success(f"Preço de revenda de '{produto_escolhido}' atualizado com sucesso!")
                st.rerun()
                
        custo_total_prod = qtd_atual * preco_mercado
        faturamento_total_prod = qtd_atual * novo_preco_revenda if 'novo_preco_revenda' in locals() else qtd_atual * preco_revenda_atual
        lucro_total_prod = faturamento_total_prod - custo_total_prod
        margem_lucro_pct = ((novo_preco_revenda - preco_mercado) / preco_mercado * 100) if preco_mercado > 0 else 0.0
        
        st.markdown("#### 💰 Resumo Financeiro Projetado (Com o Estoque Atual)")
        cp1, cp2, cp3, cp4 = st.columns(4)
        cp1.metric("Total Investido (Custo Mercado)", f"R$ {custo_total_prod:.2f}")
        cp2.metric("Total da Venda (Revenda)", f"R$ {faturamento_total_prod:.2f}")
        cp3.metric("Lucro Total Estimado", f"R$ {lucro_total_prod:.2f}")
        cp4.metric("Margem Unitária", f"{margem_lucro_pct:.1f}%")
        
        st.markdown("---")
        st.markdown("#### 📊 Tabela de Simulação de Venda em Lote")
        
        simulacao_dados = []
        for q in [1, 5, 10, 20, 50, 100, qtd_atual if qtd_atual > 0 else 1]:
            if q <= qtd_atual or q == [1, 5, 10, 20, 50, 100, qtd_atual if qtd_atual > 0 else 1][-1]:
                fat_q = q * novo_preco_revenda
                custo_q = q * preco_mercado
                lucro_q = fat_q - custo_q
                simulacao_dados.append({
                    "Quantidade": q,
                    "Preço de Mercado (Unit.)": preco_mercado,
                    "Preço de Revenda (Unit.)": novo_preco_revenda,
                    "Faturamento Total": fat_q,
                    "Custo Total": custo_q,
                    "Lucro Líquido": lucro_q
                })
        df_simulacao = pd.DataFrame(simulacao_dados).drop_duplicates(subset=['Quantidade'])
        st.dataframe(df_simulacao.style.format({
            'Preço de Mercado (Unit.)': 'R$ {:.2f}',
            'Preço de Revenda (Unit.)': 'R$ {:.2f}',
            'Faturamento Total': 'R$ {:.2f}',
            'Custo Total': 'R$ {:.2f}',
            'Lucro Líquido': 'R$ {:.2f}'
        }), hide_index=True)
        
    else:
        st.info("Cadastre produtos no estoque para visualizar as planilhas individuais.")

# ==========================================
# 3. VENDAS
# ==========================================
with tab_vendas:
    st.subheader("🛒 Registro de Vendas e Apuração de Lucro")
    
    if not df_vendas.empty and 'Lucro' in df_vendas.columns and 'Valor Total' in df_vendas.columns:
        total_faturamento = df_vendas['Valor Total'].sum()
        total_lucro_apurado = df_vendas['Lucro'].sum()
        c_v1, c_v2 = st.columns(2)
        c_v1.metric("💵 Faturamento Total de Vendas", f"R$ {total_faturamento:.2f}")
        c_v2.metric("📈 Lucro Real Líquido Apurado", f"R$ {total_lucro_apurado:.2f}")
        st.markdown("---")

    sub_v_reg, sub_v_ger = st.tabs(["➕ Registrar Venda", "📋 Histórico e Exclusão"])
    
    with sub_v_reg:
        with st.form("form_venda"):
            if not df_estoque.empty and 'Produto' in df_estoque.columns:
                prod_venda = st.selectbox("Produto Vendido", df_estoque['Produto'].tolist())
                qtd_venda = st.number_input("Quantidade", min_value=1, step=1)
                
                item_est_preview = df_estoque[df_estoque['Produto'] == prod_venda].iloc[0]
                p_unit = float(item_est_preview['Valor Unitário'])
                c_unit = float(item_est_preview['Preço de Custo'])
                est_atual = int(item_est_preview['Quantidade'])
                
                st.info(f"💡 **Prévia:** Preço de Revenda Unit.: R$ {p_unit:.2f} | Preço de Mercado Unit.: R$ {c_unit:.2f} | Lucro Unit.: R$ {p_unit - c_unit:.2f}")
                
                if st.form_submit_button("Confirmar e Registrar Venda"):
                    if qtd_venda <= est_atual:
                        vlr_total = qtd_venda * p_unit
                        lucro_venda = (p_unit - c_unit) * qtd_venda
                        data_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        supabase.table("estoque").update({"quantidade": est_atual - qtd_venda}).eq("id", int(item_est_preview['id'])).execute()
                        supabase.table("vendas").insert({"data": data_str, "produto": prod_venda, "quantidade": int(qtd_venda), "valor_total": float(vlr_total), "lucro": float(lucro_venda)}).execute()
                        supabase.table("financeiro").insert({"data": data_str, "descricao": f"Venda: {prod_venda} ({qtd_venda} un)", "tipo": "Entrada", "categoria": "Vendas de Produtos", "valor": float(vlr_total)}).execute()
                        
                        st.success(f"✅ Venda registrada! Lucro obtido nesta operação: R$ {lucro_venda:.2f}")
                        st.rerun()
                    else:
                        st.error("Estoque insuficiente para essa quantidade!")
            else:
                st.warning("Cadastre produtos no estoque primeiro.")

    with sub_v_ger:
        if not df_vendas.empty and 'Valor Total' in df_vendas.columns:
            st.dataframe(df_vendas[['id', 'Data', 'Produto', 'Quantidade', 'Valor Total', 'Lucro']].style.format({'Valor Total': 'R$ {:.2f}', 'Lucro': 'R$ {:.2f}'}), hide_index=True)
            st.markdown("---")
            lista_ids_vendas = [str(x) for x in df_vendas['id'].tolist()]
            v_id_del_str = st.selectbox("Selecione o ID da venda para excluir:", lista_ids_vendas, key="del_venda")
            if st.button("Excluir Venda Selecionada"):
                supabase.table("vendas").delete().eq("id", int(v_id_del_str)).execute()
                st.success("Venda excluída com sucesso!")
                st.rerun()
        else:
            st.info("Nenhuma venda registrada.")

# ==========================================
# 4. DESPESAS
# ==========================================
with tab_despesas:
    st.subheader("💡 Despesas do Comércio")
    sub_d_cad, sub_d_ger = st.tabs(["➕ Lançar Despesa", "📋 Gerenciar / Excluir Despesas"])
    
    with sub_d_cad:
        with st.form("form_desp"):
            c1, c2 = st.columns(2)
            with c1:
                cat_d = st.selectbox("Categoria", ["Energia / Luz", "Água", "Internet", "Aluguel", "Manutenção", "Impostos", "Outros"])
                desc_d = st.text_input("Descrição / Referência")
            with c2:
                vlr_d = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
                data_d = st.date_input("Data", value=datetime.now())
                
            if st.form_submit_button("Lançar Despesa"):
                supabase.table("financeiro").insert({
                    "data": f"{data_d} {datetime.now().strftime('%H:%M:%S')}",
                    "descricao": desc_d, "tipo": "Saída", "categoria": f"Despesa: {cat_d}", "valor": float(vlr_d)
                }).execute()
                st.success("Despesa lançada!")
                st.rerun()

    with sub_d_ger:
        df_despesas_apenas = df_financeiro[df_financeiro['Tipo'] == 'Saída'] if not df_financeiro.empty and 'Tipo' in df_financeiro.columns else pd.DataFrame()
        if not df_despesas_apenas.empty:
            st.dataframe(df_despesas_apenas[['id', 'Data', 'Categoria', 'Descrição', 'Valor']].style.format({'Valor': 'R$ {:.2f}'}), hide_index=True)
            st.markdown("---")
            lista_ids_desp = [str(x) for x in df_despesas_apenas['id'].tolist()]
            id_desp_del_str = st.selectbox("Selecione o ID da despesa para excluir:", lista_ids_desp, key="del_desp")
            if st.button("Excluir Despesa"):
                supabase.table("financeiro").delete().eq("id", int(id_desp_del_str)).execute()
                st.success("Despesa excluída!")
                st.rerun()
        else:
            st.info("Nenhuma despesa lançada.")

# ==========================================
# 5. FINANCEIRO
# ==========================================
with tab_financeiro:
    st.subheader("💰 Fluxo de Caixa Completo")
    if not df_financeiro.empty and 'Tipo' in df_financeiro.columns:
        total_ent = df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor'].sum()
        total_sai = df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas", f"R$ {total_ent:.2f}")
        c2.metric("Saídas", f"R$ {total_sai:.2f}")
        c3.metric("Saldo Líquido", f"R$ {total_ent - total_sai:.2f}")
        
        st.markdown("---")
        st.dataframe(df_financeiro[['id', 'Data', 'Tipo', 'Categoria', 'Descrição', 'Valor']].style.format({'Valor': 'R$ {:.2f}'}), hide_index=True)
        
        st.markdown("---")
        st.subheader("🗑️ Gerenciar / Excluir Registros Financeiros")
        
        try:
            res_fin = supabase.table("financeiro").select("id, data, descricao, valor, tipo").order("id", desc=True).execute()
            dados_financeiros = res_fin.data
            
            if dados_financeiros:
                opcoes_fin = {
                    f"ID: {item['id']} | Data: {item['data']} | Desc: {item['descricao']} | R$ {item['valor']} ({item['tipo']})": item['id']
                    for item in dados_financeiros
                }
                
                selecao_fin_str = st.selectbox("Selecione o registro financeiro para excluir:", list(opcoes_fin.keys()), key="select_del_financeiro")
                
                if st.button("Excluir Registro Financeiro Selecionado", type="primary"):
                    id_para_deletar = opcoes_fin[selecao_fin_str]
                    try:
                        supabase.table("financeiro").delete().eq("id", id_para_deletar).execute()
                        st.success(f"Registro financeiro ID {id_para_deletar} excluído com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir o registro financeiro: {e}")
            else:
                st.info("Nenhum registro financeiro disponível para exclusão.")
        except Exception as e:
            st.warning(f"Não foi possível carregar os registros para exclusão: {e}")
    else:
        st.info("Nenhum registro financeiro.")

# ==========================================
# 6. GESTÃO DE CLIENTES
# ==========================================
with tab_clientes:
    st.subheader("👥 Gestão de Clientes")
    sub_c_cad, sub_c_ger = st.tabs(["➕ Cadastrar Cliente", "✏️ Editar / Excluir Clientes"])
    
    with sub_c_cad:
        with st.form("form_cliente"):
            c1, c2 = st.columns(2)
            with c1:
                nome_cli = st.text_input("Nome Completo / Razão Social *")
                cpf_cnpj = st.text_input("CPF ou CNPJ")
                tel_cli = st.text_input("Telefone / WhatsApp")
            with c2:
                email_cli = st.text_input("E-mail")
                end_cli = st.text_input("Endereço Completo")
                obs_cli = st.text_area("Observações / Histórico")
                
            if st.form_submit_button("Salvar Cliente") and nome_cli:
                try:
                    supabase.table("clientes").insert({
                        "nome": nome_cli.strip(), "cpf_cnpj": cpf_cnpj.strip(), "telefone": tel_cli.strip(),
                        "email": email_cli.strip(), "endereco": end_cli.strip(), "observacoes": obs_cli.strip()
                    }).execute()
                    st.success(f"✅ Cliente '{nome_cli}' cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
                    
    with sub_c_ger:
        if not df_clientes.empty and 'nome' in df_clientes.columns:
            cli_sel_ed = st.selectbox("Selecione o cliente para Editar ou Excluir:", df_clientes['nome'].tolist(), key="sel_ed_cli")
            c_item = df_clientes[df_clientes['nome'] == cli_sel_ed].iloc[0]
            
            with st.form("form_edit_cli"):
                ec_nome = st.text_input("Nome Completo", value=str(c_item['nome']))
                ec_doc = st.text_input("CPF / CNPJ", value=str(c_item['cpf_cnpj']) if c_item['cpf_cnpj'] else "")
                ec_tel = st.text_input("Telefone", value=str(c_item['telefone']) if c_item['telefone'] else "")
                ec_email = st.text_input("E-mail", value=str(c_item['email']) if c_item['email'] else "")
                ec_end = st.text_input("Endereço", value=str(c_item['endereco']) if c_item['endereco'] else "")
                ec_obs = st.text_area("Observações", value=str(c_item['observacoes']) if c_item['observacoes'] else "")
                
                col_cb1, col_cb2 = st.columns(2)
                salvar_cli_ed = col_cb1.form_submit_button("💾 Salvar Alterações do Cliente")
                excluir_cli = col_cb2.form_submit_button("🗑 Excluir Cliente")
                
                if salvar_cli_ed:
                    supabase.table("clientes").update({
                        "nome": ec_nome, "cpf_cnpj": ec_doc, "telefone": ec_tel,
                        "email": ec_email, "endereco": ec_end, "observacoes": ec_obs
                    }).eq("id", int(c_item['id'])).execute()
                    st.success("Cliente atualizado com sucesso!")
                    st.rerun()
                    
                if excluir_cli:
                    supabase.table("clientes").delete().eq("id", int(c_item['id'])).execute()
                    st.success("Cliente excluído!")
                    st.rerun()
                    
            st.markdown("---")
            st.dataframe(df_clientes[['nome', 'cpf_cnpj', 'telefone', 'email', 'endereco', 'observacoes']], hide_index=True)
        else:
            st.info("Nenhum cliente cadastrado.")

# ==========================================
# 7. FORNECEDORES E COMPRAS
# ==========================================
with tab_fornecedores:
    st.subheader("🤝 Fornecedores e Pedidos de Compra")
    sub_f_cad, sub_f_ped, sub_f_ger = st.tabs(["➕ Novo Fornecedor", "📦 Registrar Pedido", "✏️ Gerenciar Fornecedores & Pedidos"])
    
    with sub_f_cad:
        with st.form("form_forn"):
            c1, c2 = st.columns(2)
            with c1:
                f_nome = st.text_input("Empresa *")
                f_cnpj = st.text_input("CNPJ")
                f_cont = st.text_input("Representante")
            with c2:
                f_tel = st.text_input("Telefone")
                f_email = st.text_input("E-mail")
                f_obs = st.text_area("Observações")
            if st.form_submit_button("Salvar Fornecedor") and f_nome:
                supabase.table("fornecedores").insert({"nome_empresa": f_nome, "cnpj": f_cnpj, "contato": f_cont, "telefone": f_tel, "email": f_email, "observacoes": f_obs}).execute()
                st.success("Fornecedor salvo!")
                st.rerun()

    with sub_f_ped:
        if not df_fornecedores.empty and 'nome_empresa' in df_fornecedores.columns:
            with st.form("form_ped"):
                c1, c2 = st.columns(2)
                with c1:
                    f_sel = st.selectbox("Fornecedor", df_fornecedores['nome_empresa'].tolist())
                    p_sel = st.selectbox("Produto", df_estoque['Produto'].tolist()) if not df_estoque.empty and 'Produto' in df_estoque.columns else st.text_input("Produto")
                    qtd_comp = st.number_input("Quantidade", min_value=1, step=1)
                with c2:
                    custo_u = st.number_input("Custo Unitário de Compra (R$)", min_value=0.01, step=0.01)
                    st_ped = st.selectbox("Status", ["Pendente", "Entregue"])
                
                up_est_auto = st.checkbox("Atualizar Estoque Automaticamente?", value=True)
                lanc_cx = st.checkbox("Lançar como Saída no Financeiro?", value=True)
                
                if st.form_submit_button("Registrar Pedido de Compra"):
                    total_p = qtd_comp * custo_u
                    dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    supabase.table("pedidos_compra").insert({"data": dt_str, "fornecedor": f_sel, "produto": p_sel, "quantidade": int(qtd_comp), "preco_custo_unitario": float(custo_u), "valor_total": float(total_p), "status": st_ped}).execute()
                    
                    if up_est_auto and not df_estoque.empty and 'Produto' in df_estoque.columns and p_sel in df_estoque['Produto'].values:
                        it = df_estoque[df_estoque['Produto'] == p_sel].iloc[0]
                        supabase.table("estoque").update({"quantidade": int(it['Quantidade']) + int(qtd_comp), "preco_custo": float(custo_u)}).eq("id", it['id']).execute()
                    
                    if lanc_cx:
                        supabase.table("financeiro").insert({"data": dt_str, "descricao": f"Compra ({f_sel}): {p_sel}", "tipo": "Saída", "categoria": "Compra de Mercadoria / Estoque", "valor": float(total_p)}).execute()
                        
                    st.success("Pedido de compra registrado com sucesso!")
                    st.rerun()
        else:
            st.info("Cadastre um fornecedor primeiro.")

    with sub_f_ger:
        st.write("### 🏢 Editar / Excluir Fornecedores")
        if not df_fornecedores.empty and 'nome_empresa' in df_fornecedores.columns:
            forn_sel_ed = st.selectbox("Selecione o fornecedor:", df_fornecedores['nome_empresa'].tolist(), key="ed_forn_sel")
            f_item = df_fornecedores[df_fornecedores['nome_empresa'] == forn_sel_ed].iloc[0]
            
            with st.form("form_edit_forn"):
                ef_nome = st.text_input("Empresa", value=str(f_item['nome_empresa']))
                ef_cnpj = st.text_input("CNPJ", value=str(f_item['cnpj']) if f_item['cnpj'] else "")
                ef_cont = st.text_input("Representante", value=str(f_item['contato']) if f_item['contato'] else "")
                ef_tel = st.text_input("Telefone", value=str(f_item['telefone']) if f_item['telefone'] else "")
                ef_email = st.text_input("E-mail", value=str(f_item['email']) if f_item['email'] else "")
                ef_obs = st.text_area("Observações", value=str(f_item['observacoes']) if f_item['observacoes'] else "")
                
                col_fb1, col_fb2 = st.columns(2)
                if col_fb1.form_submit_button("💾 Salvar Fornecedor"):
                    supabase.table("fornecedores").update({
                        "nome_empresa": ef_nome, "cnpj": ef_cnpj, "contato": ef_cont, "telefone": ef_tel, "email": ef_email, "observacoes": ef_obs
                    }).eq("id", int(f_item['id'])).execute()
                    st.success("Fornecedor atualizado!")
                    st.rerun()
                    
                if col_fb2.form_submit_button("🗑️ Excluir Fornecedor"):
                    supabase.table("fornecedores").delete().eq("id", int(f_item['id'])).execute()
                    st.success("Fornecedor excluído!")
                    st.rerun()
        else:
            st.info("Nenhum fornecedor cadastrado.")
            
        st.markdown("---")
        st.write("### 📦 Histórico de Pedidos de Compra (Exclusão)")
        if not df_pedidos_compra.empty:
            st.dataframe(df_pedidos_compra.style.format({'preco_custo_unitario': 'R$ {:.2f}', 'valor_total': 'R$ {:.2f}'}), hide_index=True)
            lista_ids_ped = [str(x) for x in df_pedidos_compra['id'].tolist()]
            id_ped_del_str = st.selectbox("Selecione o ID do pedido para excluir:", lista_ids_ped, key="del_ped")
            if st.button("Excluir Pedido de Compra"):
                supabase.table("pedidos_compra").delete().eq("id", int(id_ped_del_str)).execute()
                st.success("Pedido excluído!")
                st.rerun()
        else:
            st.info("Nenhum pedido de compra registrado.")

# ==========================================
# 8. ETIQUETAS
# ==========================================
with tab_etiquetas:
    st.subheader("🏷️ Emissão de Etiquetas e Código de Barras")
    if not df_estoque.empty and 'Produto' in df_estoque.columns:
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            prod_etq = st.selectbox("Selecione o Produto", df_estoque['Produto'].tolist())
            qtd_etiquetas = st.number_input("Quantidade de Etiquetas", min_value=1, max_value=100, value=10)
        
        item_etq = df_estoque[df_estoque['Produto'] == prod_etq].iloc[0]
        preco_etq = item_etq['Valor Unitário']
        cod_id = str(item_etq['id']).zfill(6)
        
        st.markdown("---")
        cols_preview = st.columns(3)
        for i in range(min(3, qtd_etiquetas)):
            with cols_preview[i]:
                st.markdown(f"""
                <div style="border: 2px dashed #333; padding: 15px; border-radius: 5px; text-align: center; background-color: #fff; color: #000;">
                    <h4 style="margin:0; font-size: 16px;">{prod_etq}</h4>
                    <p style="font-size: 12px; margin: 5px 0;">Cód: 789000{cod_id}</p>
                    <h3 style="margin:0; color: #2e7d32;">R$ {preco_etq:.2f}</h3>
                    <p style="font-size: 20px; font-family: monospace; letter-spacing: 2px; margin: 5px 0;">||| | |||| || |</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Cadastre produtos primeiro.")

# ==========================================
# 9. CURVA ABC
# ==========================================
with tab_curva_abc:
    st.subheader("📊 Inteligência de Vendas & Relatório Curva ABC")
    if not df_vendas.empty and 'Produto' in df_vendas.columns and 'Valor Total' in df_vendas.columns:
        curva_df = df_vendas.groupby('Produto').agg(
            Quantidade_Vendida=('Quantidade', 'sum'),
            Faturamento_Total=('Valor Total', 'sum'),
            Lucro_Total=('Lucro', 'sum')
        ).reset_index().sort_values(by='Faturamento_Total', ascending=False)
        
        faturamento_geral = curva_df['Faturamento_Total'].sum()
        if faturamento_geral > 0:
            curva_df['Participacao_%'] = (curva_df['Faturamento_Total'] / faturamento_geral) * 100
            curva_df['Acumulado_%'] = curva_df['Participacao_%'].cumsum()
            
            def classificar_abc(acum):
                if acum <= 80: return 'A (Até 80%)'
                elif acum <= 95: return 'B (80% - 95%)'
                else: return 'C (95% - 100%)'
                    
            curva_df['Curva ABC'] = curva_df['Acumulado_%'].apply(classificar_abc)
            st.dataframe(curva_df.style.format({'Faturamento_Total': 'R$ {:.2f}', 'Lucro_Total': 'R$ {:.2f}', 'Participacao_%': '{:.2f}%'}), hide_index=True)
        else:
            st.info("Faturamento zerado.")
    else:
        st.info("Registre vendas para ver a Curva ABC.")

# ==========================================
# 10. CAIXA & SANGRIA
# ==========================================
with tab_caixa:
    st.subheader("💵 Fechamento de Caixa Diário, Sangria e Quebra")
    sub_cx_lanc, sub_cx_ger = st.tabs(["➕ Operações de Caixa", "📋 Histórico e Exclusão"])
    
    with sub_cx_lanc:
        with st.form("form_operacao_caixa"):
            c1, c2 = st.columns(2)
            with c1:
                tipo_op = st.selectbox("Tipo de Operação", ["Abertura de Caixa", "Sangria (Retirada de Dinheiro)", "Fechamento de Caixa com Apuração"])
                resp = st.text_input("Operador / Responsável", value="Caixa Principal")
            with c2:
                vlr_op = st.number_input("Valor Envolvido (R$)", min_value=0.0, step=0.01)
                data_op = st.date_input("Data da Operação", value=datetime.now())
                
            obs_op = st.text_area("Observações")
            if st.form_submit_button("Registrar Operação de Caixa"):
                dt_str = f"{data_op} {datetime.now().strftime('%H:%M:%S')}"
                db_tipo = "Abertura" if "Abertura" in tipo_op else ("Sangria" if "Sangria" in tipo_op else "Fechamento")
                supabase.table("fechamento_caixa").insert({"data": dt_str, "tipo_registro": db_tipo, "valor": float(vlr_op), "responsavel": resp, "observacao": obs_op}).execute()
                if db_tipo == "Sangria":
                    supabase.table("financeiro").insert({"data": dt_str, "descricao": f"Sangria ({resp}): {obs_op}", "tipo": "Saída", "categoria": "Despesas Operacionais", "valor": float(vlr_op)}).execute()
                st.success("Operação registrada!")
                st.rerun()

    with sub_cx_ger:
        if not df_caixa.empty:
            st.dataframe(df_caixa.style.format({'valor': 'R$ {:.2f}'}), hide_index=True)
            lista_ids_cx = [str(x) for x in df_caixa['id'].tolist()]
            cx_del_str = st.selectbox("ID do registro de caixa para excluir:", lista_ids_cx, key="del_cx_reg")
            if st.button("Excluir Registro de Caixa"):
                supabase.table("fechamento_caixa").delete().eq("id", int(cx_del_str)).execute()
                st.success("Excluído com sucesso!")
                st.rerun()
        else:
            st.info("Nenhuma operação registrada.")

# ==========================================
# 11. DASHBOARD GERAL
# ==========================================
with tab_dashboard:
    st.subheader("📈 Dashboard Geral do Sistema")
    if not df_financeiro.empty and 'Tipo' in df_financeiro.columns:
        ent = df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor'].sum()
        sai = df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor'].sum() if 'df_financeiro' in locals() else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas Totais", f"R$ {ent:.2f}")
        c2.metric("Saídas Totais", f"R$ {sai:.2f}")
        c3.metric("Saldo Líquido", f"R$ {ent - sai:.2f}")
    else:
        st.info("Sem dados para o dashboard.")

# ==========================================
# 12. RELATÓRIO PDF INTEGRADO
# ==========================================
with tab_relatorio:
    st.subheader("📄 Relatório Geral em PDF (Integrado ao Supabase)")
    st.write(
        "Gere um relatório completo com **todas as informações do sistema** "
        "(Estoque, Vendas, Financeiro, Clientes, Fornecedores, Pedidos de Compra e Caixa) "
        "extraídas diretamente do banco de dados Supabase."
    )

    st.info(
        "📊 O relatório inclui:\n"
        "- **Valor de Custo Total por produto** (Quantidade × Preço de Custo)\n"
        "- **Valor de Venda Total por produto** (Quantidade × Valor Unitário)\n"
        "- **Linha de Totais Gerais** ao final da tabela de estoque (inventário total, "
        "capital investido em custo e potencial de venda)"
    )

    st.markdown("---")

    col_r1, col_r2 = st.columns([1, 1])
    with col_r1:
        gerar = st.button("🔄 Gerar Relatório PDF", type="primary", use_container_width=True)

    if gerar:
        with st.spinner("Gerando relatório e conectando ao Supabase..."):
            try:
                # Recarrega dados atualizados do Supabase antes de gerar o PDF
                df_estoque = carregar_dados_tabela("estoque")
                df_vendas = carregar_dados_tabela("vendas")
                df_financeiro = carregar_dados_tabela("financeiro")
                df_fornecedores = carregar_dados_tabela("fornecedores")
                df_pedidos_compra = carregar_dados_tabela("pedidos_compra")
                df_clientes = carregar_dados_tabela("clientes")
                df_caixa = carregar_dados_tabela("fechamento_caixa")

                # Normalização mínima necessária para o PDF não quebrar
                if df_estoque.empty:
                    df_estoque = pd.DataFrame(columns=['id', 'Produto', 'Categoria', 'Quantidade',
                                                       'Preço de Custo', 'Valor Unitário'])
                else:
                    col_map_est = {}
                    for col in df_estoque.columns:
                        c_lower = col.lower().strip()
                        if c_lower in ['produto', 'nome']: col_map_est[col] = 'Produto'
                        elif c_lower in ['categoria']: col_map_est[col] = 'Categoria'
                        elif c_lower in ['quantidade', 'qtd']: col_map_est[col] = 'Quantidade'
                        elif c_lower in ['valor_unitario', 'valorunitario', 'preco', 'valor']: col_map_est[col] = 'Valor Unitário'
                        elif c_lower in ['preco_custo', 'precocusto', 'custo']: col_map_est[col] = 'Preço de Custo'
                    df_estoque = df_estoque.rename(columns=col_map_est)
                    if 'Preço de Custo' not in df_estoque.columns: df_estoque['Preço de Custo'] = 0.00
                    if 'Valor Unitário' not in df_estoque.columns: df_estoque['Valor Unitário'] = 0.00
                    if 'Categoria' not in df_estoque.columns: df_estoque['Categoria'] = 'Geral'

                if df_vendas.empty:
                    df_vendas = pd.DataFrame(columns=['id', 'Data', 'Produto', 'Quantidade',
                                                      'Valor Total', 'Lucro'])
                else:
                    col_map_vendas = {}
                    for col in df_vendas.columns:
                        c_lower = col.lower().strip()
                        if c_lower == 'data': col_map_vendas[col] = 'Data'
                        elif c_lower == 'produto': col_map_vendas[col] = 'Produto'
                        elif c_lower == 'quantidade': col_map_vendas[col] = 'Quantidade'
                        elif c_lower in ['valor_total', 'valortotal']: col_map_vendas[col] = 'Valor Total'
                        elif c_lower == 'lucro': col_map_vendas[col] = 'Lucro'
                    df_vendas = df_vendas.rename(columns=col_map_vendas)

                if df_financeiro.empty:
                    df_financeiro = pd.DataFrame(columns=['id', 'Data', 'Tipo', 'Categoria',
                                                          'Descrição', 'Valor'])
                else:
                    col_map_fin = {}
                    for col in df_financeiro.columns:
                        c_lower = col.lower().strip()
                        if c_lower == 'data': col_map_fin[col] = 'Data'
                        elif c_lower in ['descricao', 'descrição']: col_map_fin[col] = 'Descrição'
                        elif c_lower == 'tipo': col_map_fin[col] = 'Tipo'
                        elif c_lower == 'categoria': col_map_fin[col] = 'Categoria'
                        elif c_lower == 'valor': col_map_fin[col] = 'Valor'
                    df_financeiro = df_financeiro.rename(columns=col_map_fin)

                if df_pedidos_compra.empty:
                    df_pedidos_compra = pd.DataFrame(columns=['id', 'data', 'fornecedor', 'produto',
                                                              'quantidade', 'preco_custo_unitario',
                                                              'valor_total', 'status'])

                pdf_bytes = gerar_relatorio_pdf()

                st.success("✅ Relatório gerado com sucesso! Clique no botão abaixo para baixar.")
                st.download_button(
                    label="⬇️ Baixar Relatório PDF",
                    data=pdf_bytes,
                    file_name=f"relatorio_erp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            except Exception as e:
                st.error(f"❌ Erro ao gerar o relatório PDF: {e}")
                st.exception(e)

    st.markdown("---")
    st.markdown("### 📋 Pré-visualização dos Totais")
    if not df_estoque.empty and 'Quantidade' in df_estoque.columns:
        q = pd.to_numeric(df_estoque['Quantidade'], errors='coerce').fillna(0)
        pc = pd.to_numeric(df_estoque.get('Preço de Custo', 0), errors='coerce').fillna(0)
        pv = pd.to_numeric(df_estoque.get('Valor Unitário', 0), errors='coerce').fillna(0)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 Itens em Estoque", f"{int(q.sum())} un")
        c2.metric("💰 Capital Investido (Custo)", f"R$ {(q * pc).sum():.2f}")
        c3.metric("🏷 Potencial de Venda", f"R$ {(q * pv).sum():.2f}")
        c4.metric("📈 Lucro Potencial", f"R$ {(q * pv).sum() - (q * pc).sum():.2f}")
    else:
        st.info("Sem produtos em estoque para pré-visualizar totais.")
