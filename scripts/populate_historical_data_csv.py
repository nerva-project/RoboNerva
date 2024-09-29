"""
populate_historical_data_csv.py

This script is used to populate the historical price data for Nerva (XNV) cryptocurrency.
The data is fetched from a CSV file and stored in the MongoDB database.
Do not use this script unless asked to do so by the project developer.

Copyright (c) 2024 Sayan "Sn1F3rt" Bhattacharyya, The Nerva Project
"""

import asyncio
import logging
from datetime import timedelta

import aiocsv
import aiofiles
import motor.motor_asyncio
from dateutil import parser

from config import MONGODB_URI, MONGODB_DATABASE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="../logs/populate_historical_data_csv.log",
    filemode="w",
)

DATA_FILE_NAME = "data.csv"  # The CSV file containing the historical price data
COLLECTION_NAME = (
    "xnv_historical_price_data"  # The name of the collection in the database
)


async def setup_database() -> motor.motor_asyncio.AsyncIOMotorClient:
    return motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)


async def main():
    client = await setup_database()
    db = client.get_database(MONGODB_DATABASE)
    collection = db[COLLECTION_NAME]

    async with aiofiles.open("data.csv", mode="r") as f:
        async for row in aiocsv.AsyncDictReader(f):
            try:
                date = parser.parse(row["snapped_at"])
                opening_price = float(row["price"])
                volume = float(row["total_volume"])

                await collection.insert_one(
                    {
                        "_id": date.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        ),
                        "opening": round(opening_price, 4),
                        "closing": None,
                        "high": None,
                        "low": None,
                        "volume": round(volume, 2),
                    }
                )

                logging.info(f"Inserted data for {date.strftime('%Y-%m-%d')}")

                if (
                    await collection.find_one({"_id": date - timedelta(days=1)})
                    is not None
                ):
                    await collection.update_one(
                        {"_id": date - timedelta(days=1)},
                        {"$set": {"closing": round(opening_price, 4)}},
                    )

                    logging.info(
                        f"Updated closing price for {date.strftime('%Y-%m-%d')}"
                    )

            except Exception as e:
                logging.info(e.__str__() + " - " + date.strftime("%Y-%m-%d"))


if __name__ == "__main__":
    asyncio.run(main())
