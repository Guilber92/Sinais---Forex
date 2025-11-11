import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf

# Função para calcular CCI
def calcular_cci(df, n=14):
    TP = (df['High'] + df['Low'] + df['Close']) / 3
    MA = TP.rolling(n).mean()
    MD = TP.rolling(n).apply(lambda x: np.fabs(x - x.mean()).mean())
    CCI = (TP - MA) / (0.015 * MD)
    df['CCI'] = CCI
    df['CCI_buy'] = ((df['CCI'] > -100) & (df['CCI'].shift(1) <= -100)).astype(int)
    df['CCI_sell'] = ((df['CCI'] < 100) & (df['CCI'].shift(1) >= 100)).astype(int)
    return df

# Função para calcular MACD
def calcular_macd(df, preco_col='Close'):
    df['EMA12'] = df[preco_col].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df[preco_col].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_buy'] = ((df['MACD'] > df['Signal']) & (df['MACD'].shift(1) <= df['Signal'].shift(1))).astype(int)
    df['MACD_sell'] = ((df['MACD'] < df['Signal']) & (df['MACD'].shift(1) >= df['Signal'].shift(1))).astype(int)
    return df

# Carregar dados reais via yfinance
def carregar_dados_reais(ticker, periodo='1mo', intervalo='1d'):
    df = yf.download(ticker, period=periodo, interval=intervalo)
    df = df.dropna()
    df.index = df.index.tz_localize(None)  # Remover fuso horário para evitar KeyError
    return df

st.title("Análise Forex Real com MACD e CCI")

# Exemplo de ativos Forex no Yahoo Finance
ativo_selecionado = st.selectbox("Selecione o ativo:", ['USDEUR=X', 'GBPUSD=X', 'USDJPY=X'])
periodo = st.selectbox("Período de dados:", ['1mo', '3mo', '6mo', '1y'])
intervalo = st.selectbox("Intervalo de dados:", ['1d', '1h', '4h'])

df = carregar_dados_reais(ativo_selecionado, periodo=periodo, intervalo=intervalo)

# Calcular indicadores
df = calcular_cci(df)
df = calcular_macd(df)

# Definir sinais para plotagem
compra = df.index[(df['CCI_buy'] == 1) | (df['MACD_buy'] == 1)]
venda = df.index[(df['CCI_sell'] == 1) | (df['MACD_sell'] == 1)]

# Gráfico preço com sinais
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Preço'))

fig.add_trace(go.Scatter(x=compra, y=df.loc[compra, 'Close'],
                         mode='markers+text', text=['BUY']*len(compra),
                         marker=dict(color='green', symbol='triangle-up', size=12),
                         textposition='top center', name='Compra'))

fig.add_trace(go.Scatter(x=venda, y=df.loc[venda, 'Close'],
                         mode='markers+text', text=['SELL']*len(venda),
                         marker=dict(color='red', symbol='triangle-down', size=12),
                         textposition='bottom center', name='Venda'))

fig.update_layout(title=f'Preço e Sinais MACD/CCI - {ativo_selecionado}', xaxis_title='Data', yaxis_title='Preço')
st.plotly_chart(fig)

# Gráfico MACD
fig_macd = go.Figure()
fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], mode='lines', name='MACD', line=dict(color='orange')))
fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], mode='lines', name='Signal', line=dict(color='purple')))

fig_macd.add_trace(go.Scatter(x=compra, y=df.loc[compra, 'MACD'], mode='markers',
                              marker=dict(color='green', symbol='triangle-up', size=12), name='MACD Compra'))
fig_macd.add_trace(go.Scatter(x=venda, y=df.loc[venda, 'MACD'], mode='markers',
                              marker=dict(color='red', symbol='triangle-down', size=12), name='MACD Venda'))

fig_macd.update_layout(title='MACD', xaxis_title='Data', yaxis_title='MACD')
st.plotly_chart(fig_macd)
