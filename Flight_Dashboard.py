#!/usr/bin/env python
# coding: utf-8

# In[56]:


import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta

# MongoDB connection setup 
mongo_conn_string = 'mongodb+srv://adejumoabdulazeez:aade6850@cluster0.ogpfaff.mongodb.net/?retryWrites=true&w=majority'
client = MongoClient(mongo_conn_string)
db = client['flight_data_db']
flights_collection = db['flights']

# Fetch data from MongoDB and flatten the nested fields
flights_data = list(flights_collection.find())
df = pd.json_normalize(flights_data)
df['flight_date'] = pd.to_datetime(df['flight_date']).dt.date

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server

# Generate formatted date labels for dropdown
today = datetime.now().date()
yesterday = today - timedelta(days=1)
two_days_ago = today - timedelta(days=2)
date_options = [
    {'label': f'Today ({today.strftime("%B %d, %Y")})', 'value': 'Today'},
    {'label': f'Yesterday ({yesterday.strftime("%B %d, %Y")})', 'value': 'Yesterday'},
    {'label': f'2 Days Ago ({two_days_ago.strftime("%B %d, %Y")})', 'value': '2 Days Ago'}
]

# Function to filter data based on date selection
def filter_data(selected_date):
    if selected_date == 'Today':
        date_filter = today
    elif selected_date == 'Yesterday':
        date_filter = yesterday
    else:  # '2 Days Ago'
        date_filter = two_days_ago

    filtered_df = df[df['flight_date'] == date_filter]
    return filtered_df

# App layout
app.layout = html.Div([
    html.H1("Flight Data Dashboard"),
    
    # Dropdown for date selection
    html.Div([
        dcc.Dropdown(
            id='date-dropdown',
            options=date_options,
            value='Today',
            style={'width': '250px'}  # Adjust width as needed
        )
    ], style={'width': '300px', 'display': 'inline-block'}),  # Adjust wrapper width
    
    dcc.Graph(id='common-airports-graph'),
    dcc.Graph(id='flight-status-graph'),
    dcc.Graph(id='airline-market-share-graph')
])

# Callbacks for updating graphs based on dropdown selection
@app.callback(
    [
        Output('common-airports-graph', 'figure'),
        Output('flight-status-graph', 'figure'),
        Output('airline-market-share-graph', 'figure')
    ],
    [Input('date-dropdown', 'value')]
)
def update_graphs(selected_date):
    filtered_df = filter_data(selected_date)

    # Visualization 1: Most Common Departure and Arrival Airports
    common_airports = pd.concat([filtered_df['departure.airport'], filtered_df['arrival.airport']]).value_counts().reset_index().head(10)
    common_airports.columns = ['Airport', 'Count']
    fig1 = px.bar(common_airports, x='Airport', y='Count', title='Top 10 Departure and Arrival Airports')
    fig1.update_layout(width=700, height=500)
    fig1.update_yaxes(title='No of Flights')  # Updating Y-axis title

    # Visualization 2: Distribution of Flight Statuses
    flight_status_distribution = filtered_df['flight_status'].value_counts().reset_index()
    flight_status_distribution.columns = ['Status', 'Count']
    fig2 = px.pie(flight_status_distribution, names='Status', values='Count', title='Flight Status Distribution')

    # Adjusting pie chart layout for left alignment
    fig2.update_layout(
        margin=dict(l=0, r=20, t=50, b=20),  # Adjust margins to push plot to the left
        legend=dict(
            x=0.02,  # Slight adjustment to x position of the legend
            y=1,  # Position the legend at the top
            orientation="v"  # Horizontal orientation of legend items
        ),
        legend_title_text='Flight Status',
        autosize=False,  # Disable autosize to set specific size
        width=700,  # Width of the figure
        height=500  # Height of the figure
    )

    # Adjusting pie chart position within the figure
    fig2.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )


    # Visualization 3: Airline Market Share (Top 5 Airlines)
    airline_market_share = filtered_df['airline.name'].value_counts().reset_index().head(5)
    airline_market_share.columns = ['Airline', 'Flights']
    fig3 = px.bar(airline_market_share, x='Airline', y='Flights', title='Airline Market Share (Top 5 Airlines)')
    fig3.update_layout(width=700, height=500)
    fig3.update_yaxes(title='No of Flights')  # Updating Y-axis title

    return fig1, fig2, fig3

if __name__ == '__main__':
    app.run_server(debug=True)

