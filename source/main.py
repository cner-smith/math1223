import requests
import json
import csv
import logging
import datetime
import os

from datetime import timedelta
from requests import Response
logging.basicConfig(level=logging.ERROR)

# Initialize a counter for the number of files written
files_written_counter = 0


def get_source_id(code: str, fight_id: str, name: str) -> str:
    query = GET_SOURCE_ID_QUERY.format(code=code, fightID=fight_id)
    response = oauth2_client.make_request(GRAPHQL_ENDPOINT, query)
    
    if response.status_code == 200:
        source_data = json.loads(response.content)
        try:
            data_keys = source_data.get('data', {}).get('reportData', {}).get('report', {}).get('table', {}).get('data', {})
            if 'composition' in data_keys:
                for entry in data_keys['composition']:
                    if entry['name'] == name:
                        return entry['id']
                logging.error(f"No matching player found for {name}")
                # TODO: need to probably find/make an exception for data retrieve fails
                raise  # Raise Error if data retrieval fails
            else:
                logging.error(f"No 'composition' data in the response.")
        except Exception as e:
            logging.error(f"Exception: {e}")
            logging.error(f"Data: {source_data}")
            raise
    else:
        logging.error(f"Request failed with status code: {response.status_code}")

    raise  # Return None if data retrieval fails


