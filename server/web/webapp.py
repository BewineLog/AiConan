import datetime

import pandas as pd
import streamlit as st

# 모델 API endpoint
api = "127.0.0.1"
url = f'http://{api}:5000'
predict_endpoint = '/model/predict/'
shap_endpoint = '/model/calculate-shap-values/'


def _max_width_():
    max_width_str = f"max-width: 1800px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>    
    """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_icon="✂️", page_title="AIConan Detecting Service")

# 기타 변수 초기화
last_updated = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# st.image(
#     "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/apple/285/scissors_2702-fe0f.png",
#     width=100,
# )

st.title("AI Conan Service")

c29, c30, c31 = st.columns([1, 6, 1])

with c30:
    uploaded_file = st.file_uploader(
        "",
        key="1",
        help="To activate 'wide mode', go to the hamburger menu > Settings > turn on 'wide mode'",
    )

    if uploaded_file is not None:
        file_container = st.expander("Check your uploaded .csv")
        shows = pd.read_csv(uploaded_file)
        uploaded_file.seek(0)
        file_container.write(shows)

    else:
        st.info(
            f"""
                👆 Upload a .csv file first. Sample to try: [biostats.csv](https://people.sc.fsu.edu/~jburkardt/data/csv/biostats.csv)
                """
        )

        st.stop()
input_user_name = st.text_input(label="User Name", value="default value")

if st.button("Start Detection"):
    con = st.container()
    con.caption("Result")
    con.write(f"User Name : {str(input_user_name)}")
    con.write(f"date : {last_updated}")
