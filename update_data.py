from bs4 import BeautifulSoup
from dateutil import parser
import pandas as pd
import numpy as np

import requests
import time
import pickle
from datetime import datetime, timedelta
import re
import os

from teams import team_lookup, format_lookup, format_length

page = 1
pos = 1
headings = [['player', 'team', 'runs', 'runs_txt', 'not_out', 'mins', 'bf', '4s', '6s', 'sr', 'pos', 'innings','opposition','ground','start_date'],
            ['player', 'team', 'overs', 'maidens', 'runs', 'wickets', 'bpo', 'balls', 'economy', 'pos', 'innings', 'opposition', 'ground', 'start_date'],
            ['team', 'score', 'runs', 'overs', 'bpo', 'rpo', 'lead', 'all_out', 'declared', 'result', 'innings', 'opposition', 'ground', 'start_date']]
#team,score,runs,overs,balls_per_over,rpo,lead,innings,result,opposition,ground,start_date,all_out_flag,declared_flag

get_idx = {'batting': 0, 'bowling': 1, 'team': 2}

prev_data = None

def extract_player_team(player_raw):
    brackets = re.findall(r'\((.*?)\)', player_raw)
    player = player_raw[:player_raw.rfind('(')].strip()
    team_str = brackets[-1]
    team = team_lookup[team_str]
    return player, team

def bowling_data(values, prev_data):
    global pos
    if len(values) == 11:
        player_raw, overs, bpo, maidens, runs, wickets, economy, innings, opp_raw, ground, start_date = values
    else:
        player_raw, overs, maidens, runs, wickets, economy, innings, opp_raw, ground, start_date = values
        bpo = 6
    player, team = extract_player_team(player_raw)
    if 'DNB' in overs or overs == 'absent' or overs == 'sub':
        overs = np.nan
        balls = np.nan
    else:
        overs_arr = overs.split('.')
        balls = int(overs_arr[0]) * int(bpo)
        if len(overs_arr) > 1:
            balls += int(overs_arr[1])
    
    opposition = opp_raw[2:]
    start_date = parser.parse(start_date)
    if not prev_data or prev_data != (innings, opposition, ground, start_date):
        pos = 1
    else:
        pos += 1
    page_values = [player, team, overs, maidens, runs, wickets, bpo, balls, economy, pos, innings, opposition, ground, start_date]
    return page_values


def batting_data(values, prev_data):
    global pos
    player_raw, runs_txt, mins, bf, fours, sixes, sr, inns, opp_raw, ground, start_date = values
    player, team = extract_player_team(player_raw)

    
    if '*' in runs_txt:
        not_out = True
        runs = int(runs_txt.replace('*', ''))
    elif 'DNB' in runs_txt or runs_txt == 'absent' or runs_txt == 'sub':
        runs = np.nan
        not_out = True
    else:
        not_out = False
        runs = int(runs_txt)

    opposition = opp_raw[2:]
    start_date = parser.parse(start_date)

    if not prev_data or prev_data != (inns, opposition, ground, start_date):
        pos = 1
    else:
        pos += 1
    # print(prev_data, (inns, opposition, ground, start_date))
    page_values = [player, team, runs, runs_txt, not_out, mins, bf, fours, sixes, sr, pos, inns, opposition, ground, start_date]
    return page_values

def team_data(values):
    if len(values) == 10:
        team, score, overs, rpo, lead, inns, result, opposition, ground, start_date = values
    elif len(values) == 9:
        team, score, overs, rpo, inns, result, opposition, ground, start_date = values
    overs = str(overs)
    overs_and_balls = overs.split('x')
    overs = overs_and_balls[0]
    
    bpo = 6
    if len(overs_and_balls) == 2:
        bpo = int(overs_and_balls[1])
    runs = score.split('/')[0]
    if runs == 'DNB':
        runs = 0
    elif runs == 'forfeited':
        runs = 0

    all_out = True
    if '/' in score or score == 'DNB':
        all_out = False
    
    declared = False
    if score[-1] == 'd':
        declared = True
    
    opposition = opposition[2:]
    if len(values) == 9:
        lead = np.nan
    page_values = [team, score, int(runs), overs, bpo, rpo, lead, all_out, declared, result, inns, opposition, ground, start_date]
    return page_values

