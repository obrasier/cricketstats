from selectolax.parser import HTMLParser
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

cache_dir = os.getenv("STATSGURU_CACHE")
apify_token = os.getenv("APIFY_TOKEN")
page = 1
pos = 1
headings = [
    [
        "player",
        "team",
        "runs",
        "runs_txt",
        "not_out",
        "mins",
        "bf",
        "4s",
        "6s",
        "sr",
        "pos",
        "innings",
        "opposition",
        "ground",
        "start_date",
        "player_id",
        "match_id",
    ],
    [
        "player",
        "team",
        "overs",
        "maidens",
        "runs",
        "wickets",
        "bpo",
        "balls",
        "economy",
        "pos",
        "innings",
        "opposition",
        "ground",
        "start_date",
        "player_id",
        "match_id",
    ],
    [
        "team",
        "score",
        "runs",
        "overs",
        "bpo",
        "rpo",
        "lead",
        "all_out",
        "declared",
        "result",
        "innings",
        "opposition",
        "ground",
        "start_date",
        "match_id",
    ],
]
# team,score,runs,overs,balls_per_over,rpo,lead,innings,result,opposition,ground,start_date,all_out_flag,declared_flag

get_idx = {"batting": 0, "bowling": 1, "team": 2}

prev_data = None


def extract_player_team(player_raw):
    brackets = re.findall(r"\((.*?)\)", player_raw)
    player = player_raw[: player_raw.rfind("(")].strip()
    team_str = brackets[-1]
    team = team_lookup(team_str)
    return player, team


def bowling_data(values, prev_data):
    global pos
    if len(values) == 11:
        (
            player_raw,
            overs,
            bpo,
            maidens,
            runs,
            wickets,
            economy,
            innings,
            opp_raw,
            ground,
            start_date,
        ) = values
    else:
        (
            player_raw,
            overs,
            maidens,
            runs,
            wickets,
            economy,
            innings,
            opp_raw,
            ground,
            start_date,
        ) = values
        bpo = 6
    player, team = extract_player_team(player_raw)
    if "DNB" in overs or overs == "absent" or overs == "sub":
        overs = np.nan
        balls = np.nan
    else:
        overs_arr = overs.split(".")
        balls = int(overs_arr[0]) * int(bpo)
        if len(overs_arr) > 1:
            balls += int(overs_arr[1])

    opposition = team_lookup(opp_raw[2:])
    start_date = parser.parse(start_date)
    if not prev_data or prev_data != (innings, opposition, ground, start_date):
        pos = 1
    else:
        pos += 1
    page_values = [
        player,
        team,
        overs,
        maidens,
        runs,
        wickets,
        bpo,
        balls,
        economy,
        pos,
        innings,
        opposition,
        ground,
        start_date,
    ]
    return page_values


def batting_data(values, prev_data):
    global pos
    (
        player_raw,
        runs_txt,
        mins,
        bf,
        fours,
        sixes,
        sr,
        inns,
        opp_raw,
        ground,
        start_date,
    ) = values
    player, team = extract_player_team(player_raw)

    if "*" in runs_txt:
        not_out = True
        runs = int(runs_txt.replace("*", ""))
    elif (
        "DNB" in runs_txt
        or runs_txt == "absent"
        or runs_txt == "sub"
        or runs_txt == "CSUB"
    ):
        runs = np.nan
        not_out = True
    else:
        not_out = False
        runs = int(runs_txt)

    opposition = team_lookup(opp_raw[2:])
    start_date = parser.parse(start_date)

    if not prev_data or prev_data != (inns, opposition, ground, start_date):
        pos = 1
    else:
        pos += 1
    # print(prev_data, (inns, opposition, ground, start_date))
    page_values = [
        player,
        team,
        runs,
        runs_txt,
        not_out,
        mins,
        bf,
        fours,
        sixes,
        sr,
        pos,
        inns,
        opposition,
        ground,
        start_date,
    ]
    return page_values


