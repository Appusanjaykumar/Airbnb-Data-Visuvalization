# Importing Libraries
import pandas as pd
import pymongo
import streamlit as st
import plotly.express as px
from streamlit_option_menu import option_menu
from PIL import Image

class AirbnbDataPreprocessing:
    @staticmethod
    def fetch_data(collection, projection):
        data = list(collection.find({}, projection))
        return pd.DataFrame(data)

    @staticmethod
    def amenities_sort(x):
        x.sort(reverse=False)
        return x

    @staticmethod
    def preprocess_data(df):
        # Your data preprocessing steps here
        # For example, handling null values and data type conversion
        df['bedrooms'].fillna(0, inplace=True)
        df['beds'].fillna(0, inplace=True)
        df['bathrooms'].fillna(0, inplace=True)
        df['cleaning_fee'].fillna('Not Specified', inplace=True)

        # Data type conversion
        df['minimum_nights'] = df['minimum_nights'].astype(int)
        df['maximum_nights'] = df['maximum_nights'].astype(int)
        df['bedrooms'] = df['bedrooms'].astype(int)
        df['beds'] = df['beds'].astype(int)
        df['bathrooms'] = df['bathrooms'].astype(str).astype(float)
        df['price'] = df['price'].astype(str).astype(float).astype(int)
        df['cleaning_fee'] = df['cleaning_fee'].apply(lambda x: int(float(str(x))) if x != 'Not Specified' else 'Not Specified')
        df['extra_people'] = df['extra_people'].astype(str).astype(float).astype(int)
        df['guests_included'] = df['guests_included'].astype(str).astype(int)
        df['country'] = df['address'].apply(lambda x: x.get('country', 'Unknown'))
        df['property_type'] = df['property_type'].astype(str).str.lower()

        return df

    @staticmethod
    def merge_dataframes():
        # MongoDB connection
        with pymongo.MongoClient("mongodb+srv://sanjaykumar:sanjay6336@cluster0.kqvktku.mongodb.net/?retryWrites=true&w=majority") as client:
            db = client["sample_airbnb"]
            col = db["listingsAndReviews"]

            # Fetch data directly into a DataFrame
            data = AirbnbDataPreprocessing.fetch_data(
                col, {'_id': 1, 'listing_url': 1, 'name': 1, 'property_type': 1, 'room_type': 1, 'bed_type': 1,
                    'minimum_nights': 1, 'maximum_nights': 1, 'cancellation_policy': 1, 'accommodates': 1,
                    'bedrooms': 1, 'beds': 1, 'number_of_reviews': 1, 'bathrooms': 1, 'price': 1,
                    'cleaning_fee': 1, 'extra_people': 1, 'guests_included': 1, 'address': 1, 'country': 1,
                    'images.picture_url': 1, 'review_scores.review_scores_rating': 1, 'availability': 1})

            # Attempt to create DataFrame
            df = pd.DataFrame(data)

            # Check if 'availability' is present in the DataFrame
            if 'availability' in df.columns and 'availability_365' in df['availability'].iloc[0].keys():
                # Print the structure of the 'availability' column
                print("Structure of the 'availability' column:", df['availability'].iloc[0])

                # Data preprocessing
                processed_data = AirbnbDataPreprocessing.preprocess_data(df)

                # Print the columns in the processed_data DataFrame
                print("Columns in the processed_data DataFrame:", processed_data.columns)

                return processed_data
            else:
                print("The column 'availability' is not present in the DataFrame.")
                return None




# Setting up page configuration
st.set_page_config(page_title="Airbnb Data Visualization | SANJAY KUMAR",
                   layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={'About': """# This dashboard app is created by *SANJAY KUMAR*!
                                        Data has been gathered from MongoDB Atlas"""})

# Example usage
processed_data = AirbnbDataPreprocessing.merge_dataframes()
print(processed_data.columns)

