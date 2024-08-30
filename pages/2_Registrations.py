import streamlit as st
from appwrite.client import Client
from appwrite.services.users import Users
import pandas as pd
import plotly.express as px
from appwrite.query import Query

# Initialize the Appwrite client
client = Client()
client.set_endpoint(st.secrets["end_point"])  # Your Appwrite Endpoint
client.set_project(st.secrets["project_id"])            # Your project ID
client.set_key(st.secrets["api_key"])  # Your API Key

# Initialize the users service
users_service = Users(client)

@st.cache_data(ttl=1000)
def fetch_users():
    users = []
    limit = 2000  # Maximum number of users per request
    last_user_id = None  # Track the last user ID for pagination

    while True:
        try:
            # Build the query list to paginate through users
            queries = [Query.limit(limit)]
            if last_user_id:
                queries.append(Query.cursor_after(last_user_id))
            
            # Fetch the users
            response = users_service.list(queries=queries)
            batch_users = response['users']
            users.extend(batch_users)

            # Break the loop if fewer users than the limit were returned
            if len(batch_users) < limit:
                break

            # Update the last user ID for the next request
            last_user_id = batch_users[-1]['$id']

        except Exception as e:
            st.error(f"Error fetching user data: {e}")
            break

    return users

# Fetch all users from the database
users_data = fetch_users()

# Convert the users data to a DataFrame
users_df = pd.DataFrame(users_data)

total_registrations = len(users_df)
st.sidebar.write(f"Total Registrations: {total_registrations}")

# Ensure the 'registration' field is in datetime format
if 'registration' in users_df.columns:
    users_df['registration'] = pd.to_datetime(users_df['registration'])
else:
    st.error("The 'registration' field is missing from the data.")
    st.stop()

# Sidebar for selecting the time interval
st.sidebar.header('Select Time Interval')
interval = st.sidebar.selectbox('Interval', ['Daily', 'Weekly', 'Monthly'])

# Aggregate registrations based on the selected interval
if interval == 'Daily':
    users_df['interval'] = users_df['registration'].dt.date
elif interval == 'Weekly':
    users_df['interval'] = users_df['registration'].dt.to_period('W').apply(lambda r: r.start_time)
else:  # Monthly
    users_df['interval'] = users_df['registration'].dt.to_period('M').apply(lambda r: r.start_time)

registrations_count = users_df.groupby('interval').size().reset_index(name='count')

col1,col2,col3 = st.columns([3,1,3])
with col2:
    image_1 = st.image("https://raw.githubusercontent.com/Dharanish111/TCC_Dashboard/main/Pics/1.png")

# Display the data table
st.header(f'Registrations Data ✍🏾 ({interval})')
with st.expander("All Registrations"):
    st.dataframe(registrations_count)

# Plot the number of registrations
fig = px.bar(registrations_count, x='interval', y='count', title=f'Number of Registrations ({interval})')
st.plotly_chart(fig)
