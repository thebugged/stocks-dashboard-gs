import json
import random
import pandas as pd
import airbyte as ab
import streamlit as st
import plotly.graph_objects as go

from itertools import islice
from datetime import datetime
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Stocks", 
    page_icon="📊", 
    layout="wide")

st.html("styles.html")

@st.cache_data
def _read_service_account_secret():
    return json.loads(st.secrets["textkey"])

@st.cache_resource
def connect_to_gsheets():
    s_acc = _read_service_account_secret()
    gsheets_connection = ab.get_source(
        "source-google-sheets",
        config={
            "spreadsheet_id": "https://docs.google.com/spreadsheets/d/1YuxLNpNfAjBlteA75dyLHyzhKuTZGpMjsEhIt5ybRvc/edit?gid=0#gid=0",
            "credentials": {
                "auth_type": "Service",
                "service_account_info": json.dumps(s_acc)
            },
        },
    )
    gsheets_connection.select_all_streams()
    return gsheets_connection


@st.cache_data
def download_data(_gsheets_connection):
    airbyte_streams = _gsheets_connection.read()

    tickers_df = airbyte_streams["TICKERS"].to_pandas()
    history_dfs = {}

    for ticker in list(tickers_df["ticker_symbol"]):
        d = airbyte_streams[ticker].to_pandas()
        history_dfs[ticker] = d
   
    return tickers_df, history_dfs

@st.cache_data
def transform_data(tickers_df, history_dfs):
    tickers_df["last_trade_time"] = pd.to_datetime(
        tickers_df["last_trade_time"], dayfirst=True
    )

    for c in [
        "last_price",
        "previous_close",
        "open",
        "volume",
        "average_volume",
        "day_high",
        "day_low",
        "p_e_ratio_",
        "eps_",
        "market_cap",
        "change"

    ]:
        tickers_df[c] = pd.to_numeric(tickers_df[c], "coerce")

    for ticker in list(tickers_df["ticker_symbol"]):
        history_dfs[ticker]["date"] = pd.to_datetime(
            history_dfs[ticker]["date"], dayfirst=True
        )

        for c in ["open", "high", "low", "close", "volume"]:
            history_dfs[ticker][c] = pd.to_numeric(history_dfs[ticker][c])

    ticker_to_open = [list(history_dfs[t]["open"]) for t in list(tickers_df["ticker_symbol"])]
    tickers_df["open"] = ticker_to_open

    return tickers_df, history_dfs

def display_overview(tickers_df):
    show_overview = st.button("View More Data")

    if show_overview:
        def format_currency(val):
            return "$ {:,.2f}".format(val)
        
        def format_percentage(val):
            return "{:,.2f} %".format(val)
    
        def format_change(val):
            return "color: red;" if (val < 0) else "color: green;"
    
        def apply_odd_row_class(row):
            return [
                "background-color: #f8f8f8" if row.name % 2 != 0 
                else "" for _ in row]
    
        styled_df = (
                tickers_df.style.format(
                    {
                        "last_price": format_currency,
                        "change": format_percentage,
                        
                    }
                )
                .apply(apply_odd_row_class, axis=1)
                .applymap(format_change, subset=["change"])
            )
        
        st.dataframe(
            styled_df,
            column_order=[
                column
                for column in list(tickers_df.columns)
                if column not in [
                    "_airbyte_raw_id",
                    "_airbyte_extracted_at",
                    "_airbyte_meta",
                ]
            ],
            column_config={
                "open": st.column_config.AreaChartColumn(
                    "Last 12 Months",
                    width = "large",
                    help = "Open Price for the last 12 Months "
                )
            },
            hide_index =True,
           
        )
        
        hide_overview = st.button("Hide Data")
        if hide_overview:
            st.empty()


def plot_candlestick(history_df):
    f_candle = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.1,
    )

    f_candle.add_trace(
        go.Candlestick(
            x=history_df.index,
            open=history_df["open"],
            high=history_df["high"],
            low=history_df["low"],
            close=history_df["close"],
            name="Dollars",
        ),
        row=1,
        col=1,
    )

    f_candle.add_trace(
        go.Bar(
            x=history_df.index, 
            y=history_df["volume"], 
            name="Volume Traded"),
        row=2,
        col=1,
    )

    f_candle.update_layout(
        title="",
        showlegend=True,
        xaxis_rangeslider_visible=False,
        yaxis1=dict(title="OHLC"),
        yaxis2=dict(title="Volume"),
        hovermode="x",
    )

    f_candle.update_layout(
        # title_font_family="Open Sans",
        # title_font_color="#174C4F",
        title_font_size=15,
        # font_size=16,
        # margin=dict(l=80, r=80, t=100, b=80, pad=0),
        # height=500,
    )
    f_candle.update_xaxes(title_text="Date", row=2, col=1)
    f_candle.update_traces(selector=dict(name="Dollars"), showlegend=True)

    return f_candle

