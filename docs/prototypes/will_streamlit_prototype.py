import streamlit as st
import plotly.express as px
from market_data import *
from monte_carlo import *

st.set_page_config(layout="wide")
st.title("Finance App")

page=st.sidebar.selectbox("Page",["Stock Lookup","Option Chain","Monte Carlo"])

if page=="Stock Lookup":
    t=st.text_input("Ticker","AAPL")
    if st.button("Lookup"):
        info=get_stock_info(t)
        st.json(info)
        h=get_price_history(t)
        fig=px.line(h,x="Date",y="Close")
        st.plotly_chart(fig,use_container_width=True)

elif page=="Option Chain":
    t=st.text_input("Ticker","AAPL")
    exps=get_option_expirations(t)
    if exps:
        e=st.selectbox("Expiration",exps)
        if st.button("Load Chain"):
            c,p=get_option_chain(t,e)
            st.write("Calls")
            st.dataframe(c)
            st.write("Puts")
            st.dataframe(p)

else:
    s0=st.number_input("Stock",100.0)
    k=st.number_input("Strike",100.0)
    r=st.number_input("Rate",0.05)
    sigma=st.number_input("Volatility",0.2)
    T=st.number_input("Years",1.0)
    typ=st.selectbox("Type",["call","put"])
    sims=st.slider("Simulations",10000,1000000,100000,10000)
    workers=st.slider("Workers",1,16,4)
    if st.button("Price"):
        price=monte_carlo_option_price_parallel(s0,k,r,sigma,T,typ,sims,workers)
        st.success(f"Option Price: ${price:.4f}")