def team_data(values):
    if len(values) == 10:
        (
            team,
            score,
            overs,
            rpo,
            lead,
            inns,
            result,
            opposition,
            ground,
            start_date,
        ) = values
    elif len(values) == 9:
        team, score, overs, rpo, inns, result, opposition, ground, start_date = values
    overs = str(overs)
    overs_and_balls = overs.split("x")
    overs = overs_and_balls[0]

    bpo = 6
    if len(overs_and_balls) == 2:
        bpo = int(overs_and_balls[1])
    runs = score.split("/")[0]
    if runs == "DNB":
        runs = 0
    elif runs == "forfeited":
        runs = 0

    all_out = True
    if "/" in score or score == "DNB":
        all_out = False

    declared = False
    if score[-1] == "d":
        declared = True

    opposition = team_lookup(opposition[2:])
    start_date = parser.parse(start_date)

    if len(values) == 9:
        lead = np.nan
    page_values = [
        team_lookup(team),
        score,
        int(runs),
        overs,
        bpo,
        rpo,
        lead,
        all_out,
        declared,
        result,
        inns,
        opposition,
        ground,
        start_date,
    ]
    return page_values


def get_data(values, activity, prev_data, f):
    if activity == "batting":
        page_values = batting_data(values, prev_data)
    elif activity == "bowling":
        page_values = bowling_data(values, prev_data)
    elif activity == "team":
        page_values = team_data(values)

    skipped = False
    idx = get_idx[activity]
    inns, opposition, ground, start_date = (
        values[-4],
        values[-3],
        values[-2],
        values[-1],
    )
    start_date = parser.parse(start_date)
    if "test" in f:
        offset_date = datetime.today() - timedelta(days=5)
    else:
        offset_date = datetime.today() - timedelta(days=1)
    if start_date >= offset_date:
        page_values = []
        skipped = True

    opposition = team_lookup(opposition[2:])
    prev_data = (inns, opposition, ground, start_date)
    return page_values, prev_data, skipped


def is_nan(val):
    # check if the value is NaN (np.isnan didn't work for varied input types)
    # yes, this is confusing.
    return val != val


# For numeric-looking values, convert both sides to the same type to
# avoid formatting issues.
def values_equal(a, b):
    if type(a) is float or type(b) is float:
        return str(float(a)) == str(float(b))
    elif type(a) is int or type(b) is int:
        return int(a) == int(b)
    else:
        return str(a) == str(b)


def rows_equal(a, b):
    for i, j in zip(a, b):
        if not is_nan(i) and not values_equal(i, j):
            return False
    return True


def id_from_link(link):
    return re.search("(\d+).html", link.attributes["href"]).group(1)


def match_link(row, html):
    mouseover = row.css_first("td.padDD a").attributes["onmouseover"]
    engine_dd_id = re.search("engine-dd\d+", mouseover).group(0)
    return html.css_first(f"#{engine_dd_id} a[href*='/match/']")


def parse_page(df, html, activity, f, last_row, can_append, data_types):
    global prev_data
    idx = get_idx[activity]
    format_str = f"{f}_{activity}"
    skip_cache = False
    for table in html.css("table.engineTable"):
        # There are a few table.engineTable in the page. We want the one that has the match
        if table.select("caption").text_contains("Innings by innings list").any_matches:
            # results caption
            rows = table.css("tr.data1")
            page_values = []
            page_size = 0
            for row in rows:
                values = [i.text() for i in row.css("td")]

                # if the only result in the table says "No records...", this means that we're
                # at a table with no results. We've queried too many tables, so just return
                # False
                if values[0] == "No records available to match this query":
                    return False, df, can_append, 0, True
                # filter out all the empty string values
                values = [x for x in values if x != ""]
                values = [x if x != "-" else np.nan for x in values]

                if len(values) != format_length[format_str] or is_nan(values[1]):
                    print(values)
                    continue

                row_values, prev_data, skipped = get_data(
                    values, activity, prev_data, f
                )
                page_size = page_size + 1

                if skipped:
                    skip_cache = True

                if len(row_values) > 0:
                    if activity != "team":
                        row_values.append(f"p{id_from_link(row.css_first('a'))}")

                    row_values.append(f"m{id_from_link(match_link(row, html))}")

                    if last_row is not None and rows_equal(row_values, last_row):
                        can_append = True
                        page_values = []
                        print("appending now.")
                    else:
                        page_values.append(row_values)

            if can_append:
                page_df = pd.DataFrame(columns=headings[idx], data=page_values)
                page_df = page_df.astype(data_types)
                df = pd.concat([df, page_df], ignore_index=True)
            # Return true to say that this page was parsed correctly
            print(df)
            return True, df, can_append, page_size, skip_cache


