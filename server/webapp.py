import datetime
import io
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

# URL of Flask API
API_URL = f'http://{api}:8000'


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
    
@st.experimental_memo(ttl=60 * 60 * 24)
def create_chart(data):
    # Group data by attack type
    groups = data.groupby("attack_type_id")

    charts = []

    # Create a separate chart for each group
    for name, group in groups:
        chart = (
            alt.Chart(group, height=500, title=f"Attack Type {name}")
            .mark_line()
            .encode(
                x=alt.X("timestamp:T", title="Date"),
                y=alt.Y("count():Q", title="Packets"),
            )
            .interactive()
        )

        charts.append(chart)

    # Combine all charts into a single chart
    chart = alt.vconcat(*charts)

    return chart

  
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
        
        input_user_name = st.text_input(label="User Name", value="default value")
         
        if st.button("Start Detection"):
            if uploaded_file is not None:
                # Check inserted .csv file
                file_container = st.expander("Check your uploaded .csv")
                shows = pd.read_csv(uploaded_file)
                file_container.write(shows)
                
                # Send POST request to Flask API with CSV file
                files = {'file': uploaded_file.getvalue()}
                response = requests.post(API_URL, files=files)
            
                # Check response status
                if response.status_code == 200:
                    
                    ###################################
        
                    # 탐지 완료에 대한 통계
    
                    ###################################
            
                    st.success(f"""💡 Detection Finished!""")
                    
                    st.subheader("Packet Table 👇")
                    st.text("")
                    
                    from st_aggrid import GridUpdateMode, DataReturnMode
                
                    gb = GridOptionsBuilder.from_dataframe(shows)
                    # enables pivoting on all columns,
                    # however i'd need to change ag grid to allow export of pivoted/grouped data, however it select/filters groups
                    gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
                    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
                    gb.configure_side_bar()  # side_bar is clearly a typo :) should by sidebar
                    gridOptions = gb.build() 
                     
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
                    
                    # Parse the response as a DataFrame
                    data = pd.read_csv(io.StringIO(response.text))
        
                    # Generate and display the chart
                    st.subheader("Packet Graph 👇")
                    st.text("")
                    chart = create_chart(data)
                    st.altair_chart(chart, use_container_width=True)
        
                    st.success("CSV file uploaded and processed successfully!")
                      
                else:
                    st.error("Error uploading CSV file.")
    
        else:
            st.info(
                f"""
                    👆 Upload a .csv file first. Sample to try: [biostats.csv](https://people.sc.fsu.edu/~jburkardt/data/csv/biostats.csv)
                    """
            )
            
            st.stop()
         
         
            
        ###################################
    
        # 비정상 패킷 감지시 알람 기능

        ###################################
        
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
        
        ###################################
        
        # 통계자료 다운로드 가능하도록 구현
        # from functionforDownloadButtons import download_button
    
        ###################################
        # c29, c30, c31 = st.columns([1, 1, 2])
        # with c29:
        
        #     CSVButton = download_button(
        #         df,
        #         "File.csv",
        #         "Download to CSV",
        #     )
        
        # with c30:
        #     CSVButton = download_button(
        #         df,
        #         "File.csv",
        #         "Download to TXT",
        # )
    
    
if __name__ == '__main__':
    streamlit_main()
