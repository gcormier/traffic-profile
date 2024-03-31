# import default packages
import time
import os
import argparse
from datetime import datetime

# import 3rd part packages
import yaml
from tqdm import tqdm
import googlemaps
import matplotlib
matplotlib.use('Agg') #necessary to plot image without display
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# import local package
import config
from datetime import datetime

gmaps = googlemaps.Client(key=config.key) #use your google api key here

# Set up argument parsing
parser = argparse.ArgumentParser(description='Trip profiling tool.')
parser.add_argument('route_file', type=str,
                    help='str: file name for a yaml with origin and destination specified')
parser.add_argument('--hours', type=int,
                    help='int: number of hours to run for')
parser.add_argument('--minutes', type=int,
                    help='int: number of minutes to run for')
parser.add_argument('--interval', default=2, type=int,
                    help='int: how often to poll traffic data')
args = parser.parse_args()

# Assign arguments to variables
file_name = args.route_file
intervalMinutes = args.interval
# If both args.minutes and hours are defined, return an error
if args.minutes is not None and args.hours is not None:
    raise ValueError("Please only use either --hours or --minutes, not both.")

# If they used args.minutes assign it to minutes
if args.minutes is not None:
    minutes = args.minutes
    
if args.hours is not None:
    minutes = args.hours * 60

# Load data from YAML file
with open(file_name, 'r') as f:
    data = yaml.safe_load(f)

origin = data["origin"]
destination = data["destination"]   


def get_duration():

    now = datetime.now()
    directions = gmaps.directions(origin, destination, traffic_model="best_guess", mode="driving", departure_time=now)

    traffic_secs = directions[0]['legs'][0]['duration_in_traffic']['value'] / 60

    return now, traffic_secs


def plot_todays_traffic(data, route_name):

    times_list = data['datetime']
    durations_list = data['duration']

    print (data['datetime'].iloc[0])
    start_date = datetime.strptime(str(data['datetime'].iloc[0]), '%Y-%m-%d %H:%M:%S.%f')
    pretty_date = start_date.strftime(f"%Y-%m-%d-%H%M")

    fig, ax = plt.subplots()
    ax.plot_date(times_list, durations_list, linestyle='-', linewidth=3, marker=" ")

    ax.set_ylabel('Trip Duration (min)')
    ax.set_xlabel('Departure Time')
    ax.set_title(f"Traffic Profile for {route_name} Starting at {pretty_date}")


    fig.autofmt_xdate()

    with plt.style.context('ggplot'):
        plt.savefig(f'./traffic_profile_{route_name}_{pretty_date}.png')

    return


def main():
    
    p, f = os.path.split(file_name)
    
    route = f.replace(".yaml", "")
    # data stored is csv of day of the week, date time of instance, and duration of trip
    df = pd.DataFrame(columns=('day_of_week','datetime','duration'))
    
    
    print(f"Calculating trip duration over the next {minutes} minutes at {intervalMinutes} minute intervals.")
    for i in tqdm(range((int)(minutes / intervalMinutes))):
        now, duration = get_duration()
        dow = datetime.today().weekday()
        df.loc[i] = [dow, now, duration]
        time.sleep(60 * intervalMinutes)


    if not os.path.isfile('./traffic_%s.csv' % route):
        with open('./traffic_%s.csv' % route, 'w') as f:
            df.to_csv(f, header=True, index=False)

    else:
        with open('./traffic_%s.csv' % route, "a") as f:
            df.to_csv(f, header=False, index=False)
    
    plot_todays_traffic(df, route)

    return

main()
