import re

format_lookup = {
    "men_test": 1,
    "men_odi": 2,
    "men_t20i": 3,
    "women_test": 8,
    "women_odi": 9,
    "women_t20i": 10,
}
# format_lookup = {'women_odi': 9, 'women_t20i':10}

format_length = {
    "men_test_batting": 11,
    "men_test_bowling": 11,
    "men_odi_bowling": 11,
    "men_odi_batting": 11,
    "men_t20i_batting": 11,
    "men_t20i_bowling": 10,
    "women_test_batting": 11,
    "women_test_bowling": 11,
    "women_odi_batting": 11,
    "women_odi_bowling": 10,
    "women_t20i_batting": 11,
    "women_t20i_bowling": 10,
    "men_test_team": 10,
    "men_odi_team": 9,
    "men_t20i_team": 9,
    "women_test_team": 10,
    "women_odi_team": 9,
    "women_t20i_team": 9,
}

teams = {
    "Australia": ["aus"],
    "England": ["eng"],
    "South Africa": ["sa"],
    "West Indies": ["wi"],
    "New Zealand": ["nz"],
    "India": ["ind"],
    "Pakistan": ["pak"],
    "Sri Lanka": ["sl"],
    "Zimbabwe": ["zim"],
    "Bangladesh": ["ban", "bd", "bdesh"],
    "ICC World XI": ["icc", "world"],
    "Ireland": ["ire"],
    "Afghanistan": ["afg"],
    "East Africa": ["eaf"],
    "Canada": ["can"],
    "U.S.A.": ["usa"],
    "Nepal": ["nep"],
    "Oman": ["oma"],
    "Namibia": ["nam"],
    "U.A.E.": ["uae"],
    "Scotland": ["sco", "scot"],
    "P.N.G.": ["png"],
    "Netherlands": ["ned", "neth", "nl"],
    "Hong Kong": ["hkg"],
    "Kenya": ["ken"],
    "Bermuda": ["bmuda"],
    "Asia XI": ["asia"],
    "Africa XI": ["afr"],
    "Bahrain": ["bhr"],
    "Saudi Arabia": ["ksa", "saudi"],
    "Maldives": ["mal", "mald", "mdv"],
    "Kuwait": ["kuw"],
    "Qatar": ["qat"],
    "Philippines": ["phi"],
    "Vanuatu": ["van", "vanuatu wome"],
    "Malta": ["mlt"],
    "Spain": ["esp"],
    "Mexico": ["mex"],
    "Belize": ["blz"],
    "Costa Rica": ["crc"],
    "Panama": ["pnm"],
    "Germany": ["ger"],
    "Belgium": ["bel", "belg"],
    "Nigeria": ["nga"],
    "Ghana": ["gha"],
    "Uganda": ["uga"],
    "Botswana": ["bot"],
    "Italy": ["ita"],
    "Jersey": ["jer", "jey"],
    "Guernsey": ["gue", "gun"],
    "Norway": ["nor"],
    "Denmark": ["den"],
    "Thailand": ["thai", "thi"],
    "Malaysia": ["mal"],
    "Samoa": ["samwn"],
    "Finland": ["fin"],
    "Singapore": ["sgp", "spore"],
    "Cayman Islands": ["caym", "cayman is"],
    "Romania": ["rom"],
    "Austria": ["aut"],
    "Turkey": ["tky"],
    "Luxembourg": ["lux"],
    "Czech Republic": ["czk-r", "czech rep."],
    "Argentina": ["arg"],
    "Chile": ["chi"],
    "Peru": ["per"],
    "Serbia": ["srb"],
    "Bulgaria": ["bul"],
    "Portugal": ["port"],
    "Gibraltar": ["gibr"],
    "Mozambique": ["moz"],
    "Malawi": ["mlw", "mwi"],
    "Bhutan": ["bhu"],
    "Iran": [],
    "Isle of Man": ["iom"],
    "Indonesia": ["ina", "indonesia wm"],
    "Myanmar": ["mya"],
    "Rwanda": ["rwa", "rwn"],
    "Sierra Leone": ["sierra l", "sle"],
    "Japan": ["jpn"],
    "Fiji": ["fji"],
    "Tanzania": ["tan", "tzn"],
    "Mali": ["mli"],
    "France": ["fra", "fran"],
    "Singapor": ["sin"],
    "South Korea": ["kor", "sk", "skor"],
    "China": ["chn"],
    "Young England": ["yewmn", "y. eng"],
    "International XI": ["intwn", "int xi"],
    "Trinidiad and Tobago": ["ttwmn", "t & t"],
    "Jamaica": ["jamwn"],
    "Lesotho": ["les"],
    "Brazil": ["bra", ""],
    "Hungary": ["hun"],
    "Sweden": ["swe"],
    "Greece": ["grc"],
    "Eswatini": ["esw", "swa", "swz", "swaziland"],
    "Cameroon": ["cam", "cmr"],
    "Estonia": ["est"],
    "Cyprus": ["cyp"],
    "Seychelles": ["sey"],
    "Switzerland": ["sui"],
    "Bahamas": ["bhm"],
    "Saudia Arabia": ["ksa"],
    "Gambia": ["gam"],
    "Israel": ["isr"],
    "Denmk": ["dnk"],
    "Croatia": ["crt"],
    "Barbados": ["brb"],
    "Slovenia": ["svn"],
    "Cook Islands": ["cok"],
    "World XI": ["world-xi"],
    "St Helena": ["sthel"],
}

teams_inverted = {}

for team, keys in teams.items():
    teams_inverted[team.lower()] = team

    for key in keys:
        teams_inverted[key] = team


def team_lookup(team):
    canonical = re.sub(r"(-w| (women|wmn))$", "", team.lower())

    return teams_inverted[canonical]