@st.experimental_fragment
def display_symbol_history(tickers_df, history_dfs):
    left_widget, right_widget, _  = st.columns([1,1,3])

    selected_ticker = left_widget.selectbox(
        "Choose Stock",
        list(history_dfs.keys()),
    )
    selected_period = right_widget.selectbox(
        "Time Period",
        ("1W", "1M", "90d", "1Y"),
        2,
    )

    history_df = history_dfs[selected_ticker]

    history_df["date"] = pd.to_datetime(history_df["date"], dayfirst=True) 
    history_df = history_df.set_index("date")
    mapping_period = {
        "1W": 7,
        "1M": 31,
        "90d": 90,
        "1Y": 365
    }
    today = datetime.today().date()
    delay_days = mapping_period[selected_period]
    history_df = history_df[
                            (today - pd.Timedelta(delay_days, unit="d")) : today
                            ]
    
    f_candle = plot_candlestick(history_df)
    
    l,c,r = st.columns(3)

    with l:
        st.html('<span class="low_indicator"></span>')
        st.metric(
            "Lowest Close Price",
            f'{history_df["close"].min():,} $',
        )
        st.metric(
            "Lowest Volume Day Trade",
            f'{history_df["volume"].min():,}'
        )
        

    with c:
        st.html('<span class="high_indicator"></span>')
        st.metric(
            "Highest Close Price",
            f'{history_df["close"].max():,}$',
        )
        st.metric(
            "Highest Volume Day Trade",
            f'{history_df["volume"].max():,}',
        )

    with r:
        st.html('<span class="bottom_indicator"></span>')
        with st.container():
            st.metric(
                "Current Market Cap",
                "{:,} $".format(
                    tickers_df[tickers_df["ticker_symbol"] == selected_ticker][
                        "market_cap"
                    ].values[0]
                ),
            )
            st.metric("Average Daily Volume", 
                    f'{int(history_df["volume"].mean()):,}'
                    )
    
    st.plotly_chart(f_candle, use_container_width = True)

def batched(iterable, n_cols):
    if n_cols < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n_cols)):
        yield batch

def plot_sparkline(data):
    fig_spark = go.Figure(
        data=go.Scatter(
            y=data,
            mode="lines",
            fill="tozeroy",
            line_color="red",
            fillcolor="pink",
        ),
    )
    fig_spark.update_traces(hovertemplate="Price: $ %{y:.2f}")
    fig_spark.update_xaxes(visible=False, fixedrange=True)
    fig_spark.update_yaxes(visible=False, fixedrange=True)
    fig_spark.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        height=50,
        margin=dict(t=10, l=0, b=0, r=0, pad=0),
    )
    return fig_spark

def display_watchlist_card(ticker_symbol, symbol_name, last_price, change, open):
    with st.container(border=True):
        st.html(f'<span class="watchlist_card"></span>')

        tl, tr = st.columns([2, 1])
        bl, br = st.columns([1, 1])

        with tl:
            st.html(f'<span class="watchlist_symbol_name"></span>')
            st.markdown(f"{symbol_name}")

        with tr:
            st.html(f'<span class="watchlist_ticker"></span>')
            st.markdown(f"{ticker_symbol}")
            negative_gradient = float(change) < 0
            st.markdown(
                f":{'red' if negative_gradient else 'green'}[{'▼' if negative_gradient else '▲'} {change} %]"
            )

        with bl:
            with st.container():
                st.html(f'<span class="watchlist_price_label"></span>')
                st.markdown(f"Current Value")

            with st.container():
                st.html(f'<span class="watchlist_price_value"></span>')
                st.markdown(f"$ {last_price:.2f}")

        with br:
            fig_spark = plot_sparkline(open)
            st.html(f'<span class="watchlist_br"></span>')
            st.plotly_chart(
                fig_spark, config=dict(displayModeBar=False), use_container_width=True
            )

def display_watchlist(tickers_df):
    n_cols = 4
    
    total_tickers = len(tickers_df)
    random_indices = random.sample(range(total_tickers), n_cols)
    
    # Slice the data using the randomly selected indices
    random_tickers = tickers_df.iloc[random_indices]

    for row in batched(random_tickers.itertuples(), n_cols):
        cols = st.columns(n_cols)
        for col, ticker in zip(cols, row):
            if ticker:
                with col:
                    display_watchlist_card(
                        ticker.ticker_symbol,
                        ticker.symbol_name,
                        ticker.last_price,
                        ticker.change,
                        ticker.open,
                    )



gsheets_connection = connect_to_gsheets()
tickers_df, history_dfs = download_data(gsheets_connection)
tickers_df, history_dfs = transform_data(tickers_df, history_dfs)

st.html("<h1 class ='title'> Stocks </h1>")
st.divider()

st.caption("**Watchlist**")
display_watchlist(tickers_df)


st.markdown("")
st.markdown("")
st.caption("**Stocks Insights**")



display_symbol_history(tickers_df, history_dfs)
display_overview(tickers_df)


disclaimer = """
---
**Disclaimer**: This dashboard is for informational purposes only. 
Please consult with a professional financial advisor before making any investment decisions. The creators of this dashboard are not responsible for any actions taken based on the information provided.
"""
st.caption(disclaimer)