# Creating option menu in the side bar
with st.sidebar:
    selected = option_menu("Menu", ["Home", "Overview", "Explore"],
                           icons=["house", "graph-up-arrow", "bar-chart-line"],
                           menu_icon="menu-button-wide",
                           default_index=0,
                           styles={"nav-link": {"font-size": "20px", "text-align": "left", "margin": "-2px",
                                               "--hover-color": "#FF5A5F"},
                                   "nav-link-selected": {"background-color": "#FF5A5F"}}
                           )

# READING THE CLEANED DATAFRAME
df = processed_data.head()

# HOME PAGE
if selected == "Home":
    # Title Image
    col1, col2 = st.columns(2, gap='medium')
    col1.markdown("## :blue[Domain] : Travel Industry, Property Management and Tourism")
    col1.markdown("## :blue[Technologies used] : Python, Pandas, Plotly, Streamlit, MongoDB")
    col1.markdown(
        "## :blue[Overview] : To analyze Airbnb data using MongoDB Atlas, perform data cleaning and preparation, develop interactive visualizations, and create dynamic plots to gain insights into pricing variations, availability patterns, and location-based trends. ")
    col2.markdown("#   ")
    col2.markdown("#   ")

# OVERVIEW PAGE
if selected == "Overview":
    # RAW DATA
    if st.button("Click to view Dataframe"):
        st.write(df)

    # INSIGHTS

   # GETTING USER INPUTS
    country = st.sidebar.multiselect('Select a country', sorted(processed_data['country'].unique()),
                                 sorted(processed_data['country'].unique()))

    prop = st.sidebar.multiselect('Select Property_type', sorted(processed_data['property_type'].unique()),
                              sorted(processed_data['property_type'].unique()))

    room = st.sidebar.multiselect('Select Room_type', sorted(processed_data['room_type'].unique()),
                              sorted(processed_data['room_type'].unique()))

    price = st.slider('Select Price', processed_data['price'].min(), processed_data['price'].max(),
                  (processed_data['price'].min(), processed_data['price'].max()))



    # CONVERTING THE USER INPUT INTO QUERY
    query = f'country in {country} & room_type in {room} & property_type in {prop} & price >= {price[0]} & price <= {price[1]}'

    # CREATING COLUMNS
    col1, col2 = st.columns(2, gap='medium')

    with col1:
        # TOP 10 PROPERTY TYPES BAR CHART
        df1 = df.query(query).groupby(["property_type"]).size().reset_index(name="Listings").sort_values(
        by='Listings', ascending=False)[:10]
        fig = px.bar(df1,
             title='Top 10 Property Types',
             x='Listings',  # This should be the name of the column you want on the x-axis
             y='property_type',  # This should be the name of the column you want on the y-axis
             orientation='h',
             color='property_type',
             color_continuous_scale=px.colors.sequential.Agsunset)
        st.plotly_chart(fig, use_container_width=True)

        # TOP 10 HOSTS BAR CHART
        df2 = df.query(query)
        if 'host' in df2.columns:
            df2 = df2.groupby(df2['host'].apply(lambda x: x.get('host_name', 'Unknown'))).size().reset_index(name="Listings").sort_values(
                by='Listings', ascending=False)[:10]
        else:
            df2 = pd.DataFrame(columns=['host_name', 'Listings'])

        fig = px.bar(df2,
                     title='Top 10 Hosts with Highest number of Listings',
                     x='Listings',
                     y='host_name',  # Updated to lowercase 'host_name'
                     orientation='h',
                     color='host_name',  # Updated to lowercase 'host_name'
                     color_continuous_scale=px.colors.sequential.Agsunset)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # TOTAL LISTINGS IN EACH ROOM TYPES PIE CHART
        df1 = df.query(query).groupby(["room_type"]).size().reset_index(name="counts")
        fig = px.pie(df1,
                     title='Total Listings in each Room_types',
                     names='room_type',
                     values='counts',
                     color_discrete_sequence=px.colors.sequential.Rainbow
                     )
        fig.update_traces(textposition='outside', textinfo='value+label')
        st.plotly_chart(fig, use_container_width=True)

        # TOTAL LISTINGS BY COUNTRY CHOROPLETH MAP
        country_df = df.query(query).groupby(['country'], as_index=False)['name'].count().rename(
            columns={'name': 'Total_Listings'})
        fig = px.choropleth(country_df,
                            title='Total Listings in each Country',
                            locations='country',
                            locationmode='country names',
                            color='Total_Listings',
                            color_continuous_scale=px.colors.sequential.Plasma
                            )
        st.plotly_chart(fig, use_container_width=True)

