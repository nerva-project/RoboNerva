"""
populate_historical_data_manual.py

This script is used to populate the historical price data for Nerva (XNV) cryptocurrency.
The data is entered manually.
Do not use this script unless asked to do so by the project developer.

Copyright (c) 2024 Sayan "Sn1F3rt" Bhattacharyya, The Nerva Project
"""

import asyncio

import motor.motor_asyncio
from dateutil import parser

from config import MONGODB_URI, MONGODB_DATABASE


COLLECTION_NAME = (
    "xnv_historical_price_data"  # The name of the collection in the database
)


async def setup_database() -> motor.motor_asyncio.AsyncIOMotorClient:
    return motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)


async def main():
    client = await setup_database()
    db = client.get_database(MONGODB_DATABASE)
    collection = db[COLLECTION_NAME]

    date = parser.parse(input("Enter the date (YYYY-MM-DD): "))
    opening_price = input("Enter the opening price: ").strip() or None
    closing_price = input("Enter the closing price: ").strip() or None
    high_price = input("Enter the high price: ").strip() or None
    low_price = input("Enter the low price: ").strip() or None
    volume = input("Enter the volume: ").strip() or None

    try:
        if await collection.find_one({"_id": date}) is None:
            await collection.insert_one(
                {
                    "_id": date.replace(hour=0, minute=0, second=0, microsecond=0),
                    "opening": (
                        round(float(opening_price), 4) if opening_price else None
                    ),
                    "closing": (
                        round(float(closing_price), 4) if closing_price else None
                    ),
                    "high": round(float(high_price), 4) if high_price else None,
                    "low": round(float(low_price), 4) if low_price else None,
                    "volume": round(float(volume)) if volume else None,
                }
            )

            print(f"Inserted data for {date.strftime('%Y-%m-%d')}")

        else:
            data = await collection.find_one({"_id": date})

            await collection.update_one(
                {"_id": date},
                {
                    "$set": {
                        "opening": (
                            round(float(opening_price), 4)
                            if opening_price
                            else data.get("opening")
                        ),
                        "closing": (
                            round(float(closing_price), 4)
                            if closing_price
                            else data.get("closing")
                        ),
                        "high": (
                            round(float(high_price), 4)
                            if high_price
                            else data.get("high")
                        ),
                        "low": (
                            round(float(low_price), 4)
                            if low_price
                            else data.get("low")
                        ),
                        "volume": (
                            round(float(volume), 2) if volume else data.get("volume")
                        ),
                    }
                },
            )

            print(f"Updated data for {date.strftime('%Y-%m-%d')}")

    except Exception as e:
        print(e.__str__() + " - " + date.strftime("%Y-%m-%d"))


if __name__ == "__main__":
    asyncio.run(main())
