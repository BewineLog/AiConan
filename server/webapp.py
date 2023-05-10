import datetime
import io
import pandas as pd
import streamlit as st
import requests
import altair as alt
import json

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


# define login page interface
def login():
    st.title('Admin Login')
    userId = st.text_input('userId')
    password = st.text_input('password', type="password")
    
    if st.button('Login'):
        response = requests.post(url + "/authenticate", data={'userId': userId, 'password': password})
        
        if response.status_code == 200 and 'token' in response.json():
            st.success('Login successful')
            st.session_state.token = response.json()['token']
            admin_page()
        else:
            st.error('Invalid user ID or password.')


def admin_page():
    print(">> welcome to admin page")
    st.title("AIConan service Admin Page")
    st.subheader("Packet Table 👇")
    st.text("")
    
    # if st.button("Monitoring Graph"):
    #     response = requests.get(url + "/api/data")

    #     if response.status_code == 200:
    #         # Display table
    #         data = pd.read_csv(io.StringIO(response.text))
            
    #         from st_aggrid import GridUpdateMode, DataReturnMode
            
    #         gb = GridOptionsBuilder.from_dataframe(data)
    #         gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
    #         gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    #         gb.configure_side_bar()
    #         gridOptions = gb.build()
    #         response = AgGrid(
    #             data,
    #             gridOptions=gridOptions,
    #             enable_enterprise_modules=True,
    #             update_mode=GridUpdateMode.MODEL_CHANGED,
    #             data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    #             fit_columns_on_grid_load=False,
    #         )
            
    #         st.subheader("Packet Table 👇")
    #         st.text("")
    #         df = pd.DataFrame(response["selected_rows"])
    #         st.table(df)
    #         st.text("")
            
    #         st.subheader("Packet Graph 👇")
    #         st.text("")
    #         chart = create_chart(data)
    #         st.altair_chart(chart, use_container_width=True)
            
    #         st.success("CSV file processed successfully!")
            
    #     else:
    #         st.error("Error fetching data from Flask API.")


def user_page():
    
    st.title("AI Conan Service")
    
    c29, c30, c31 = st.columns([1, 6, 1])
    
    with c30:
        uploaded_file = st.file_uploader(
            "",
            key="1",
            help="Upload .csv file",
        )
        
        input_user_name = st.text_input(label="User Name", value="default")
        
        if uploaded_file is not None:
            # Check inserted .csv file
            file_container = st.expander("Check your uploaded .csv")
            shows = pd.read_csv(uploaded_file)
            uploaded_file.seek(0)
            file_container.write(shows)
        
        if st.button("Start Detection"):
            if uploaded_file is not None:
                # Send POST request to Flask API with CSV file
                files = {'file': uploaded_file.getvalue()}
                response = requests.post(url + "/api/detection", files=files)
            
                # Check response status
                if response.status_code == 200:
                    # Check response content for "DoS Attack Detected" message
                    
                    response_json = json.loads(response.text)
                    print(">> ", response_json)
                    number_of_attack = int(response_json[-2])

                    if number_of_attack > 0:
                         st.warning(number_of_attack + " Attack Detected!")
                    else:
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
        user_page()
    elif page == "Admin Page":
        if 'user_id' not in st.session_state:
          login()
    else:
        admin_page()

# Set the app page configuration
st.set_page_config( page_title="AIConan Detecting Service", page_icon="favicon.ico")


# Create a sidebar to switch between pages
selected_page = st.sidebar.selectbox("Select a page", ("User Page", "Admin Page"))
show_page(selected_page)