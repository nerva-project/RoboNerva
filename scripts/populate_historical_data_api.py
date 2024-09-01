"""
populate_historical_data_api.py

This script is used to populate the historical price data for the past 365 days for Nerva (XNV) cryptocurrency.
The data is fetched from the CoinGecko API and stored in the MongoDB database.
Do not use this script unless asked to do so by the project developer.

Copyright (c) 2024 Sayan "Sn1F3rt" Bhattacharyya, The Nerva Project
"""

import asyncio
import logging
from datetime import datetime, timedelta, UTC

import aiohttp
import motor.motor_asyncio

from config import MONGODB_URI, COINGECKO_API_KEY, MONGODB_DATABASE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="../logs/populate_historical_data_api.log",
    filemode="w",
)


COLLECTION_NAME = (
    "xnv_historical_price_data"  # The name of the collection in the database
)


async def setup_database() -> motor.motor_asyncio.AsyncIOMotorClient:
    return motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)


async def main():
    client = await setup_database()
    db = client.get_database(MONGODB_DATABASE)
    collection = db[COLLECTION_NAME]

    for i in range(1, 365):
        yesterday_date = datetime.now(UTC) - timedelta(days=i)

        start_timestamp = int(
            yesterday_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            ).timestamp()
        )
        end_timestamp = int(
            (yesterday_date + timedelta(days=1))
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .timestamp()
        )

        headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
        params = {"vs_currency": "usd", "from": start_timestamp, "to": end_timestamp}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.coingecko.com/api/v3/coins/nerva/market_chart/range",
                    params=params,
                    headers=headers,
                ) as res:
                    data = await res.json()

                    prices = data["prices"]
                    volumes = data["total_volumes"]

                    opening_price = prices[0][1]
                    closing_price = prices[-1][1]
                    high_price = max([price[1] for price in prices])
                    low_price = min([price[1] for price in prices])
                    volume = volumes[0][1]

                    await collection.insert_one(
                        {
                            "_id": yesterday_date.replace(
                                hour=0, minute=0, second=0, microsecond=0
                            ),
                            "opening": round(opening_price, 4),
                            "closing": round(closing_price, 4),
                            "high": round(high_price, 4),
                            "low": round(low_price, 4),
                            "volume": round(volume, 2),
                        }
                    )

                    logging.info(
                        f"Inserted data for {yesterday_date.strftime('%Y-%m-%d')}"
                    )

        except Exception as e:
            _ = e

            logging.info("Rate limited, waiting for 60 seconds...")
            await asyncio.sleep(60)

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://api.coingecko.com/api/v3/coins/nerva/market_chart/range",
                        params=params,
                        headers=headers,
                    ) as res:
                        data = await res.json()

                        prices = data["prices"]
                        volumes = data["total_volumes"]

                        opening_price = prices[0][1]
                        closing_price = prices[-1][1]
                        high_price = max([price[1] for price in prices])
                        low_price = min([price[1] for price in prices])
                        volume = volumes[0][1]

                        await collection.insert_one(
                            {
                                "_id": yesterday_date.replace(
                                    hour=0, minute=0, second=0, microsecond=0
                                ),
                                "opening": round(opening_price, 4),
                                "closing": round(closing_price, 4),
                                "high": round(high_price, 4),
                                "low": round(low_price, 4),
                                "volume": round(volume, 2),
                            }
                        )

                        logging.info(
                            f"Inserted data for {yesterday_date.strftime('%Y-%m-%d')}"
                        )

            except Exception as e:
                logging.info(
                    e.__str__() + " - " + yesterday_date.strftime("%Y-%m-%d")
                )

            continue


if __name__ == "__main__":
    asyncio.run(main())
