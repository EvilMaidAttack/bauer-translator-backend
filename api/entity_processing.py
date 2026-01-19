import json
import pandas as pd
from pathlib import Path
import logging
logging.basicConfig(level=logging.INFO)

pd.set_option('display.max_columns', 1000)

class EntityProcessor:
    ENTITY_COLUMNS = ["text", "type", "entityId", "confidenceScore"]

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.df: pd.DataFrame = pd.DataFrame(columns=self.ENTITY_COLUMNS)

    # ---------- Loading ----------

    def load(self) -> "EntityProcessor":
        logging.info(f"Loading entities from {self.path}")
        try:
            with self.path.open(encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error("Failed to load JSON from %s: %s", self.path, e)
            self._empty()
            return self

        return self.load_from_dict(data)

    
    def load_from_dict(self, data: dict) -> "EntityProcessor":
        """
        Load entities from already parsed JSON dict.
        """
        entities = data.get("entities")

        if not isinstance(entities, list):
            logging.warning("No entities list found in JSON.")
            self._empty()
            return self

        entities = [e for e in entities if isinstance(e, dict)]

        if not entities:
            logging.warning("Entities list is empty or contains no valid entities.")
            self._empty()
            return self

        df = pd.DataFrame(entities)

        for col in self.ENTITY_COLUMNS:
            if col not in df:
                df[col] = pd.NA

        self.df = df[self.ENTITY_COLUMNS]
        return self

    
    def aggregate_entity_ids_by_text(self) -> pd.DataFrame:
        """
        Aggregates entityIds by text, joining multiple IDs with a comma. Returns a new DataFrame of columns: text, type, entityIds, confidenceScore (mean).
        """
        if self.df.empty:
            logging.warning("aggregate_entity_ids_by_text called on empty DataFrame")
            return pd.DataFrame(
            columns=["text", "type", "entityId", "confidenceScore"]
            )

        aggregated = self.df.groupby(["text", "type"]).agg({
            "entityId": lambda ids: ",".join(sorted(set(ids.dropna().astype(str)))),
            "confidenceScore": "mean"}).reset_index()
        logging.info("Aggregated entityIds by text, resulting in %d unique texts", len(aggregated))
        return aggregated
    
    def assign_unique_entity_ids(self) -> "EntityProcessor":
        """
        Adds a stable uniqueEntityId column based on (text, type).
        Same text+type will always receive the same ID.
        """
        if self.df.empty:
            logging.warning("assign_unique_entity_ids called on empty DataFrame")
            self.df["uniqueEntityId"] = pd.Series(dtype="string")
            return self

        # Reihenfolge beibehalten → cumcount wäre falsch!
        keys = self.df[["text", "type"]].astype(str)

        # eindeutige Gruppen in Erscheinungs-Reihenfolge
        unique_keys = (
            keys.drop_duplicates()
            .reset_index(drop=True)
        )

        # Zähler pro Typ (PERSON, ORGANIZATION, ...)
        counters = {}

        def make_id(row):
            entity_type = row["type"].upper()
            counters.setdefault(entity_type, 0)
            counters[entity_type] += 1
            return f"[{entity_type}-{counters[entity_type]}]"

        unique_keys["uniqueEntityId"] = unique_keys.apply(make_id, axis=1)

        # Mapping zurück auf das Original-DF
        mapping = {
            (row.text, row.type): row.uniqueEntityId
            for row in unique_keys.itertuples()
        }

        self.df["uniqueEntityId"] = [
            mapping[(t, ty)] for t, ty in zip(self.df["text"], self.df["type"])
        ]

        logging.info("Assigned uniqueEntityId to %d entities", len(self.df))

        return self
    
    def filter_by_type(self, entity_type: str) -> "EntityProcessor":
        if not self.df.empty:
            self.df = self.df[self.df["type"] == entity_type]
        return self

    def filter_by_confidence(self, min_score: float) -> "EntityProcessor":
        if not self.df.empty:
            self.df = self.df[self.df["confidenceScore"] >= min_score]
        return self
    
    def _empty(self):
        self.df = pd.DataFrame(columns=self.ENTITY_COLUMNS)

# df = (
#     EntityProcessor("api/utils/The_King’s_Challenge.result.json")
#     .load()
#     .aggregate_entity_ids_by_text()
#     )

# print(df.head(10))



