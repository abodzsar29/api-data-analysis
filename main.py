# Information was retrieved from Samsara's databases by their API according to the documentation found here:
# https://developers.samsara.com/reference/overview
# https://developers.samsara.com/docs/telematics
# https://developers.samsara.com/reference/getvehiclestats

import requests
import json
import time
import pandas as pd
import matplotlib.pyplot as plt


class ConnectionTester:

    def __init__(self, token):
        self.token = token  # API Token has been removed for security reasons
        self.params = {'sensors': 'id'}
        self.headers = {'Authorization': 'Bearer ' + self.token}
        self.initial_connection()

    # Testing if current sensor data is reachable by printing out the most recent values for the Temperature,
    # Humidity and Door Status attributes, as well as printing out information about the sensor
    def initial_connection(self):
        for urlValue in ['temperature', 'humidity', 'door', 'list']:
            url = 'https://api.samsara.com/v1/sensors/' + urlValue
            response = requests.request('GET', url=url,
                                        headers=self.headers,
                                        params=self.params).json()
            print("-- Printing data for sensor: " + urlValue + "\n" + str(
                response))


class DataRetriever:

    def __init__(self):
        self.ct_object = ConnectionTester("SAMSARA_SENSOR_TOKEN")
        self.sensorHistoryUrl = 'https://api.samsara.com/v1/sensors/history'
        self.date_container = []
        self.temp_history_data = []
        self.humid_history_data = []
        self.door_status_list = []

    def date_converter(self, start, end, increment):
        self.date_container = []
        for x in range(start, end, increment):
            converted_time = time.strftime('%Y-%m-%d', time.localtime(x))
            self.date_container.append(converted_time)

    # Retrieving the temperature and humidity data for each day between 2022-06-26 00:00 and 2022-07-25 00:00
    def temp_humid_data(self):
        sensor_history_params = {
            'endMS': 1658793600000,
            'fillMissing': 'withNull',
            'series': [{'field': 'ambientTemperature',
                        'widgetId': 278018084739635}],
            'startMs': 1656198000000,
            'stepMS': 3600000
        }
        value_sum = 0  # For summing up the 24 values per day, so average can be calculated and appended to list
        for i in ['ambientTemperature', 'humidity']:
            sensor_history_params['series'][0][
                'field'] = i  # Changing the parameters for the API request to retrieve humidity and temperature data
            temp_history_response = requests.post(url=self.sensorHistoryUrl,
                                                  headers=self.ct_object.headers,
                                                  data=json.dumps(
                                                      sensor_history_params)).json()
            for y in range(1,
                           721):  # There are 720 values in the request for every hour of 30 days (30 * 24)
                if i == 'ambientTemperature':
                    value_sum += round(
                        (temp_history_response['results'][y]['series'][
                             0] / 1000),
                        1)  # Temperature data is retrieved in millicelcius therefore dividing by 1000 and rounding to 1 decimal place
                elif i == 'humidity':
                    value_sum += temp_history_response['results'][y]['series'][
                        0]
                if y % 24 == 0 and y != 0:  # Take the average of the 24 data values extracted for every day and append it to final data list
                    value_sum /= 24
                    if i == 'ambientTemperature':
                        self.temp_history_data.append(round(value_sum, 1))
                    elif i == 'humidity':
                        self.humid_history_data.append(round(value_sum, 1))
                    temp_sum = 0  # Zero the integer holding the sum of values when data for a new day gets extracted

    # Retrieving door status data between 2022-06-26 00:00 and 2022-07-02 00:00 per every hour
    def door_status_data(self):
        door_history_params = {
            'endMS': 1656802800000,
            'fillMissing': 'withNull',
            'series': [{'field': 'doorClosed',
                        'widgetId': 278018084465093}],
            'startMs': 1656198000000,
            'stepMS': 3600000
        }
        door_history_response = requests.post(url=self.sensorHistoryUrl,
                                              headers=self.ct_object.headers,
                                              data=json.dumps(
                                                  door_history_params)).json()
        for z in range(0,
                       168):  # Extracting the binary values of the door status indicator from the request and appending it to a list
            self.door_status_list.append(
                door_history_response['results'][z]['series'][0])

    def plot_graph(self, x_data, y_data, x_label, y_label, title):
        x_data = pd.to_datetime(x_data)
        df = pd.DataFrame({'value': y_data})
        df = df.set_index(x_data)
        plt.plot(df)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.gcf().autofmt_xdate()
        plt.show()

    # Plotting the graphs for humidity and temperature data side by side
    def temp_humid_graph(self):
        # Retrieving dates in Year-Month-Date format for each day between 2022-06-26 00:00 and 2022-07-25 00:00 for temperature and humidity graphs
        self.date_converter(1656198000, 1658790000, 86400)
        self.date_container = pd.to_datetime(self.date_container)
        # Retrieve data and labels
        x_data = self.date_container
        y_temp_data = self.temp_history_data
        y_humid_data = self.humid_history_data
        # Plot temperature and humidity side by side
        self.plot_graph(x_data, y_temp_data, "Time", "Temperature in Celsius",
                        "Temperature Data")
        self.plot_graph(x_data, y_humid_data, "Time", "Humidity in Percentage",
                        "Humidity Data")

    # Plotting the graph for the door status data
    def door_status_graph(self):
        # Converting epoch time to Year-Month-Date format per hour, between 2022-06-26 00:00:00 and 2022-07-02 23:00:00 for the Door Status dataset
        self.date_converter(1656198000, 1656802800, 3600)
        self.date_container = pd.to_datetime(self.date_container)
        # Retrieve data and labels
        x_data = self.date_container
        y_door_data = self.door_status_list
        # Plot door status data
        self.plot_graph(x_data, y_door_data, "Time",
                        "Door Status where 0 = Open, 1 = Closed",
                        "Door Status Data")

# Samsara API token
api_token = 'SAMSARA_SENSOR_TOKEN'

test_connection = ConnectionTester(api_token)
retrieve_data = DataRetriever()
retrieve_data.temp_humid_data()
retrieve_data.door_status_data()
retrieve_data.temp_humid_graph()
retrieve_data.door_status_graph()
