import time
import streamlit as st
import pandas as pd
import numpy as np
import requests
from bokeh.plotting import figure
import neurokit2 as nk
import heartpy as hp

st.set_page_config(
    page_title="Real-Time ECG readings Dashboard",
    page_icon="✅",
    layout="wide",
)
st.title('Real-Time ECG readings from AD8232 sensor on ESP32 board')

DATE_COLUMN = 'date_created'
DATA_URL = ("https://smartcare-main-production.up.railway.app/sensors/1/last4096")
DATA_URL_ANN = "https://smartcare-main-production.up.railway.app/annotations"
SAMPLING_RATE = 100

# @st.cache_data
def load_data(nrows):
    json_data = requests.get(DATA_URL).json()
    annot_data = requests.get(DATA_URL_ANN).json()
    data = pd.DataFrame(json_data)
    return data.tail(nrows), annot_data

placeholder = st.empty()

while True:
    data, annot_data = load_data(4096)
    sd = [float(each) for each in data["reading_value"]]
    sdf = np.array(sd).flatten()

    # st.write(pd.DataFrame([float(each) for each in data["reading_value"]]))
    # signals, info = nk.ecg_process(
    #     pd.Series(
    #         [float(each) for each in data["reading_value"]]
    #     ),
    #     sampling_rate=SAMPLING_RATE
    # )
    # st.write(info)

    # df, info = nk.ecg_process(sd, sampling_rate=SAMPLING_RATE)
    # st.write(info)
    # analyze_epochs = nk.ecg_analyze({"0": df}, sampling_rate=100)
    # st.write(analyze_epochs)

    working_data, measures = hp.process(sdf, SAMPLING_RATE, report_time=True)
    # anr = nk.ecg_analyze(data["reading_value"], sampling_rate=SAMPLING_RATE)
    # st.write(anr)

    with placeholder.container():
        y = data["reading_value"]
        x = list(range(y.size))

        p = figure(title="ECG Readings", x_axis_label="S", y_axis_label="R")
        p.line(x, y, legend_label="Trend", line_width=2)

        st.write('breathing rate is: %s Hz' %measures['breathingrate'])
        st.write('heart rate is: %s BPM' %measures['bpm'])
        st.write('last_annotations: ')
        st.write(annot_data)
        st.bokeh_chart(p, use_container_width=True)

    time.sleep(10)
    