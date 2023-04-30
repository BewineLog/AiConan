import datetime

import pandas as pd
import streamlit as st
import requests
import altair as alt

###################################
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

###################################

# 모델 API endpoint
api = "127.0.0.1"
url = f'http://{api}:8000'
predict_endpoint = '/'
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
    
@st.experimental_memo
def get_data():
    source = data.stocks()
    source = source[source.date.gt("2004-01-01")]
    return source
    
@st.experimental_memo(ttl=60 * 60 * 24)
def get_chart(data):
    hover = alt.selection_single(
        fields=["date"],
        nearest=True,
        on="mouseover",
        empty="none",
    )

    lines = (
        alt.Chart(data, height=500, title="Test Car Detection Graph")
        .mark_line()
        .encode(
            x=alt.X("date", title="Date"),
            y=alt.Y("packets", title="Packets"),
            color="symbol",
        )
    )

    # Draw points on the line, and highlight based on selection
    points = lines.transform_filter(hover).mark_circle(size=65)

    # Draw a rule at the location of the selection
    tooltips = (
        alt.Chart(data)
        .mark_rule()
        .encode(
            x="yearmonthdate(date)",
            y="packets",
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip("date", title="Date"),
                alt.Tooltip("packets", title="Packets"),
            ],
        )
        .add_selection(hover)
    )

    return (lines + points + tooltips).interactive()


def streamlit_main():
    
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
            help="Upload CSV file",
        )
    
        if uploaded_file is not None:
            file_container = st.expander("Check your uploaded .csv")
            shows = pd.read_csv(uploaded_file)
            uploaded_file.seek(0)
            file_container.write(shows)
            
            # Send POST request to Flask API with CSV file
            files = {'file': uploaded_file.getvalue()}
            response = requests.post("http://your-flask-api-url.com/detection", files=files)
            
            # Check response status
            if response.status_code == 200:
                st.success("CSV file uploaded successfully!")
            else:
                st.error("Error uploading CSV file.")
    
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
        results = requests.post(url + predict_endpoint)
        con.write(results)
    
    gb = GridOptionsBuilder.from_dataframe(shows)
    # enables pivoting on all columns,
    # however i'd need to change ag grid to allow export of pivoted/grouped data, however it select/filters groups
    gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_side_bar()  # side_bar is clearly a typo :) should by sidebar
    gridOptions = gb.build()
    
    
    # Define the CSS style for the alarm modal
    css = """
    div[data-testid="stAlert"] > div {
        background-color: red !important;
        color: white !important;
        text-align: center !important;
        font-weight: bold !important;
        font-size: 24px !important;
        border-radius: 10px !important;
        box-shadow: 0 0 10px rgba(0,0,0,0.5) !important;
    }
    """

    # Add a button to trigger the alarm modal
    if st.button("Trigger Alarm"):
        # Show the alarm modal
        st.warning("DoS Attack Detected!")
    
    
    st.success(f"""💡 Detection Finished!""")
    
    st.subheader("Packet Table 👇")
    st.text("")
    
    from st_aggrid import GridUpdateMode, DataReturnMode
     
    response = AgGrid(
        shows,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=False,
    )
    
    df = pd.DataFrame(response["selected_rows"])
    st.table(df)
    st.text("")
    
    st.subheader("Packet Graph 👇")
    st.text("")
    
    source = get_data()
    chart = get_chart(source)
    

if __name__ == '__main__':
    streamlit_main()
