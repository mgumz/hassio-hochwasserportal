import requests
import bs4
import re

API_TIMEOUT = 10

def fetch_json(url):
    try:
        response = requests.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        json_data = response.json()
        return json_data
    except requests.exceptions.RequestException as e:
        LOGGER.error("An error occurred while fetching the JSON: %s", e)
        return None
    except ValueError as e:
        LOGGER.error("Error parsing JSON data: %s", e)
        return None

def fetch_soup(url):
    try:
        response = requests.get(url, timeout=API_TIMEOUT)
        # Override encoding by real educated guess (required for SH)
        response.encoding = response.apparent_encoding
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, "lxml")
        return soup
    except requests.exceptions.RequestException as e:
        LOGGER.error("An error occurred while fetching the LXML: %s", e)
        return None
    except XMLSyntaxError as e:
        LOGGER.error("Error parsing LXML data: %s", e)
        return None

def get_by_stations():
    stations = []
    data = fetch_soup("https://www.hnd.bayern.de/pegel")
    boobls = data.find_all("img", class_="bobbl")
    for bobbl in boobls:
        ident  = "BY_"+str(bobbl.get('id'))[1:]
        name = str(bobbl.get('data-name')).strip()+" / "+str(bobbl.get('data-zeile2')).strip()
        stations.append((ident, name))
    return stations

def get_ni_stations():
    stations = []
    data = fetch_json("https://bis.azure-api.net/PegelonlinePublic/REST/stammdaten/stationen/All?key=9dc05f4e3b4a43a9988d747825b39f43")
    for entry in data['getStammdatenResult']:
        ident = "NI_"+entry['STA_Nummer']
        name = entry['Name'].strip()+" / "+entry['GewaesserName'].strip()
        stations.append((ident, name))
    return stations

def get_nw_stations():
    stations = []
    data = fetch_json("https://hochwasserportal.nrw/lanuv/data/internet/stations/stations.json")
    for station in data:
        if len(station["WTO_OBJECT"].strip()) > 0:
            ident = "NW_"+station["station_no"]
            name = station["station_name"].strip()+" / "+station["WTO_OBJECT"].strip()
            stations.append((ident, name))
    return stations

def get_sh_stations():
    stations = []
    data = fetch_soup("https://hsi-sh.de")
    search_string =re.compile('dialogheader-*')
    h1s = data.find_all("h1", id=search_string)
    for h1 in h1s:
        h1_text = h1.getText().split()
        name = " ".join(h1_text[0:len(h1_text)-2])
        ident = "SH_"+h1_text[-1]
        d_list = h1.find_next()
        for dd in d_list:
            if dd.name == 'dd' and dd.attrs['class'][0] == 'tooltip-content__gewaesser':
                name += " / "+dd.getText().strip()
        stations.append((ident, name))
    return stations

def get_th_stations():
    stations = []
    data = fetch_soup("https://hnz.thueringen.de/hw-portal/thueringen.html")
    table = data.find_all("table", id="pegelTabelle")[0]
    tbody = table.find_all("tbody")[0]
    trs = tbody.find_all("tr")
    for tr in trs:
        tds = tr.find_all("td")
        ident = None
        name = None
        cnt = 0
        for td in tds:
            if cnt == 1:
                ident = "TH_"+td.getText().strip()
            elif cnt == 2:
                name = td.getText().strip()
            elif cnt == 3:
                name += " / "+td.getText().strip()
            cnt += 1
        stations.append((ident, name))
    return stations

# Fetch and sort all available stations
all_stations = []
print("Fetching BY")
all_stations.extend(get_by_stations())
print("Fetching NI")
all_stations.extend(get_ni_stations())
print("Fetching NW")
all_stations.extend(get_nw_stations())
print("Fetching SH")
all_stations.extend(get_sh_stations())
print("Fetching TH")
all_stations.extend(get_th_stations())

all_stations.sort(key=lambda x: x[0])

print("Updating pegel.md")
f = open("pegel.md", "w", encoding="utf-8")

output = "| Pegel | Description |"
print(output, file=f)
output = "|-------|-------------|"
print(output, file=f)
for pegel in all_stations:
    output = "| " + pegel[0] + " | " + pegel[1] + " |"
    print(output, file=f)

f.close()