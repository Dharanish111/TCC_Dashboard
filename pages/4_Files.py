import streamlit as st
from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.services.storage import Storage
import pandas as pd
import plotly.express as px
from appwrite.query import Query

# Initialize the Appwrite client
client = Client().set_endpoint(st.secrets["end_point"])\
                 .set_project(st.secrets["project_id"])\
                 .set_key(st.secrets["api_key"])

# Initialize the services
users_service = Users(client)
storage_service = Storage(client)

def fetch_data(service, list_func, resource_name, queries=None):
    data = []
    limit = 2000
    last_id = None

    while True:
        try:
            query_list = [Query.limit(limit)]
            if last_id:
                query_list.append(Query.cursor_after(last_id))
            if queries:
                query_list.extend(queries)

            response = list_func(*([queries] if resource_name == "users" else [bucket_id, query_list]))
            batch_data = response[resource_name]
            data.extend(batch_data)
            
            if len(batch_data) < limit:
                break

            last_id = batch_data[-1]['$id']

        except Exception as e:
            st.error(f"Error fetching {resource_name}: {e}")
            break

    return data

# Fetch users and recordings data
users_data = fetch_data(users_service, users_service.list, 'users')
bucket_id = st.secrets["bucket_id"]
recordings_data = fetch_data(storage_service, storage_service.list_files, 'files')

# Convert data to DataFrame
users_df = pd.DataFrame(users_data)
recordings_df = pd.DataFrame(recordings_data)

# Ensure datetime conversion
users_df['registration'] = pd.to_datetime(users_df['registration'], errors='coerce')
recordings_df['$updatedAt'] = pd.to_datetime(recordings_df.get('$updatedAt'), errors='coerce')
recordings_df['$createdAt'] = pd.to_datetime(recordings_df.get('$createdAt'), errors='coerce')

# Calculate the total size of all recordings in GB
total_size_bytes = recordings_df['sizeOriginal'].sum()
total_size_gb = total_size_bytes / (1024 ** 3)

# Separate video and audio files based on mimeType
video_files = recordings_df[recordings_df['name'].str.endswith('.mp4')]
audio_files = recordings_df[recordings_df['name'].str.endswith('.aac')]

# Calculate the total size for video and audio files in GB
total_video_size_gb = video_files['sizeOriginal'].sum() / (1024 ** 3)
total_audio_size_gb = audio_files['sizeOriginal'].sum() / (1024 ** 3)

# Display the total sizes
st.sidebar.write(f"Total files: {len(recordings_data)}")
st.sidebar.write(f"Total data size: {total_size_gb:.2f} GB")

option = st.sidebar.selectbox("select type",["Audio","Video"])
if option == "Audio":
    st.sidebar.write(f"Total audio data size: {total_audio_size_gb:.2f} GB")

elif option == "Video":
    st.sidebar.write(f"Total video data size: {total_video_size_gb:.2f} GB")

# Sidebar interval selection
st.sidebar.header('Select Time Interval')
interval = st.sidebar.selectbox('Interval', ['Daily', 'Weekly', 'Monthly'])

interval_map = {
    'Daily': 'dt.date',
    'Weekly': 'dt.to_period("W").apply(lambda r: r.start_time)',
    'Monthly': 'dt.to_period("M").apply(lambda r: r.start_time)'
}

# Aggregate based on the selected interval
users_df['interval'] = eval(f"users_df['registration'].{interval_map[interval]}")
recordings_df['interval'] = eval(f"recordings_df['$updatedAt'].{interval_map[interval]}")

registrations_count = users_df.groupby('interval').size().reset_index(name='count')
uploads_count = recordings_df.groupby('interval').size().reset_index(name='count')


col1,col2,col3 = st.columns([3,1,3])
with col2:
    image_1 = st.image("https://raw.githubusercontent.com/Dharanish111/TCC_Dashboard/main/1.png")
    
st.title("Files 📂")
# Display results
with st.expander("Total Files"):
    st.dataframe(recordings_data)

# Select columns for download
st.sidebar.header("Download Data")
selected_columns = st.multiselect("Select Columns to Download", options=recordings_df.columns.tolist(), default=None)
if selected_columns:
    filtered_df = recordings_df[selected_columns]
    csv = filtered_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='filtered_data.csv',
        mime='text/csv',
    )

if not uploads_count.empty:
    st.subheader(f'Number of File Uploads ({interval})')
    st.plotly_chart(px.bar(uploads_count, x='interval', y='count', title=f'Number of File Uploads ({interval})'))
else:
    st.warning('No file uploads data available to display.')

st.subheader(f'File Uploads Data ({interval})')
st.dataframe(uploads_count)