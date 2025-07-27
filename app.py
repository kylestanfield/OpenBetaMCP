import requests
import json
from mcp.server.fastmcp import FastMCP
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import logging


logging.basicConfig(level=logging.INFO)

mcp = FastMCP("openbeta")

endpoint = 'https://stg-api.openbeta.io'
headers = {
        'Content-Type': 'application/json'
    }
# Select your transport with a defined url endpoint
transport = RequestsHTTPTransport(
    url=endpoint,
    headers=headers,
    use_json=True,
)

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

areaQuery = """
query {
    areas(filter: {area_name: {match: "Grotto, The"}}) {
        area_name
        climbs {
            name
        }
        children {
            area_name
            metadata {
                lat
                lng
            }
        }
    }
}
"""

nearMeQuery = """
query {
    cragsNear(
        lnglat: {
            lat:37.75
            lng: 122.45
        },
        maxDistance: 50000
    ) {
        crags {
            area_name
        }
    }
}
"""
# helper function to make request/query to openbeta graphQL DB
def make_request(query):
    json_payload = {'query': query}

    
    try:
        response = requests.post(endpoint, json=json_payload, headers=headers)
        response.raise_for_status()

        return json.dumps(response.json(), indent=2)
    except requests.exceptions.RequestException as e:
        print('An error occurred: ', e)
        return None

@mcp.tool()
def get_crags_near_location(lat: float, lng: float, maxDistance: int):
    """Get rock climbing crags near GPS coordinates.
    
    Args:
        lat: float value for lattitude
        lng: float value for longitude
        maxDistance: radius in meters to find crags within
    """
    data = """query {{
                    cragsNear(
                        lnglat: {{
                            lat: {lat}
                            lng: {lng}
                        }},
                        maxDistance: {maxDistance}
                        includeCrags: true
                    ) {{
                        crags {{
                            area_name
                        }}
                    }}
                }}""".format(lat=lat, lng=lng, maxDistance=maxDistance)
    query = gql(data)
    try:
        result = client.execute(query)

        # Check for GraphQL errors in the response itself
        if 'errors' in result:
            error_messages = [err['message'] for err in result['errors']]
            return f"GraphQL API Error: {'; '.join(error_messages)}"
        
        # If no errors, return the data
        #print(result)
        return json.dumps(result, indent=2)
    except Exception as e:
        # Catch any network or client-side exceptions
        return f"An error occurred during GraphQL execution: {str(e)}"

if __name__ == '__main__':
    mcp.run(transport='stdio')
