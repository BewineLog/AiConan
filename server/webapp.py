import datetime
import io
import pandas as pd
import streamlit as st
import requests
import altair as alt
import json
from streamlit_echarts import st_echarts
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode

api = "127.0.0.1"
url = f'http://{api}:8000'

class LoginPage:
    def __init__(self):
        self.userId = None
        self.password = None

    def render(self):
        st.title('Admin Login')
        self.userId = st.text_input('userId', key="login-userid")
        self.password = st.text_input('password', type="password", key='login-password')
        
        if st.button('Login'):
            response = requests.post(url + "/authenticate", data={'userId': self.userId, 'password': self.password})
            
            if response.status_code == 200 and 'token' in response.json():
                st.success('Login successful')
                st.session_state.token = response.json()['token']
                return True
            else:
                st.error('Invalid user ID or password.')
        return False

def fetch_data():
    response = requests.get(url + '/api/data')
    if response.status_code == 200:
        data = json.loads(response.text)
        data = pd.DataFrame(data)
        return data
    return None

def create_chart(data):
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X("attack_types_id:N", axis=alt.Axis(title="Attack Type")),
        y=alt.Y("count():Q", axis=alt.Axis(title="Count")),
    ).properties(width=700, height=400)
    return chart

def admin_content():
     # Fetch user data
    headers = {'Authorization': 'Bearer ' + st.session_state.token}
    response = requests.get(url + '/users', headers=headers)
    if response.status_code != 200:
        st.error('Failed to fetch user data.')
        return
    
    user_data = response.json()
    
    # Display section buttons for each user
    st.sidebar.title('User Sections')
    selected_user = st.sidebar.radio('Select User', ['Full user data'] + [user['username'] for user in user_data])
    
    # Fetch data based on user selection
    if selected_user == 'Full user data':
        with st.spinner('Loading data...'):
            data = fetch_data()  # Fetch data for all users
    else:
        # Fetch data for the selected user
        user_id = next((user['id'] for user in user_data if user['username'] == selected_user), None)
        if user_id is None:
            st.error(f"User '{selected_user}' not found.")
            return
        
        response = requests.get(url + f'/data/{user_id}', headers=headers)
        if response.status_code != 200:
            st.error('Error fetching data.')
            return

        data = pd.DataFrame(response.json())
    
        # Display data table
        if data is not None:
            st.success('Data fetched successfully!')
        else:
            st.error('No data available.')
                
    # Display table
    st.subheader("Packet Table")
    st.text("")
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
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=False,
    )
    
    # Display Chart
    st.subheader("Packet Chart")
    st.text("")
    chart = create_chart(data)
    st.altair_chart(chart, use_container_width=True)
    
    st.success("Data processed successfully!")

def admin_page():
    st.title("AIConan Service Admin Page")

    if st.button('Logout'):
        headers = {'Authorization': 'Bearer ' + st.session_state.token}
        response = requests.get(url + '/logout', headers=headers)
        if response.status_code == 200:
            st.session_state.token = None
            st.success('Logout successful. Please login again.')
            st.experimental_rerun()
        else:
            st.error('Logout failed')

    if 'token' in st.session_state and st.session_state.token is not None:
        admin_content()

def user_page():
    st.title("AI Conan Service")
    c29, c30, c31 = st.columns([1, 6, 1])
    
    with c30:
        uploaded_file = st.file_uploader(
            "",
            key="1",
            help="Upload .csv file",
        )
        input_user_name = st.text_input(label="Enter User Name", value="default")
        user_input = {"username" : input_user_name}
 
        if uploaded_file is not None:
            # Check inserted .csv file
            file_container = st.expander("Check your uploaded .csv")
            shows = pd.read_csv(uploaded_file)
            uploaded_file.seek(0)
            
            # Drop the 'Unnamed: 0' column if it exists
            if 'Unnamed: 0' in shows.columns:
                shows.drop('Unnamed: 0', axis=1, inplace=True)
            
            file_container.write(shows)

        if st.button("Start Detection"):
            with st.spinner('Loading data...'):
                if uploaded_file is not None:
                    # Send POST request to Flask API with CSV file
                    files = {'file': uploaded_file.getvalue()}
                    response = requests.post(url + "/api/detection", files=files, data=user_input)
                    
                    # Check response status
                    if response.status_code == 200:
                        response_json = json.loads(response.text)
                        number_of_attack = response_json.split(' ')[1][:-1]
                        print(">> ", number_of_attack)
                        number_of_attack = int(number_of_attack)
                        if number_of_attack > 0:
                            st.warning(f"{number_of_attack} Attack Detected!")
                        else:
                            st.success("💡 Detection Finished!")
                    else:
                        st.error("Error uploading CSV file.")
            
        
        else:
            st.info(
                f"""
                    👆 Upload a .csv file first. Sample to try: [biostats.csv](https://people.sc.fsu.edu/~jburkardt/data/csv/biostats.csv)
                    """
            )
            
            st.stop()

def show_page(page):
    if page == "User Page":
        user_page()
    elif page == "Admin Page":
        if 'token' not in st.session_state or st.session_state.token is None:
            if not LoginPage().render():
                return
        admin_page()

# Set the app page configuration
st.set_page_config(page_title="AIConan Detecting Service", page_icon="favicon.ico")

# Create a sidebar to switch between pages
selected_page = st.sidebar.selectbox("Select a page", ("User Page", "Admin Page"))

# Run the app
if __name__ == "__main__":
    show_page(selected_page)
