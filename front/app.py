import time
import streamlit as st
import pandas as pd
import numpy as np
import requests
from bokeh.plotting import figure

st.set_page_config(
    page_title="Real-Time ECG readings Dashboard",
    page_icon="✅",
    layout="wide",
)
st.title('Real-Time ECG readings from AD8232 sensor on ESP32 board')

DATE_COLUMN = 'date_created'
DATA_URL = ("https://smartcare-main-production.up.railway.app/sensors/1")

# @st.cache_data
def load_data(nrows):
    json_data = requests.get(DATA_URL).json()
    data = pd.DataFrame(json_data)
    return data.tail(nrows)

placeholder = st.empty()

while True:
    data = load_data(100)
    with placeholder.container():
        y = data["reading_value"]
        x = list(range(y.size))

        p = figure(title="ECG Readings", x_axis_label="S", y_axis_label="R")
        p.line(x, y, legend_label="Trend", line_width=2)

        st.bokeh_chart(p, use_container_width=True)

    time.sleep(10000)