def export_player_data(fight_id: str, code: str, source_id: str) -> None:
    # Export the player's data to a CSV file
    query = GET_PLAYER_DATA_QUERY.format(code=code, fightID=fight_id, sourceID=source_id)
    response = oauth2_client.make_request(GRAPHQL_ENDPOINT, query)  # Using the OAuth2Client method
    player_data_response = response.content
    
    if player_data_response:
        try:
            player_data = json.loads(player_data_response)

            if isinstance(player_data, dict) and player_data:  # Check if player_data is a non-empty dictionary
                with open(f"{code}.csv", "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(player_data.keys())  # Write header row
                    writer.writerow(player_data.values())  # Write data rows
            else:
                logging.error(f"Player data is empty or not in the expected format.")

        except json.decoder.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")

    else:
        logging.error(f"No 'data' attribute found in the player data response.")


def modify_healing_done_data(healing_data: str) -> list[dict[str, str]]:
    modified_healing_data = []
    for entry in healing_data:
        # Append each ability's healing and its amount as a separate row
        modified_healing_data.append({'ability': entry['name'], 'healing_amount': entry['total']})
    return modified_healing_data


def modify_combatant_info_data(combatant_info: str) -> list[dict[str, str]]:
    modified_combatant_info = []
    stats_data = combatant_info.get("stats", {})
    for stat_key, stat_value in stats_data.items():
        # Assuming the value could be in a format like {'min': x, 'max': y}, we'll default to 'min'
        value_to_add = stat_value['min'] if isinstance(stat_value, dict) and 'min' in stat_value else stat_value
        # Ensure the value is an integer
        value_to_add = int(value_to_add)
        modified_combatant_info.append({'info_key': stat_key, 'info_value': value_to_add})
    return modified_combatant_info


def process_data_and_export(name: str, data: str) -> None:
    global files_written_counter

    # Extract and modify the required data
    total_time = str(timedelta(milliseconds=data.get('totalTime', 0))).split(", ")[-1]  # Convert milliseconds to a readable time format

    healers_count = sum(1 for player in data.get('composition', []) if player.get('specs') and 'healer' in player['specs'][0].get('role', '').lower())

    modified_healing_data = modify_healing_done_data(data.get('healingDone', []))
    modified_combatant_info_data = modify_combatant_info_data(data.get('combatantInfo', {}))

    # Check if csv-output file exists, if not create it
    os.makedirs("csv-output", exist_ok=True)

    # Write the modified data to a new CSV file named after the player's name
    with open(f"csv-output/{name}_modified.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=['total_time', 'healers_count', 'stats', 'total', 'ability', 'healing_done_total'])
        writer.writeheader()

        # Concurrently write combatant info data and healing data
        max_rows = max(len(modified_combatant_info_data), len(modified_healing_data))
        for i in range(max_rows):
            row_data = {
                'total_time': total_time if i == 0 else None,  # Write only once
                'healers_count': healers_count if i == 0 else None,  # Write only once
                'stats': modified_combatant_info_data[i]['info_key'] if i < len(modified_combatant_info_data) else None,
                'total': modified_combatant_info_data[i]['info_value'] if i < len(modified_combatant_info_data) else None,
                'ability': modified_healing_data[i]['ability'] if i < len(modified_healing_data) else None,
                'healing_done_total': modified_healing_data[i]['healing_amount'] if i < len(modified_healing_data) else None
            }
            writer.writerow(row_data)

    files_written_counter += 1
    print(f"Files Written ({files_written_counter}/100)")


class OAuth2Client:
    def __init__(self, client_id: str, client_secret: str, authorization_url: str, access_token_url: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_url = authorization_url
        self.access_token_url = access_token_url
        self.access_token = None
        self.token_expiry = None
        self.get_access_token()

    def get_access_token(self) -> str:
        if hasattr(self, 'access_token') and self.access_token and hasattr(self, 'token_expiry') and self.token_expiry and datetime.datetime.now() < self.token_expiry:
            return self.access_token
        
        response = requests.post(
            self.access_token_url,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret)
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            # Assuming token expires in 1 hour for caching purposes.
            self.token_expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
            return self.access_token
        else:
            logging.error(f"Failed to obtain access token.")
            raise

    def make_request(self, url: str, query: str = '') -> Response:
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.post(url, headers=headers, json={"query": query})
        return response


# Set the GraphQL endpoint
GRAPHQL_ENDPOINT = "https://www.warcraftlogs.com/api/v2/client"

# Define the GraphQL queries
GET_TOP_PRIESTS_QUERY = """
query request {
    worldData{
        encounter(id:2685){
            characterRankings(
                metric: hps,
                className: "Priest"
                specName: "Holy"

            )
        }
    }
}
"""

GET_SOURCE_ID_QUERY = """
query request {{
    reportData {{
        report(code:"{code}") {{
            table(fightIDs:{fightID})
        }}
    }}
}}
"""

GET_PLAYER_DATA_QUERY = """
query request {{
    reportData {{
        report(code:"{code}") {{
            table(fightIDs:{fightID}, sourceID:{sourceID})
        }}
    }}
}}
"""

# TODO: consider transition to .env file instead of config.json file
with open('config.json', 'r') as f:
    config_data = json.load(f)

# Create an OAuth2 client
oauth2_client = OAuth2Client(
    client_id=config_data["client_id"],
    client_secret=config_data["client_secret"],
    authorization_url="https://www.warcraftlogs.com/oauth/authorize",
    access_token_url="https://www.warcraftlogs.com/oauth/token"
)


def main() -> None:

    access_token = oauth2_client.get_access_token()

    if not access_token:
        logging.error(f"No access token obtained. Cannot make the request.")
        return

    response = oauth2_client.make_request(GRAPHQL_ENDPOINT, GET_TOP_PRIESTS_QUERY)
    if response.status_code != 200:
        logging.error(f"Request for top priests data failed with status code: {response.status_code}")
        return

    top_priests_response = response.json()
    if 'data' in top_priests_response:
        priest_rankings = top_priests_response['data']['worldData']['encounter']['characterRankings']['rankings']

        player_data = []

        for entry in priest_rankings:
            # Process each priest in some way, extracting required information
            code = entry["report"]["code"]
            fight_id = entry["report"]["fightID"]
            name = entry["name"]

            # Get the source ID for the player
            source_id = get_source_id(code, fight_id, name)

            if source_id:
                # Add the player data to the list
                player_data.append({
                    "code": code,
                    "fight_id": fight_id,
                    "name": name,
                    "source_id": source_id
                })
            else:
                logging.error(f"Failed to retrieve source ID for {code}")

        # Export the player data and process it
        for entry in player_data:
            # export_player_data(entry["fight_id"], entry["code"], entry["source_id"])

            # Already have source_id from the earlier call, so we use it directly
            report_data_response = oauth2_client.make_request(GRAPHQL_ENDPOINT, GET_PLAYER_DATA_QUERY.format(code=entry["code"], fightID=entry["fight_id"], sourceID=entry["source_id"]))

            if "data" in report_data_response.json():
                report_data = report_data_response.json()["data"]["reportData"]["report"]["table"]["data"]
                process_data_and_export(entry["name"], report_data)  # Pass player's name to function
            else:
                logging.error(f"No 'data' attribute found in the report for {entry['code']}")
    else:
        logging.error(f"No 'data' attribute found in the response for top priests.")


if __name__ == "__main__":
    main()
