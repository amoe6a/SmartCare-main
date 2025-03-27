import time
import streamlit as st
import pandas as pd
import numpy as np
import requests
from bokeh.plotting import figure
import neurokit2 as nk
import heartpy as hp
import ecg_plot

st.set_page_config(
    page_title="Real-Time ECG readings Dashboard",
    page_icon="✅",
    layout="wide",
)
st.title('Real-Time ECG readings from AD8232 sensor on ESP32 board')

DATE_COLUMN = 'date_created'
DATA_URL = "https://smartcare-main-production.up.railway.app/sensors/1/last4096"
DATA_PROCESSED_URL = "https://smartcare-main-production.up.railway.app/sensors/1/processed/last4096/"
DATA_URL_ANN = "https://smartcare-main-production.up.railway.app/annotations"
SAMPLING_RATE = 400

# @st.cache_data
def load_data(nrows):
    json_data = requests.get(DATA_URL).json()
    json_data_processed = requests.get(DATA_PROCESSED_URL).json()
    annot_data = requests.get(DATA_URL_ANN).json()
    data = pd.DataFrame(json_data)
    data_processed = pd.DataFrame(json_data_processed)
    return data.tail(nrows), data_processed.tail(nrows), annot_data

placeholder = st.empty()

while True:
    data, data_processed, annot_data = load_data(4096)
    sd = [float(each) for each in data["reading_value"]]
    sd_processed = [float(each) for each in data_processed["reading_value"]]
    sdf = np.array(sd).flatten()
    sdf_processed = np.array(sd_processed).flatten()

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
    working_data_processed, measures_processed = hp.process(sdf_processed, SAMPLING_RATE, report_time=True)
    # anr = nk.ecg_analyze(data["reading_value"], sampling_rate=SAMPLING_RATE)
    # st.write(anr)

    with placeholder.container():
        y = data_processed["reading_value"]
        x = list(range(y.size))

        p = figure(title="ECG Readings", x_axis_label="S", y_axis_label="R")
        p.line(x, y, legend_label="Trend", line_width=2)

        st.write('breathing rate is: %s Hz' %measures_processed['breathingrate'])
        st.write('heart rate is: %s BPM' %measures_processed['bpm'])
        st.write('last_annotations: ')
        st.write(annot_data)
        st.bokeh_chart(p, use_container_width=True)
        ecg_plot.plot(working_data, sample_rate=SAMPLING_RATE,
                  lead_index=["DI"], style='bw')

    time.sleep(10000)
    