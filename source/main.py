import requests
import pandas as pd

# Replace 'YOUR_ACCESS_TOKEN', 'BOSS_ID', and 'DIFFICULTY' with your data
access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5YTgwZTY2Yy1mNTBlLTRiZDEtOTEyOC01NzYwYzczODRmOWQiLCJqdGkiOiI5OTliMGNlM2VmZjlmMmY0MjgyN2JlMWNlM2IzYjI0YWIyZTdmNTA0MDExMGQ2ZTJlYTY2YjZiZjRkMzg1MTViYWJiYzMyZjBlMGZkNjNmMyIsImlhdCI6MTY5ODc4NjE2OS4yOTA1NTksIm5iZiI6MTY5ODc4NjE2OS4yOTA1NjEsImV4cCI6MTcyOTg5MDE2OS4yNTYyNzUsInN1YiI6IjI5MTk2NSIsInNjb3BlcyI6WyJ2aWV3LXVzZXItcHJvZmlsZSIsInZpZXctcHJpdmF0ZS1yZXBvcnRzIl19.rHM4eYRNK-Rc0c3igWHv0rP7F4m5Q0mfUk8txtvjwWLKh7obK_g73NmfaBkfQJP2ffQTb37wHlgvoVFc_LxcdK7iUyxQjW1sQqlFBwD709bzH_h2SPyadZZH1fwpXCW9VQ3wtWA_LAAr4Wb-xlasYSH_z9-ZKUEfkfWZklD3nUOpcjeebbgeNB4rdeDniDKGM0yTth7WsKzyEtNZeJJaZQFwgp61FrCiYDjbNcdqpon58Kb8Hi9NDAofwJ0CmS4BtCbdBISWzStclwdKJJkesxw0Iysrn7_qPvAf9kQ16yjwnrE1BaavPrc0tI_8pAuJUmX_2nxWP79Ygwh-znokyMMXyFofkyE3oQtrxiCnIzOsF54FfIAwN-mgL0xewjWghzQ_ZWg1nAuj59xxkglShPx0EYfgSFvjU12ktlVuOHWn7NNLMKBtcaHl91w3TwWyDFeCu7wHDODSoViFF5x5g2bbWPZXsLd1XsZ4jfO_QfHTfgG5BCRQxyTT8sFs7OBlPF0rKRiC_rKO-TDhgsuANlCJ2tUXLmBie6jZ6ZwDnkMM5BEPqHi0nxdq6ZjwRVPZUwexv3vC-V4tqdFSgDznoltVjb-3yTvzs7BnL6ks0sSLHbB__tITi-yHVupFgZBv7hsjoyqjZ9HpY6et8lT8dKnPBtBDphfA-MpLAW63c-E'
boss_id = '2685'  # The ID of the boss you're interested in
difficulty = 'mythic'  # Specify difficulty (e.g., 'normal', 'heroic', 'mythic')

# URL for fetching reports
url = f'https://www.warcraftlogs.com:443/v1/reports/guild/GUILD_NAME/Boss/{boss_id}?api_key={access_token}&difficulty={difficulty}'

# Make a GET request to the API
response = requests.get(url)

if response.status_code == 200:  # Check if the request was successful
    reports_data = response.json()  # Parse JSON data

    # Extract the top 100 holy priests from the reports (assuming 'class' represents the class information)
    holy_priests = [report for report in reports_data if report['spec'] == 'Holy Priest'][:100]

    # Iterate over the top 100 holy priests' reports
    for priest in holy_priests:
        report_id = priest['id']  # Extract the report ID

        # Make a request to fetch detailed information for the report
        report_url = f'https://www.warcraftlogs.com:443/v1/report/fights/{report_id}?api_key={access_token}'
        report_response = requests.get(report_url)

        if report_response.status_code == 200:
            detailed_report_data = report_response.json()

            # Extracting summary data of character, gear, stats, talents, etc.
            character_summary = detailed_report_data.get('friendlies')
            healing_summary = detailed_report_data.get('healing')
            healing_breakdown = detailed_report_data.get('phases')  # Check the specific structure for spell breakdown

            # Create a Pandas DataFrame for character summary data
            character_df = pd.DataFrame(character_summary)
            
            # Create a separate sheet for character summary in the CSV file
            character_filename = f"{priest['name']}_character_summary.csv"
            character_df.to_csv(character_filename, index=False)
            
            # Create a Pandas DataFrame for overall healing summary data
            healing_df = pd.DataFrame(healing_summary)
            
            # Create a separate sheet for overall healing summary in the CSV file
            healing_filename = f"{priest['name']}_healing_summary.csv"
            healing_df.to_csv(healing_filename, index=False)
            
            # Create a Pandas DataFrame for healing breakdown data
            breakdown_df = pd.DataFrame(healing_breakdown)  # Adjust this based on the actual breakdown structure
            
            # Create a separate sheet for healing breakdown in the CSV file
            breakdown_filename = f"{priest['name']}_healing_breakdown.csv"
            breakdown_df.to_csv(breakdown_filename, index=False)
        else:
            print(f"Failed to fetch data for priest: {priest['name']}. Status code:", report_response.status_code)
else:
    print("Failed to fetch data from the API. Status code:", response.status_code)