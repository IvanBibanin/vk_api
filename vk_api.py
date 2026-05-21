from __future__ import annotations

import traceback
from typing import Any

import pandas as pd
import requests


class Vk:
    def __init__(self, token: str = ""):
        self.token = token
        self.df_origin = pd.DataFrame()
        self.campaigns_data: dict[str, Any] = {}
        self.campaigns_name_data: dict[str, Any] = {}

    def _handle_response(self, response: requests.Response, success_message: str = ""):
        """Handle VK API HTTP responses."""
        if response.status_code in (200, 201, 204):
            if success_message:
                print(success_message)

            if not response.text:
                return {}

            try:
                return response.json()
            except ValueError:
                print("API returned a non-JSON response")
                print(response.text[:300])
                return None

        if response.status_code == 401:
            print("Authorization error: invalid token")
        elif response.status_code == 404:
            print("API method was not found")
        elif 400 <= response.status_code < 500:
            print(f"Request error: {response.status_code}")
        elif response.status_code >= 500:
            print("Internal server error")
        else:
            print(f"Unexpected API status: {response.status_code}")

        if response.text:
            print(response.text[:300])

        return None

    def _request_json(self, method: str, url: str, success_message: str = "", **kwargs):
        """Make one request to VK API and return JSON or None on error."""
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            return self._handle_response(response, success_message)
        except requests.exceptions.Timeout:
            print("API request timed out")
        except requests.exceptions.RequestException as error:
            print(f"Network request error: {error}")
        except Exception:
            print(traceback.format_exc())

        return None

    def _request_all_items(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        limit: int = 100,
    ):
        """Load all paginated API items using limit and offset."""
        all_items = []
        offset = 0
        total_count = None

        while True:
            page_params = dict(params or {})
            page_params["limit"] = limit
            page_params["offset"] = offset

            data = self._request_json(
                "get",
                url,
                headers=headers,
                params=page_params,
            )

            if data is None:
                return None

            items = data.get("items", [])
            total_count = data.get("count", total_count)

            if not items:
                break

            all_items.extend(items)
            offset += len(items)

            if total_count is not None and offset >= total_count:
                break

            if len(items) < limit:
                break

        return {
            "count": len(all_items),
            "items": all_items,
        }

    def to_dataframe(self, data: dict[str, Any]) -> pd.DataFrame:
        if not data or "items" not in data:
            self.df_origin = pd.DataFrame()
            return self.df_origin

        if data["items"] and "rows" in data["items"][0]:
            self.df_origin = pd.json_normalize(
                data["items"],
                record_path="rows",
                meta=["id"],
                sep="_",
            )
        else:
            self.df_origin = pd.json_normalize(
                data["items"],
                sep="_",
            )

        return self.df_origin

    def get_campaigns_name(self, limit: int = 100) -> pd.DataFrame | None:
        url = "https://ads.vk.com/api/v2/ad_plans.json"
        headers = {"Authorization": f"Bearer {self.token}"}

        data = self._request_all_items(
            url,
            headers=headers,
            limit=limit,
        )

        if data is None:
            return None

        self.campaigns_name_data = data
        return self.to_dataframe(data)

    def get_campaigns(
        self,
        type_object: str = "ad_plans",
        metriks: list[str] | str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> pd.DataFrame | None:
        url = f"https://ads.vk.com/api/v2/statistics/{type_object}/day.json"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "metrics": "all",
            "attribution": "conversion",
            "date_from": date_from,
            "date_to": date_to,
        }

        data = self._request_json(
            "get",
            url,
            headers=headers,
            params=params,
        )

        if data is None:
            return None

        self.campaigns_data = data
        df = self.to_dataframe(data)

        if metriks is None:
            return df

        if isinstance(metriks, str):
            metriks = [metriks]

        missing_columns = [column for column in metriks if column not in df.columns]

        if missing_columns:
            print("Missing columns:")
            print(missing_columns)
            print("Available columns:")
            print(df.columns.tolist())
            return df

        return df[metriks]