# EXPLORE PAGE
# EXPLORE PAGE
if selected == "Explore":
    st.markdown("## Explore more about the Airbnb data")

    # GETTING USER INPUTS
    country = st.sidebar.multiselect('Select a Country', sorted(processed_data['country'].unique()),
                                     sorted(processed_data['country'].unique()))
    prop = st.sidebar.multiselect('Select Property_type', sorted(processed_data['property_type'].unique()),
                              sorted(processed_data['property_type'].unique()))
    room = st.sidebar.multiselect('Select Room_type', sorted(processed_data['room_type'].unique()),
                              sorted(processed_data['room_type'].unique()))
    price = st.slider('Select Price', processed_data['price'].min(), processed_data['price'].max(),
                  (processed_data['price'].min(), processed_data['price'].max()))

    # CONVERTING THE USER INPUT INTO QUERY
    query = f'country in {country} & room_type in {room} & property_type in {prop} & price >= {price[0]} & price <= {price[1]}'

    # HEADING 1
    st.markdown("## Price Analysis")

    # CREATING COLUMNS
    col1, col2 = st.columns(2, gap='medium')

    with col1:
        # AVG PRICE BY ROOM TYPE BARCHART
        pr_df = processed_data.query(query).groupby('room_type', as_index=False)['price'].mean().sort_values(by='price')

        fig = px.bar(data_frame=pr_df,
             x='room_type',  # Use lowercase 'room_type'
             y='price',      # Use lowercase 'price'
             color='price',   # Use lowercase 'price'
             title='Avg Price in each Room type'
             )
        st.plotly_chart(fig, use_container_width=True)

    # HEADING 2
    st.markdown("## Availability Analysis")

    # AVAILABILITY BY ROOM TYPE BOX PLOT
    # Assuming your DataFrame structure is similar to this
    df_availability = processed_data.query(query)

    # Print column names
    st.write("Column Names:", df_availability.columns)

    # Print first few rows of the DataFrame
    st.write("DataFrame Head:", df_availability.head())

   # Check if 'availability' is present in the DataFrame
# Check if 'availability' is present in the DataFrame
# Check if 'availability' is present in the DataFrame
    if 'availability' in processed_data.columns and 'availability_365' in processed_data['availability'].iloc[0].keys():
        # Extract 'availability_365' from the nested structure
        processed_data['availability_365'] = processed_data['availability'].apply(lambda x: x.get('availability_365'))

        # Create a box plot
        fig = px.box(
            data_frame=processed_data,
            x='room_type',
            y='availability_365',
            color='room_type',
            title='Availability by Room_type'
        )

        # Show the plot
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("The column 'availability_365' is not present in the DataFrame.")





    with col2:
        # AVG PRICE IN COUNTRIES SCATTERGEO
        country_df = processed_data.query(query).groupby('country', as_index=False)['price'].mean()
        fig = px.scatter_geo(data_frame=country_df,
                            locations='country',
                            color='price',
                            hover_data=['price'],
                            locationmode='country names',
                            size='price',
                            title='Avg Price in each Country',
                            color_continuous_scale='agsunset'
                            )
        st.plotly_chart(fig, use_container_width=True)

        # AVG AVAILABILITY IN COUNTRIES SCATTERGEO
        country_df_availability = processed_data.query(query).groupby('country', as_index=False)['availability_365'].mean()
        country_df_availability.availability_365 = country_df_availability.availability_365.astype(int)
        fig = px.scatter_geo(data_frame=country_df_availability,
                            locations='country',
                            color='availability_365',
                            hover_data=['availability_365'],
                            locationmode='country names',
                            size='availability_365',
                            title='Avg Availability in each Country',
                            color_continuous_scale='agsunset'
                            )
        st.plotly_chart(fig, use_container_width=True)





