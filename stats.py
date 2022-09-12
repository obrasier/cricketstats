import pandas as pd
import numpy as np
import glob
import datetime
import argparse
import pickle


def get_dataset(args):
    gender = "women" if args.women else "men"
    form = "bowling" if args.bowling else "batting"

    if args.teams:
        df = pd.read_pickle(f"data/{gender}_{args.format}_team.pkl")
    else:
        df = pd.read_pickle(f"data/{gender}_{args.format}_{form}.pkl")
    return df


def get_max_consecutive(group):
    # this works for each player
    # first get all matches and compare with a shifted version to how many are the same in a row
    df_bool = group["criteria_match"] != group["criteria_match"].shift()
    # take the cumulative sum of the matches in a row to get the number of each
    df_cumsum = df_bool.cumsum()
    # then groupby the size of each group
    search_groups = group.groupby(df_cumsum)

    # the above will give us the size, but we also want the raw data out of each
    # so below we are getting the indexes from the original dataset so we can look them up later

    # what we want is the longest group where criteria_match == True
    # make a dictionary with the key the name, but store each length
    lengths = {n: len(g) for n, g in search_groups if g["criteria_match"].all() == True}
    try:
        # m is the maximum number of matches
        m = max(lengths.values())
    except ValueError:
        # if there are no matches, return 0 and not-a-number
        return pd.DataFrame({"maximum": [0], "num_results": 0, "indexes": [np.nan]})
    # get a list of groups where the match is the players maximum value
    # includes if a player matches multiple times
    # all_groups = [search_groups.get_group(key) for key,val in lengths.items()]
    max_groups_list = [
        search_groups.get_group(key) for key, val in lengths.items() if val == m
    ]
    num_items = len(max_groups_list)
    return pd.DataFrame(
        {
            "maximum": [m] * num_items,
            "num_results": [num_items] * num_items,
            "indexes": [g["index"].values for g in max_groups_list],
        }
    )


def get_all_consecutive(criteria, data, sort_order=["player", "start_date", "innings"]):
    data = data.sort_values(by=sort_order)
    data.reset_index(inplace=True)
    # Get all rows where runs is not NaN
    data = data.dropna(subset=["runs"])

    # drop all columns where the values were after doesn't exist
    all_columns = list(data.columns.values)
    for c in all_columns:
        if c in criteria:
            data = data[data[c] != np.nan]
    # find all matches and set them to true, set non-matches to False
    data.loc[data.eval(criteria), "criteria_match"] = True
    data["criteria_match"].fillna(False, inplace=True)
    # group by all the search item, and then actually do the check for each one.
    search_item = all_columns[1]
    results = data.groupby(search_item).apply(get_max_consecutive)
    return results


def get_most_consecutive(
    query, data, sort_order=["player", "start_date", "innings"], args=None
):
    results = get_all_consecutive(query, data, sort_order)
    # get the maximum result
    max_value = results["maximum"].max()
    # get all matches to the maximum
    max_results = results[results["maximum"] == max_value]
    # get the matches out of the original dataset to get the innings
    result_data = data.reindex(np.concatenate(max_results.indexes.values))

    return max_value, result_data


# def get_most_consecutive_team(query, data, sort_order=['team', 'start_date', 'innings'], args=None):
#     return get_most_consecutive(query, data, sort_order, args=args)


def filter_pos(data, args):
    sort_order = ["player", "start_date", "innings"]
    data = data.sort_values(by=sort_order)
    data.reset_index(inplace=True)
    # Get all rows where runs is not NaN
    if not args.bowling:
        data = data.dropna(subset=["runs"])
    else:
        data = data.dropna(subset=["overs"])
    bats = data.groupby(["player"])["pos"].agg(pd.Series.mean)
    if not args.tail:
        bats = bats[bats <= args.maxpos]
    else:
        bats = bats[bats > args.maxpos]
    data = data[data["player"].isin(bats.index)]
    return data


def query_data(data, query):
    result = data.query(query)
    match = result.groupby(["player"]).size().sort_values(ascending=False)
    return match


parser = argparse.ArgumentParser(
    description="Consecutive cricket stats, process a query, get consecutive cricket stats."
)
parser.add_argument(
    "query",
    type=str,
    help="The query you want to ask. Must use the column headings in the data files.",
)
parser.add_argument("--women", "-w", default=False, action="store_true")
parser.add_argument("--bowling", "-b", default=False, action="store_true")
parser.add_argument("--teams", "-t", default=False, action="store_true")
parser.add_argument("--average", "-a", default=False, action="store_true")
parser.add_argument(
    "--complex",
    "-c",
    default=False,
    action="store_true",
    help="ignore the query option and use a code version in the file instead.",
)
parser.add_argument(
    "--print",
    "-p",
    default=False,
    action="store_true",
    help="print the whole dataframe as output",
)
parser.add_argument(
    "--format",
    "-f",
    default="test",
    choices=["test", "odi", "t20i"],
    help="The format you want data for, default is test",
)
parser.add_argument("--tail", default=False, action="store_true")
parser.add_argument("--filter", default=False, action="store_true")
parser.add_argument("--maxpos", nargs="?", const=6, type=int, default=6)


args = parser.parse_args()

if args.print:
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", None)


df = get_dataset(args)

if args.complex:
    # modify this example from the blogpost, it's just an example of a complex query that might
    # be easier to write in the code instead of writing it into the command line:
    # call with `consecutive_stats.py --complex` (assuming individual men and test, which are the default)
    english_grounds = [
        "Lord's",
        "Birmingham",
        "Manchester",
        "The Oval",
        "Sheffield",
        "Nottingham",
        "Leeds",
    ]

    # this is how you can build it up programmatically, start with the beginning of the query
    query = """innings_wickets_taken >= 3 and (ground == """

    # this next line is tricky, have to wrap each item in double quotes ""
    query += " or ground == ".join(f'"{g}"' for g in english_grounds)

    # finish it off by closing the brackets
    query += ")"
    # print so you see that the final query looks like
    print(query)

    # sorting by player, ground, data, number groups the players together
    sort_order = ["player", "ground", "start_date", "innings"]

    results = get_all_consecutive(query, df.copy(), sort_order)
    results.sort_values(by=["maximum"], ascending=False, inplace=True)
    # display 10 results by default
    print(results.head(10)["maximum"])
else:
    if args.filter:
        data = filter_pos(df.copy(), args)
        result = query_data(data, args.query)
    else:
        if args.teams:
            max_value, result = get_most_consecutive(
                args.query, data=df.copy(), sort_order=["team", "start_date", "innings"]
            )
        else:
            max_value, result = get_most_consecutive(args.query, data=df.copy())
        print(max_value)

    print(result)
    # if args.bowling:
    #     # innings_overs_bowled,innings_bowled_flag,innings_maidens_bowled,innings_runs_conceded,innings_wickets_taken,4_wickets,5_wickets,10_wickets,innings_wickets_taken_buckets,innings_economy_rate
    #     cols_to_print = ['player', 'overs', 'maidens', 'wickets',
    #                      'runs', 'economy', 'opposition' ,'ground', 'start_date', 'innings']
    # else:
    #     # batting columns available, there are more but these are the actually useful ones
    #     cols_to_print = ['player', 'team', 'runs', 'runs_txt', 'not_out', 'mins', 'pos', 'bf', '4s', '6s', 'sr','innings','opposition','ground','start_date']
    # print(result[cols_to_print])
