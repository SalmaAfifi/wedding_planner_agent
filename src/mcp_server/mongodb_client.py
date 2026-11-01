import json
import logging
from typing import Annotated, Any, Union
from bson import ObjectId
from pydantic import BeforeValidator, Field, TypeAdapter
from pymongo import MongoClient

logger = logging.getLogger(__name__)

MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


def _to_month_int(v: Any) -> Any:
    if isinstance(v, str):
        cleaned = v.strip().lower()
        if cleaned.isdigit():
            return int(cleaned)
        if cleaned in MONTH_MAP:
            return MONTH_MAP[cleaned]
    return v


# Pydantic type validating and bounding month to 1 <= month <= 12
MonthType = Annotated[int, BeforeValidator(_to_month_int), Field(ge=1, le=12)]
_month_adapter = TypeAdapter(MonthType)


def parse_month(month: Union[int, str]) -> int:
    """Validate and normalize user month input to int (1-12) using Pydantic."""
    return _month_adapter.validate_python(month)


class MongoDBClient:
    """MongoDB Client for querying wedding venues and dates."""

    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "wedding_venues"):
        self.uri = uri
        self.db_name = db_name
        self.client = MongoClient(uri)
        self.db = self.client.get_database(db_name)
        self.venues = self.db.get_collection("venues")

    def get_venues_by_month_and_country(
        self,
        month: Union[int, str],
        country: str
    ) -> list[dict[str, Any]]:
        """
        Query venues in the specified country that have availability in the specified month.

        Preserves the document's original schema structure (including BSON Date / datetime objects
        and ObjectId for _id), while filtering available_dates to only include the dates of the
        requested month.

        :param month: Month as an integer (1-12) or string (e.g. '06', 'June', 'jun').
        :param country: Country name (case-insensitive regex match).
        :return: List of venue documents matching the schema with available_dates filtered for that month.
        """
        target_month = parse_month(month)
        country_clean = country.strip()

        # Case-insensitive match on country
        query = {"country": {"$regex": f"^{country_clean}$", "$options": "i"}}

        matching_venues = []
        try:
            cursor = self.venues.find(query)
            for doc in cursor:
                # Keep original datetime objects for the dates of this month
                month_dates = [
                    d
                    for d in doc.get("available_dates", [])
                    if d.month == target_month
                ]

                # Return only venues that have available dates in this month
                if month_dates:
                    venue_data = dict(doc)
                    venue_data["available_dates"] = month_dates
                    matching_venues.append(venue_data)

            return matching_venues

        except Exception as e:
            logger.error(f"Error querying venues for country={country}, month={month}: {e}")
            raise Exception(f"Unable to query venues due to error: {e}") from e

    def close(self):
        """Close the MongoDB client connection."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_venues_by_month_and_country(
    month: Union[int, str],
    country: str,
    uri: str = "mongodb://localhost:27017/",
    db_name: str = "wedding_venues"
) -> list[dict[str, Any]]:
    """Convenience function to query venues by month and country without manually instantiating MongoDBClient."""
    with MongoDBClient(uri=uri, db_name=db_name) as client:
        return client.get_venues_by_month_and_country(month=month, country=country)


if __name__ == "__main__":
    from bson.json_util import dumps
    # Example usage: Find venues in Greece available in February
    try:
        sample_venues = get_venues_by_month_and_country(month="February", country="Greece")
        print(f"Found {len(sample_venues)} venue(s) in Greece available in February:")
        # bson.json_util.dumps formats exact JSON Schema with {"$oid": "..."} and {"$date": "..."}
        print(dumps(sample_venues, indent=4))
    except Exception as err:
        print(f"Error: {err}")
