import logging
from typing import Any, Union
from bson.json_util import dumps
from mcp.server import MCPServer

from mcp_server.mongodb_client import get_venues_by_month_and_country

logger = logging.getLogger(__name__)

# Initialize MCPServer
mcp = MCPServer("Wedding Venue")


@mcp.tool()
def get_available_wedding_venues(
    country: str,
    month: Union[int, str]
) -> str:
    """
    Find available wedding venues for a given country and month.

    :param country: Country name to search in (e.g. 'Greece', 'Italy', 'France').
    :param month: Target month as an integer (1-12) or string (e.g. 'February', 'feb', '02').
    :return: JSON formatted string containing the list of matching venue documents.
    """
    logger.info(f"Fetching wedding venues for country='{country}', month='{month}'")
    venues = get_venues_by_month_and_country(month=month, country=country)
    return dumps(venues)


if __name__ == "__main__":
    mcp.run()
