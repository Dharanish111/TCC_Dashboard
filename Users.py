import streamlit as st
from appwrite.client import Client
from appwrite.services.users import Users
import pandas as pd
import plotly.express as px
from appwrite.query import Query
import concurrent.futures
import time

st.set_page_config(
    page_title="TCC_Dashboard",
    page_icon="https://raw.githubusercontent.com/Dharanish111/TCC_Dashboard/main/Pics/1.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the Appwrite client
client = Client().set_endpoint(st.secrets["end_point"])\
                 .set_project(st.secrets["project_id"])\
                 .set_key(st.secrets["api_key"])

# Initialize the users service
users_service = Users(client)

@st.cache_data(ttl=1000)
def fetch_users():
    users = []
    limit = 2000
    last_user_id = None

    while True:
        try:
            queries = [Query.limit(limit)]
            if last_user_id:
                queries.append(Query.cursor_after(last_user_id))
            
            response = users_service.list(queries=queries)
            batch_users = response['users']
            users.extend(batch_users)
            
            if len(batch_users) < limit:
                break

            last_user_id = batch_users[-1]['$id']

        except Exception as e:
            st.error(f"Error fetching user data: {e}")
            break

    return users

# Fetch user data
users_data = fetch_users()

# Convert user data to DataFrame
df = pd.DataFrame(users_data)

# Check if 'registration' field exists and convert it to datetime
if 'registration' in df.columns:
    df['registration'] = pd.to_datetime(df['registration'])
else:
    st.error("The 'registration' field is missing from the data.")
    st.stop()

# Display total number of users
total_users = len(df)
st.sidebar.write(f"Total Users: {total_users}")

col1,col2,col3 =st.columns([3,1,3])
with col2:
    st.image("https://raw.githubusercontent.com/Dharanish111/TCC_Dashboard/main/Pics/1.png",width = 195)

st.title("Users 👤")

with st.expander("See Total Data"):
    st.dataframe(df)

# Select columns for download
st.sidebar.header("Download Data")
selected_columns = st.multiselect("Select Columns to Download", options=df.columns.tolist(), default=None)
if selected_columns:
    filtered_df = df[selected_columns]
    csv = filtered_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='filtered_data.csv',
        mime='text/csv',
    )

if not df.empty:
    fig = px.histogram(df, x='registration', title='User Registrations per Day')
    st.plotly_chart(fig)
else:
    st.write("No data available for the selected filters.")

# Filters
st.sidebar.header('Filters')
phone_number = st.sidebar.text_input('Phone Number')
email = st.sidebar.text_input('Email')
date_range = st.sidebar.date_input('Date Range', [])

# Apply filters if any are provided
if phone_number or email or (len(date_range) == 2):
    filtered_df = df.copy()

    if phone_number:
        filtered_df = filtered_df[filtered_df['phone'] == phone_number]
        st.dataframe(filtered_df)

    if email:
        filtered_df = filtered_df[filtered_df['email'] == email]
        st.dataframe(filtered_df)

    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['registration'].dt.date >= start_date) &
            (filtered_df['registration'].dt.date <= end_date)
        ]

    if not filtered_df.empty:
        st.subheader(f'Filtered User Data from {start_date} to {end_date}')
        st.dataframe(filtered_df)

        fig = px.histogram(filtered_df, x='registration', title='User Registrations per Day')
        st.plotly_chart(fig)
    filter_total_users = len(filtered_df)
    st.sidebar.write(f"Total Users after using filter: {filter_total_users}")
    else:
        st.write("No data available for the selected filters.")
else:
    st.write("No filters applied. Please use the sidebar to filter data.")
