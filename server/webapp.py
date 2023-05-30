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
    # Define a dictionary mapping attack type IDs to their corresponding labels
    attack_type_labels = {
        1: 'Normal',
        2: 'DoS',
        3: 'Fuzzy',
        4: 'Spoofing'
    }

    # Convert the attack types column to a string type
    data['attack_types_id'] = data['attack_types_id'].astype(str)

    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X("attack_types_id:N", axis=alt.Axis(title="Attack Type", 
                                                   tickCount=len(attack_type_labels),
                                                   labelExpr="datum.value === '1' ? 'Normal' : datum.value === '2' ? 'DoS' : datum.value === '3' ? 'Fuzzy' : 'Spoofing'",
                                                   labelAngle=0)),
        y=alt.Y("count():Q", axis=alt.Axis(title="Count")),
    ).properties(width=700, height=400)

    return chart
    
def create_line_chart(data):
    # Define a dictionary mapping attack type IDs to their corresponding labels
    attack_type_labels = {
        '1': 'Normal',
        '2': 'DoS',
        '3': 'Fuzzy',
        '4': 'Spoofing'
    }

    # Convert the attack types column to a string type
    data['attack_types_id'] = data['attack_types_id'].astype(str)

    # Replace the attack type IDs with their corresponding labels
    data['attack_types_id'] = data['attack_types_id'].map(attack_type_labels)
    
    # Drop rows with missing timestamps
    data = data.dropna(subset=['timestamp', 'attack_types_id'])
    
    # Convert the timestamp column to a datetime object
    # Make sure to use the correct unit for your timestamp
    # data['timestamp'] = pd.to_datetime(data['timestamp'], format='%H:%M:%S.%f')
    
    
    # Group by timestamp and attack type, count the number of messages (rows)
    # current_date = datetime.date.today()
    print(data['timestamp'].head(10))
    current_date = pd.to_datetime('today').normalize()  # Get the current date (with time set to 00:00:00)
    data['timestamp'] = pd.to_datetime(data['timestamp'], format='%H:%M:%S.%f').dt.floor('S')
    data['timestamp'] = data['timestamp'].dt.time
    data['timestamp'] = data['timestamp'].apply(lambda x: pd.Timestamp.combine(current_date, x))
    print('>>:::',data['timestamp'].head(10))
    # microsecond_range = pd.interval_range(start=data['timestamp'].min(), end=data['timestamp'].max(), freq='1U')
    data = data.groupby([pd.Grouper(key='timestamp', freq='1S'), 'attack_types_id']).size().reset_index(name='count')
    print(data['timestamp'].head(10))
    # Check if all timestamps are unique or not
    print("Number of unique timestamps:", data['timestamp'].nunique())
    print("Number of total rows:", len(data))

    # Check the type of min_timestamp and max_timestamp
    min_timestamp = data['timestamp'].min()
    max_timestamp = data['timestamp'].max()
    print("Type of min_timestamp:", type(min_timestamp))
    print("Type of max_timestamp:", type(max_timestamp))
    # unique_timestamps = data['timestamp'].drop_duplicates().tolist()

    # Print the min and max timestamps here
    print('Min:', min_timestamp)
    print('Max:', max_timestamp)
    
    uniq_timestamp = data['timestamp'].unique()
    formatted_timestamp = [datetime.datetime.strptime(str(ts)[:-4], "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d %H:%M:%S")
                        for ts in uniq_timestamp]
    print(formatted_timestamp)
    if pd.isnull(min_timestamp) or pd.isnull(max_timestamp):
        print('Invalid timestamp range detected. Cannot create the chart.')
        return None

    max_count = data['count'].max()
    y_scale = alt.Scale(domain=(0, max_count + 300))
    print('>>>',max_count)
    # alt.data_transformers.disable_max_rows()
    chart = alt.Chart(data).mark_line().encode(
        # x=alt.X('timestamp:T', scale=alt.Scale(domain=(min_timestamp,max_timestamp)), title='Timestamp'),
        # y=alt.Y('count:Q', scale=y_scale, title='Count'),
        x=alt.X('timestamp:T',  title='Timestamp'),
        y=alt.Y('count:Q',  title='Count'),
        color=alt.Color('attack_types_id:N', legend=alt.Legend(title="Attack Type")),
        tooltip=['timestamp:T','attack_types_id:N', 'count:Q']
    ).properties(width=700, height=400)
    
    # st.altair_chart(chart, use_container_width=True)

    # 데이터 표시
    # st.write(data['count'])
    return chart


def admin_content():
     # Fetch user data
    headers = {'Authorization': 'Bearer ' + st.session_state.token}
    response = requests.get(url + '/users', headers=headers)
    if response.status_code != 200:
        st.error('Failed to fetch user data.')
        return
    
    user_data = response.json()
    print(user_data)
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
        
        with st.spinner('Loading data...'):
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
    
    
    print('>>> ',data['timestamp'])         
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
    
    print('>>>?? ',data['timestamp']) 
    line_chart = create_line_chart(data)
    if line_chart is not None:
        st.altair_chart(line_chart, use_container_width=True)
    else:
        st.write("Unable to create the chart due to invalid timestamp range.")
        
    # st.subheader("Packet Counts Over Time")
    # st.text("")
    # line_chart = create_line_chart(data)
    # st.altair_chart(line_chart, use_container_width=True)
    
    
    st.success("Data processed successfully!")

def admin_page():
    st.title("AIConan Service Admin Page")
    if 'token' not in st.session_state or st.session_state.token is None:
        st.experimental_rerun()

    if st.button('Logout'):
        headers = {'Authorization': 'Bearer ' + st.session_state.token}
        response = requests.get(url + '/logout', headers=headers)
        if response.status_code == 200:
            st.session_state.token = None
            st.success('Logout successful. Please login again.')
            st.experimental_rerun()
        else:
            st.error('Logout failed')

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
        print(">>> input_username : ", user_input, "type : ", type(input_user_name))
        
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
                    👆 Upload a .csv file first. Sample to try: [testDataset.csv](https://demoblog-bucket-uiwlov.s3.ap-northeast-2.amazonaws.com/test_dataset.csv)
                    """
            )
    
            st.stop()

def show_page(page):
    if page == "User Page":
        user_page()
    elif page == "Admin Page":
        if 'token' not in st.session_state or st.session_state.token is None:
            LoginPage().render()
        else:
            admin_page()

# Set the app page configuration
st.set_page_config(page_title="AIConan Detecting Service", page_icon="favicon.ico")

# Create a sidebar to switch between pages
selected_page = st.sidebar.selectbox("Select a page", ("User Page", "Admin Page"))

# Run the app
if __name__ == "__main__":
    show_page(selected_page)