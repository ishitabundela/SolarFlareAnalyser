import streamlit as st 
import requests
import os
import base64
from datetime import datetime, timedelta, timezone
import pandas as pd
import plotly.express as px



def get_solar_flare_data(start_date, end_date):
    # Format dates for API call
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Make API call
    url = f"https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/FLR?startDate={start_date_str}&endDate={end_date_str}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API call failed with status code {response.status_code}")

def process_data(data):
    # Extract relevant information
    processed_data = []
    for flare in data:
        processed_data.append({
            'flrID': flare['flrID'],
            'beginTime': flare['beginTime'],
            'peakTime': flare['peakTime'],
            'endTime': flare['endTime'],
            'classType': flare['classType'],
            'sourceLocation': flare['sourceLocation'],
            'activeRegionNum': flare['activeRegionNum'],
            'linkedEvents': len(flare.get('linkedEvents', []) or []),
            'instruments': len(flare.get('instruments', []) or [])
        })
    
    return pd.DataFrame(processed_data)

def main():
    # Set page config for a dark theme
    st.set_page_config(page_title="Solar Flare Explorer", page_icon="☀️", layout="wide")

    # Custom CSS for dark theme and styling
    st.markdown("""
    <style>
    .stApp {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    .stTitle, .stSubheader, h1, h2, h3, h4, h5, h6 {
        color: #FFD700 !important;
    }
    .stTitle {
        font-size: 3rem !important;
    }
    .stButton>button {
        background-color: #4B0082;
        color: white;
        border-radius: 10px;
    }
    .stDateInput>div>div>input {
        color: white !important;
    }
    /* Make all text white for better readability */
    p, span, div, label, .stTextInput>div>div>input, .stSelectbox, .stMultiSelect, .stSlider, .stTable, .stMarkdown, .stTab {
        color: white !important;
    }
    /* Ensure plotly chart titles and labels are white */
    .js-plotly-plot .plotly .gtitle, .js-plotly-plot .plotly .xtitle, .js-plotly-plot .plotly .ytitle, .js-plotly-plot .plotly .legendtext {
        color: white !important;
    }
    /* Make tab labels white */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: white !important;
    }
    /* Ensure date input text is visible */
    input[type="date"] {
        color-scheme: dark;
    }
    /* Add rounded corners to various elements */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stMultiSelect>div>div>div, .element-container, .stDateInput>div>div>input {
        border-radius: 10px !important;
    }
    .stPlotlyChart {
        border-radius: 10px;
        overflow: hidden;
    }
    .stTabs [data-baseweb="tab-list"] {
        border-radius: 10px 10px 0 0;
    }
    .stTabs [data-baseweb="tab-panel"] {
        border-radius: 0 0 10px 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Title with emoji
    st.markdown("# ☀️ Solar Flare Explorer")
    
    # Date input in a single row
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now(timezone.utc).date() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now(timezone.utc).date())

    if start_date <= end_date:
        if st.button("Analyze Solar Flares"):
            with st.spinner("Fetching and processing data..."):
                # Fetch data
                data = get_solar_flare_data(start_date, end_date)
                
                # Process data
                df = process_data(data)
                
                # Display total flares count
                st.markdown(f"## Total Flares: {len(df)}")
                
                # Add tabs for different sections
                tabs = st.tabs(["Pie Chart", "Flare Timeline", "Advanced Analysis"])
                
                with tabs[0]:
                    st.markdown("This section provides an overview of the solar flare data and the distribution of their class types.")
                    # Class Type Distribution
                    st.subheader("Distribution of Flare Class Types")
                    class_counts = df['classType'].value_counts()
                    fig1 = px.pie(values=class_counts.values, names=class_counts.index, title='Distribution of Flare Class Types')
                    st.plotly_chart(fig1, use_container_width=True)

                with tabs[1]:
                    # Flares Over Time
                    st.subheader("Number of Flares Over Time")
                    df['beginTime'] = pd.to_datetime(df['beginTime'])
                    daily_counts = df.set_index('beginTime').resample('D')['flrID'].count().reset_index()
                    fig2 = px.line(daily_counts, x='beginTime', y='flrID', title='Number of Flares Over Time')
                    fig2.update_xaxes(title='Date')
                    fig2.update_yaxes(title='Number of Flares')
                    st.plotly_chart(fig2, use_container_width=True)

                with tabs[2]:
                    # Flare Intensity Over Time
                    st.subheader("Solar Flare Intensity Over Time")
                    df['intensity'] = df['classType'].apply(lambda x: ord(x[0]) - 65)  # Convert A-X to 0-23
                    
                    fig3 = px.scatter(df, x='beginTime', y='intensity', color='intensity',
                                      color_continuous_scale='YlOrRd', 
                                      title='Solar Flare Intensity Over Time',
                                      labels={'beginTime': 'Date', 'intensity': 'Flare Class'},
                                      hover_data=['classType'])
                    
                    fig3.update_traces(marker=dict(size=10))
                    fig3.update_yaxes(tickvals=list(range(0, 24, 5)), ticktext=['A', 'B', 'C', 'M', 'X'])
                    fig3.update_layout(yaxis_range=[-1, 24])
                    
                    st.plotly_chart(fig3, use_container_width=True)

    else:
        st.error("Error: End date must be after start date.")

    # Footer
    st.markdown("---")
    st.markdown(" | Data source: NASA DONKI API - Real-time data from the Space Weather Database Of Notifications, Knowledge, Information (DONKI) by Auth. NASA data Sources - HRS")

# def get_base64(bin_file):
#     with open(bin_file, 'rb') as f:
#         data = f.read()
#     return base64.b64encode(data).decode()

# def set_background(png_file):
#     bin_str = get_base64(png_file)
#     page_bg_img = '''
#     <style>
#     .stApp {
#     background-image: url("data:image/png;base64,%s");
#     background-size: cover;
#     background-repeat: no-repeat;
#     background-position: center center;
#     }
#     </style>
#     ''' % bin_str
#     st.markdown(page_bg_img, unsafe_allow_html=True)

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# set_background(f"{BASE_DIR}/img/bg.jpeg")

if __name__ == "__main__":
    main()
