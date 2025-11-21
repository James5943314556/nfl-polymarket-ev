import httpx
from typing import List, Dict, Any, Optional
from backend.markets.config import NFL_TAG_ID


BASE_URL = "https://gamma-api.polymarket.com"


class GammaClient:
    """
    Thin, doc-aligned wrapper for the Polymarket Gamma API.

    Key points (from official docs and public SDKs):

      - /sports:
          GET https://gamma-api.polymarket.com/sports
          -> [
                {
                  "sport": "<string>",
                  "image": "<string>",
                  "resolution": "<string>",
                  "ordering": "<string>",
                  "tags": "<string>",  # comma-separated tag IDs
                  "series": "<string>"
                },
             ]

      - /tags:
          GET https://gamma-api.polymarket.com/tags
          -> [{ "id": "<string>", "label": "<string>", "slug": "<string>", ... }, ...]

      - /events:
          GET https://gamma-api.polymarket.com/events
          Query params (subset):
            - active: bool
            - closed: bool
            - archived: bool
            - limit, offset
            - id, slug
            - tag, tag_id, tag_slug, related_tags, ...

      - /markets:
          GET https://gamma-api.polymarket.com/markets
          Query params (subset):
            - active, closed, archived
            - limit, offset
            - id, slug
            - tag_id, related_tags, condition_ids, ...
    """

    def __init__(self, base_url: str = BASE_URL, timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout

    # ----------------------------------------------------------
    # Low-level GET wrapper
    # ----------------------------------------------------------
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            return r.json()

    # ----------------------------------------------------------
    # SPORTS
    # ----------------------------------------------------------
    def get_sports(self) -> List[Dict[str, Any]]:
        data = self._get("/sports")
        if isinstance(data, list):
            return data
        return data

    def find_sports(self, term: str) -> List[Dict[str, Any]]:
        term = term.lower()
        sports = self.get_sports()
        return [s for s in sports if term in (s.get("sport") or "").lower()]

    def extract_sport_tag_ids(self, sport_obj: Dict[str, Any]) -> List[str]:
        tags_field = sport_obj.get("tags") or ""
        if not isinstance(tags_field, str):
            return []
        return [t.strip() for t in tags_field.split(",") if t.strip()]

    # ----------------------------------------------------------
    # TAGS
    # ----------------------------------------------------------
    def get_tags(self, limit: int = 200, offset: int = 0) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        data = self._get("/tags", params=params)
        if isinstance(data, list):
            return data
        return data.get("tags", [])

    def find_tags(self, term: str, limit: int = 500) -> List[Dict[str, Any]]:
        term = term.lower()
        tags = self.get_tags(limit=limit, offset=0)
        results = []
        for t in tags:
            label = (t.get("label") or "").lower()
            slug = (t.get("slug") or "").lower()
            if term in label or term in slug:
                results.append(t)
        return results

    # ----------------------------------------------------------
    # EVENTS
    # ----------------------------------------------------------
    def get_events(
        self,
        active: Optional[bool] = None,
        closed: Optional[bool] = None,
        archived: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
        tag: Optional[str] = None,
        tag_id: Optional[str] = None,
        tag_slug: Optional[str] = None,
        related_tags: Optional[str] = None,
        slug: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        if active is not None:
            params["active"] = active
        if closed is not None:
            params["closed"] = closed
        if archived is not None:
            params["archived"] = archived

        if tag is not None:
            params["tag"] = tag
        if tag_id is not None:
            params["tag_id"] = tag_id
        if tag_slug is not None:
            params["tag_slug"] = tag_slug
        if related_tags is not None:
            params["related_tags"] = related_tags

        if slug is not None:
            params["slug"] = slug
        if event_id is not None:
            params["id"] = event_id

        data = self._get("/events", params=params)
        if isinstance(data, list):
            return data
        return data.get("events", [])

    # ----------------------------------------------------------
    # MARKETS
    # ----------------------------------------------------------
    def get_markets(
        self,
        active: Optional[bool] = None,
        closed: Optional[bool] = None,
        archived: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
        tag_id: Optional[str] = None,
        slug: Optional[str] = None,
        market_id: Optional[str] = None,
        condition_ids: Optional[str] = None,
        related_tags: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        if active is not None:
            params["active"] = active
        if closed is not None:
            params["closed"] = closed
        if archived is not None:
            params["archived"] = archived

        if tag_id is not None:
            params["tag_id"] = tag_id
        if slug is not None:
            params["slug"] = slug
        if market_id is not None:
            params["id"] = market_id
        if condition_ids is not None:
            params["condition_ids"] = condition_ids
        if related_tags is not None:
            params["related_tags"] = related_tags

        data = self._get("/markets", params=params)
        if isinstance(data, list):
            return data
        return data.get("markets", [])

    # ----------------------------------------------------------
    # FILTERING HELPERS
    # ----------------------------------------------------------
    @staticmethod
    def filter_moneyline_markets(markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for m in markets:
            q = (m.get("question") or m.get("title") or "").lower()
            if "moneyline" in q or "who will win" in q or "wins?" in q or "winner" in q:
                results.append(m)
        return results

    # ----------------------------------------------------------
    # NFL-specific helpers using NFL_TAG_ID = "450"
    # ----------------------------------------------------------
    def get_nfl_events(
        self,
        active: Optional[bool] = True,
        closed: Optional[bool] = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        return self.get_events(
            active=active,
            closed=closed,
            limit=limit,
            offset=offset,
            tag_id=NFL_TAG_ID,
        )

    def get_nfl_moneyline_markets(
        self,
        active: Optional[bool] = True,
        closed: Optional[bool] = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        events = self.get_nfl_events(
            active=active,
            closed=closed,
            limit=limit,
            offset=offset,
        )
        results = []

        for ev in events:
            eid = ev.get("id")
            markets = self.get_markets(
                active=active,
                closed=closed,
                limit=limit,
                offset=0,
                tag_id=NFL_TAG_ID,
            )
            moneylines = self.filter_moneyline_markets(markets)
            if moneylines:
                results.append({"event": ev, "moneyline_markets": moneylines})

        return results

    # ----------------------------------------------------------
    # EVENT BY SLUG (one specific game)
    # ----------------------------------------------------------
    def get_event_by_slug(self, slug: str) -> Dict[str, Any]:
        """
        Fetch a single event by its slug, e.g.
        slug = "nfl-buf-hou-2025-11-20"
        """
        return self._get(f"/events/slug/{slug}")
