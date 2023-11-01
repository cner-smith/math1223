import requests
import json
import csv

def match_name_and_source_id(player_data, source_id):
    """Matches the name of a player with their sourceID.

    Args:
        player_data: A list of player data, including the player's name, code, and fightID.
        source_id: The player's sourceID.

    Returns:
        The player's name.
    """

    for player in player_data:
        if player["name"] == source_id:
            return player["name"]

    return None

def export_player_data(fight_id, code, source_id):
    """Exports the player's data to a CSV file.

    Args:
        fight_id: The fightID of the encounter.
        code: The player's code.
        source_id: The player's sourceID.
    """

    access_token = OAuth2Client(
        client_id="9a80e66c-f50e-4bd1-9128-5760c7384f9d",
        client_secret="n8RTGEGFrbxGl4SxoNR4NjWBeje96QYap8TH12Jb",
        authorization_url="https://www.warcraftlogs.com/oauth/authorize",
        access_token_url="https://www.warcraftlogs.com/oauth/token"
    ).get_access_token()

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(
        GRAPHQL_ENDPOINT,
        headers=headers,
        json={"query": GET_PLAYER_DATA_QUERY.format(code=code, fightID=fight_id, sourceID=source_id)}
    )

    player_data = json.loads(response.content)["data"]["reportData"]["report"]["table"]

    with open(f"{code}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(player_data.keys())
        for row in player_data.values():
            writer.writerow(row)

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
query request {
   reportData {
         report(code:"{code}") {
            table(fightIDs:{fightID})
         }
      }
}
"""

GET_PLAYER_DATA_QUERY = """
query request {
   reportData {
         report(code:"{code}") {
            table(fightIDs:{fightID},sourceID:{sourceID})
         }
      }
}
"""

# Get the top 100 priests
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.post(GRAPHQL_ENDPOINT, headers=headers, json={"query": GET_TOP_PRIESTS_QUERY})
top_priests = json.loads(response.content)["data"]["worldData"]["encounter"]["characterRankings"]

# Create a list to store the player data
player_data = []

# Iterate over the top 100 priests and get the source ID for each one
for priest in top_priests[:100]:
    code = priest["code"]
    fight_id = priest["fightID"]
    name = priest["name"]

    # Get the source ID for the player
    response = requests.post(GRAPHQL_ENDPOINT, headers=headers, json={"query": GET_SOURCE_ID_QUERY.format(code=code, fightID=fight_id)})
    source_id = json.loads(response.content)["data"]["reportData"]["report"]["table"]["sourceID"]

    # Add the player data to the list
    player_data.append({
        "code": code,
        "fight_id": fight_id,
        "name": name,
        "source_id": source_id
    })

# Match the name and sourceID for each player
for player in player_data:
    source_id = match_name_and_source_id(player_data, player["code"])
    player["source_id"] = source_id

# Export the player data to a CSV file for each player
for player in player_data:
    export_player_data(player["fight_id"], player["code"], player["source_id"])
