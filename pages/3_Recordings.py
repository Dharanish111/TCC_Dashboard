import streamlit as st
import pandas as pd
from appwrite.client import Client
from appwrite.services.databases import Databases
from datetime import datetime
from appwrite.query import Query

# Initialize Appwrite client
client = Client()
client.set_endpoint(st.secrets["end_point"])  # Replace with your Appwrite endpoint
client.set_project(st.secrets["project_id"])  # Replace with your Appwrite project ID
client.set_key(st.secrets["api_key"])  # Replace with your Appwrite API key

# Initialize Databases service
databases = Databases(client)

# Fetch data from Appwrite database with pagination
@st.cache_data(ttl=1000)
def fetch_data_from_appwrite():
    documents = []
    limit = 2000  # Number of documents per page
    last_document_id = None

    while True:
        queries = [Query.limit(limit)]
        if last_document_id:
            queries.append(Query.cursor_after(last_document_id))
        
        response = databases.list_documents(
            database_id=st.secrets["database_id"],  # Replace with your database ID
            collection_id=st.secrets["collection_id"],  # Replace with your collection ID
            queries=queries
        )
        batch_documents = response['documents']
        documents.extend(batch_documents)

        if len(batch_documents) < limit:
            break
        
        last_document_id = batch_documents[-1]['$id']  # Track the last document ID for pagination

    return documents

# Fetch data
data = fetch_data_from_appwrite()

# Convert the fetched data to a DataFrame
df = pd.DataFrame(data)


total_recordings = len(data)
st.sidebar.write(f"Total recordings: {total_recordings}")

# Convert the '$createdAt' field to datetime
if '$createdAt' in df.columns:
    df['$createdAt'] = pd.to_datetime(df['$createdAt'])
else:
    st.error("The '$createdAt' field is missing from the data.")
    st.stop()



col1,col2,col3 = st.columns([3,1,3])
with col2:
    image_1 = st.image("https://raw.githubusercontent.com/Dharanish111/TCC_Dashboard/main/1.png")
    


st.header("Total Recordings ⏺️")
st.dataframe(df)

# Sidebar filters
st.sidebar.header("Filters")
phone_number = st.sidebar.text_input("Search by Phone Number")
email = st.sidebar.text_input("Search by Email")
date_range = st.sidebar.date_input('Date Range', [])

# Start with a copy of the original DataFrame
filtered_df = df.copy()

# Apply filters based on user input
if phone_number:
    filtered_df = filtered_df[filtered_df['phone_number'].str.contains(phone_number, na=False)]

if email:
    filtered_df = filtered_df[filtered_df['email'].str.contains(email, case=False, na=False)]

if len(date_range) == 2:  # Ensure two dates are selected
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['$createdAt'].dt.date >= start_date) &
        (filtered_df['$createdAt'].dt.date <= end_date)
    ]


    # Display the filtered data
    st.subheader(f"Filtered Data from {start_date} to {end_date}")
    st.dataframe(filtered_df)