def get_data(values, page_df, activity, prev_data, f):
    if activity == 'batting':
        page_values = batting_data(values, prev_data)
    elif activity == 'bowling':
        page_values = bowling_data(values, prev_data)
    elif activity == 'team':
        page_values = team_data(values)
    
    idx = get_idx[activity]
    inns, opposition, ground, start_date = values[-4], values[-3], values[-2], values[-1]
    start_date = parser.parse(start_date)
    if 'test' in f:
        offset_date = datetime.today() - timedelta(days=5)
    else:
        offset_date = datetime.today() - timedelta(days=2)
    if start_date < offset_date:
        series = pd.Series(page_values, index=headings[idx])
        page_df = page_df.append(series, ignore_index=True)

    opposition = opposition[2:]
    prev_data = (inns, opposition, ground, start_date)
    return page_df, prev_data

def is_nan(val):
    # check if the value is NaN (np.isnan didn't work for varied input types)
    # yes, this is confusing.
    return val != val

def parse_page(df, soup, activity, f, last_row, can_append):
    global prev_data
    idx = get_idx[activity]
    format_str = f"{f}_{activity}"
    for table in soup.findAll("table", class_ = "engineTable"):
        # There are a few table.engineTable in the page. We want the one that has the match
        if table.find("caption", text="Innings by innings list") is not None:
        # results caption
            rows = table.findAll("tr", class_ = "data1")
            page_df = pd.DataFrame(columns=headings[idx])
            for row in rows:
                values = [i.text for i in row.findAll("td")]
                
                # if the only result in the table says "No records...", this means that we're
                # at a table with no results. We've queried too many tables, so just return
                # False
                if values[0] == u'No records available to match this query':
                    return False, df, can_append
                # filter out all the empty string values
                values = [x for x in values if x != '']
                values = [x if x != '-' else np.nan for x in values]
                # print(len(values))
                if len(values) != format_length[format_str] or is_nan(values[1]):
                    print(values)
                    continue

                page_df, prev_data = get_data(values, page_df, activity, prev_data, f)
                if not page_df.empty and page_df.iloc[-1].equals(last_row):
                    can_append = True
                    page_df = pd.DataFrame(columns=headings[idx])
                    print('appending now.')
                
            if can_append:
                df = df.append(page_df, ignore_index=True)
            # Return true to say that this page was parsed correctly
            print(df)
            return True, df, can_append

def scrape_pages():
    for activity in ('batting', 'bowling', 'team',):
        for f in format_lookup.keys():
            print(f'Starting format {f}')
            print(f'starting {activity}')
            idx = get_idx[activity]

            if os.path.exists(f"data/{f}_{activity}.pkl"):
                df = pd.read_pickle(f"data/{f}_{activity}.pkl")
                page_num = (len(df) // 200) - 1
                last_row = df.iloc[-1]
                can_append = False
            else:
                df = pd.DataFrame(columns=headings[idx])
                page_num = 1
                last_row = None
                can_append = True
            more_results = True
            while more_results:
                print(f"Scraping page {page_num}")
                
                soup = getpage(page_num, f, activity)
                more_results, df, can_append = parse_page(df, soup, activity, f, last_row, can_append)
                # put a sleep in there so we don't hammer the cricinfo site too much
                time.sleep(0.5)
                page_num += 1
            if activity == 'batting':
                data_types = {'mins': int, 'bf': int, '4s': int, '6s': int, 'sr': float}
            elif activity == 'bowling':
                data_types = {'maidens': int, 'runs': int, 'wickets':int, 'bpo': int, 'balls': int, 'economy': float}
            elif activity == 'team':
                data_types = {'runs': int, 'bpo': int, 'rpo': float, 'lead': int, 'innings': int}
            df = df.astype(data_types, errors='ignore')
            df.to_pickle(f'data/{f}_{activity}.pkl')
            df.to_csv(f'data/{f}_{activity}.csv')
    print('All done!')

def getpage(page_num, f, activity):
    f = format_lookup[f]
    url = f'https://stats.espncricinfo.com/ci/engine/stats/index.html?class={f};filter=advanced;orderby=start;page={page_num};size=200;template=results;type={activity};view=innings'
    try:
        webpage = requests.get(url).text
    except requests.exceptions.RequestException as e:
        print(f"This error occured: {e}")
        print()
        print('Sleeping and trying again in 5 seconds...')
        time.sleep(5)
        webpage = requests.get(url).text
        pass
    
    soup = BeautifulSoup(webpage, features="html.parser")
    return soup

scrape_pages()