def scrape_pages():
    for activity in (
        "batting",
        "bowling",
        "team",
    ):
        if activity == "batting":
            data_types = {
                "mins": "Int32",
                "bf": "Int32",
                "4s": "Int32",
                "6s": "Int32",
                "sr": float,
                "start_date": "datetime64[ns]",
            }
        elif activity == "bowling":
            data_types = {
                "maidens": "Int32",
                "runs": "Int32",
                "wickets": "Int32",
                "bpo": "Int32",
                "balls": "Int32",
                "economy": float,
                "start_date": "datetime64[ns]",
            }
        elif activity == "team":
            data_types = {
                "runs": "Int32",
                "bpo": "Int32",
                "rpo": float,
                "lead": "Int32",
                "innings": "Int32",
                "start_date": "datetime64[ns]",
            }

        for f in format_lookup.keys():
            print(f"Starting format {f}")
            print(f"starting {activity}")
            idx = get_idx[activity]

            if os.path.exists(f"data/{f}_{activity}.pkl"):
                df = pd.read_pickle(f"data/{f}_{activity}.pkl")
                page_num = (len(df) // 200) - 1
                last_row = df.iloc[-1].to_dict().values()
                can_append = False
            else:
                df = pd.DataFrame(columns=headings[idx])
                page_num = 1
                last_row = None
                can_append = True

            df = df.astype(data_types)
            more_results = True
            while more_results:
                print(f"Scraping page {page_num}")

                try:
                    html = getpage(page_num, f, activity)

                    more_results, df, can_append, page_size, skip_cache = parse_page(
                        df, html, activity, f, last_row, can_append, data_types
                    )

                    # Always remove the last page visited as it may not be complete.
                    if cache_dir is not None and os.path.exists(
                        cache_path(page_num, f, activity)
                    ):
                        if not more_results or page_size < 200 or skip_cache:
                            os.remove(cache_path(page_num, f, activity))

                    page_num += 1
                except TypeError as e:
                    remove_path = cache_path(page_num, f, activity)
                    print(f"Bad cache entry found, removing: {remove_path}")
                    print()

                    os.remove(remove_path)
                    raise e
                except KeyError as e:
                    print(
                        f"Unknown team code: {e} (update teams.py). Saving and skipping"
                    )
                    print()

                    more_results = False

            df.to_pickle(f"data/{f}_{activity}.pkl")
            df.to_csv(f"data/{f}_{activity}.csv")
    print("All done!")


def cache_path(page_num, f, activity):
    return f"{cache_dir}/{f}-{activity}-{page_num}.html"


def getpage(page_num, f, activity):
    from_cache = False
    format_id = format_lookup[f]
    url = f"https://stats.espncricinfo.com/ci/engine/stats/index.html?class={format_id};filter=advanced;orderby=start;page={page_num};size=200;template=results;type={activity};view=innings"

    try:
        print(url)

        if cache_dir is not None and os.path.exists(cache_path(page_num, f, activity)):
            print(f"From cache: {cache_path(page_num, f, activity)}")
            with open(cache_path(page_num, f, activity)) as c:
                webpage = c.read()
                from_cache = True
        else:
            # put a sleep in there so we don't hammer the cricinfo site too much
            time.sleep(15)
            webpage = fetch_body(url)
    except requests.exceptions.RequestException as e:
        print(f"This error occured: {e}")
        print()
        print("Sleeping and trying again in 5 seconds...")
        time.sleep(5)
        webpage = requests.get(url).text
        pass

    if cache_dir is not None and not from_cache:
        with open(cache_path(page_num, f, activity), "w") as c:
            c.write(webpage)

    html = HTMLParser(webpage)
    return html


def fetch_body(url):
    if apify_token:
        defaults = {
            "pageFunction": "async function pageFunction(context) { return { body: context.body }; }"
        }
        run = requests.post(
            f"https://api.apify.com/v2/acts/YrQuEkowkNCLdk4j2/run-sync?token={apify_token}&timeout=60&outputRecordKey=body",
            json={**defaults, "startUrls": [{"url": url}]},
            timeout=90,
        )
        run.raise_for_status()
        dataset = requests.get(
            f"https://api.apify.com/v2/acts/YrQuEkowkNCLdk4j2/runs/last/dataset/items?actorTaskId=YrQuEkowkNCLdk4j2&token={apify_token}",
            timeout=60,
        ).json()
        return dataset[0]["body"]

    return requests.get(url, timeout=10)


if cache_dir is not None and not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

scrape_pages()
