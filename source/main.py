import requests
import json
import csv

def get_source_id(code, fight_id, access_token, name):
    # Get the source ID for the player
    response = requests.post(
        GRAPHQL_ENDPOINT,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"query": GET_SOURCE_ID_QUERY.format(code=code, fightID=fight_id)}
    )
    
    if response.status_code == 200:
        source_data = json.loads(response.content)
        if 'data' in source_data and 'reportData' in source_data['data'] and 'report' in source_data['data']['reportData']:
            data = source_data['data']['reportData']['report']['table']['data']
            if 'composition' in data:
                # Loop through the composition to find the matching name
                for entry in data['composition']:
                    if entry['name'] == name:
                        return entry['name'], entry['id']
                print(f"No matching player found for {name}")
            else:
                print("No 'composition' data in the response.")
        else:
            print("Unexpected response structure - missing specific data attributes")
    else:
        print("Request failed with status code:", response.status_code)

    return None, None  # Return None if data retrieval fails

def export_player_data(fight_id, code, source_id, access_token):
    # Export the player's data to a CSV file
    response = requests.post(
        GRAPHQL_ENDPOINT,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"query": GET_PLAYER_DATA_QUERY.format(code=code, fightID=fight_id, sourceID=source_id)}
    )
    player_data_response = json.loads(response.content)
    print(player_data_response)

    if "data" in player_data_response:
        player_data = player_data_response["data"]["reportData"]["report"]["table"]["data"]

        if isinstance(player_data, list) and player_data:  # Check if player_data is a non-empty list
            with open(f"{code}.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(player_data[0].keys())  # Write header row

                for row in player_data:
                    writer.writerow(row.values())  # Write data rows
        else:
            print("Player data is empty or not in the expected format.")
    else:
        print("No 'data' attribute found in the player data response.")

class OAuth2Client:
    def __init__(self, client_id, client_secret, authorization_url, access_token_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_url = authorization_url
        self.access_token_url = access_token_url
        self.access_token = None

    def get_access_token(self):
        if self.access_token is None:
            response = requests.post(
                self.access_token_url,
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"}
            )

            access_token = json.loads(response.content)["access_token"]
            self.access_token = access_token

        return self.access_token

    def send_graphql_query(self, query):
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}"
        }

        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers=headers,
            json={"query": query}
        )

        return response.json()

# Create an OAuth2 client
oauth2_client = OAuth2Client(
    client_id="9a80e66c-f50e-4bd1-9128-5760c7384f9d",
    client_secret="n8RTGEGFrbxGl4SxoNR4NjWBeje96QYap8TH12Jb",
    authorization_url="https://www.warcraftlogs.com/oauth/authorize",
    access_token_url="https://www.warcraftlogs.com/oauth/token"
)

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

# Get the top 100 priests
access_token = oauth2_client.get_access_token()
response = requests.post(GRAPHQL_ENDPOINT, headers={"Authorization": f"Bearer {access_token}"}, json={"query": GET_TOP_PRIESTS_QUERY})
top_priests_response = json.loads(response.content)


if 'data' in top_priests_response:
    world_data = top_priests_response['data']['worldData']
    encounter_data = world_data['encounter']
    character_rankings = encounter_data['characterRankings']
    priest_rankings = character_rankings['rankings']

    player_data = []

    for entry in priest_rankings:
        # Process each priest in some way, extracting required information
        code = entry["report"]["code"]
        fight_id = entry["report"]["fightID"]
        name = entry["name"]

        # Get the source ID for the player
        source_id = get_source_id(code, fight_id, access_token, name)

        # Add the player data to the list
        player_data.append({
            "code": code,
            "fight_id": fight_id,
            "name": name,
            "source_id": source_id
        })

    # Match the name and sourceID for each player
    for entry in player_data:
        name, source_id = get_source_id(entry["code"], entry["fight_id"], access_token, entry["name"])

        if name is not None and source_id is not None:
            entry["source_id"] = source_id
        else:
            # Handle cases where the name or source ID is not found
            print(f"Failed to retrieve source ID for {entry['code']}")

    # Export the player data to a CSV file for each player
    for entry in player_data:
        export_player_data(entry["fight_id"], entry["code"], entry["source_id"], access_token)