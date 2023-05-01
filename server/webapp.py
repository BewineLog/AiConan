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

def admin_page():
    st.title("AIConan service Admin Page")
    st.subheader("Packet Table 👇")
    st.text("")
    
    if st.button("Trigger Alarm"):
        response = requests.get(API_URL)
        
        if response.status_code == 200:
            # Display table
            data = pd.read_csv(io.StringIO(response.text))
            
            from st_aggrid import GridUpdateMode, DataReturnMode
            
            gb = GridOptionsBuilder.from_dataframe(data)
            gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
            gb.configure_selection(selection_mode="multiple", use_checkbox=True)
            gb.configure_side_bar()
            gridOptions = gb.build()
            response = AgGrid(
                data,
                gridOptions=gridOptions,
                enable_enterprise_modules=True,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                data_return_mode=DataReturnMode.ALL,
                fit_columns_on_grid_load=False,
            )
            df = pd.DataFrame(response["selected_rows"])
            st.table(df)
            st.text("")
            
            st.subheader("Packet Graph 👇")
            st.text("")
            chart = create_chart(data)
            st.altair_chart(chart, use_container_width=True)
            
            st.success("CSV file processed successfully!")
            
        else:
            st.error("Error fetching data from Flask API.")

    
 
def streamlit_main():
    
    st.title("AI Conan Service")
    
    c29, c30, c31 = st.columns([1, 6, 1])
    
    with c30:
        uploaded_file = st.file_uploader(
            "",
            key="1",
            help="Upload .csv file",
        )
        
        input_user_name = st.text_input(label="User Name", value="default")
         
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
                    st.success(f"""💡 Detection Finished!""")
                      
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
        

# Define a function to show the selected page
def show_page(page):
    if page == "User Page":
        streamlit_main()
    elif page == "Admin Page":
        admin_page()

# Set the app page configuration
st.set_page_config(page_icon="✂️", page_title="AIConan Detecting Service")

# Create a sidebar to switch between pages
selected_page = st.sidebar.selectbox("Select a page", ("User Page", "Admin Page"))
show_page(selected_page)