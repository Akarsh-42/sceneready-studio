"""Typed boundaries for user input, model output, and source validation."""
from datetime import date
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator

Topic = Literal["location_access", "night_filming", "drone", "road_control", "stunts", "animals", "minors"]


class Brief(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=2, max_length=100)
    location: str = Field(default="", max_length=200)
    shoot_date: date | None = None
    crew_size: int = Field(default=6, ge=1, le=500)
    script: str = Field(min_length=30, max_length=12000)

    @field_validator("title", "city", "location", "script", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class Scene(BaseModel):
    id: str = Field(max_length=30)
    heading: str = Field(max_length=180)
    setting: Literal["interior", "exterior", "mixed", "unknown"]
    time_of_day: Literal["day", "night", "mixed", "unknown"]
    people: list[str] = Field(max_length=12)
    equipment: list[str] = Field(max_length=12)
    production_needs: list[str] = Field(max_length=12)
    script_excerpt: str = Field(max_length=400)


class Breakdown(BaseModel):
    summary: str = Field(max_length=800)
    scenes: list[Scene] = Field(min_length=1, max_length=8)
    research_topics: list[Topic] = Field(max_length=3)
    missing_details: list[str] = Field(max_length=10)


class Source(BaseModel):
    id: str
    title: str
    url: str
    domain: str
    government_domain: bool
    excerpts: list[str]
    retrieved_at: str
    query: str


class Citation(BaseModel):
    source_id: str = Field(max_length=30)
    quote: str = Field(min_length=20, max_length=240)


class ProposedTask(BaseModel):
    title: str = Field(max_length=160)
    scene_ids: list[str] = Field(max_length=8)
    department: Literal["Production", "Locations", "Camera", "Safety"]
    priority: Literal["high", "medium", "low"]
    action: str = Field(max_length=700)
    rationale: str = Field(max_length=500)
    citations: list[Citation] = Field(max_length=3)
    needs_verification: str = Field(max_length=500)


class Assessment(BaseModel):
    tasks: list[ProposedTask] = Field(min_length=1, max_length=8)
    questions: list[str] = Field(max_length=8)


def source_url(raw: str) -> tuple[str, str] | None:
    """Allow only ordinary web links; never accept model-authored URLs."""
    try:
        parts = urlsplit(raw)
        host = (parts.hostname or "").lower()
        if parts.scheme not in {"http", "https"} or not host or parts.username or parts.password:
            return None
        if any(ord(c) < 33 for c in raw) or host in {"localhost", "127.0.0.1", "::1"}:
            return None
        return raw, host
    except ValueError:
        return None


def government_domain(host: str) -> bool:
    return any(host == suffix or host.endswith("." + suffix)
               for suffix in ("gov.in", "nic.in", "gov", "gov.uk"))


def normalized(value: str) -> str:
    return " ".join(value.split())


def validate_report(assessment: Assessment, breakdown: Breakdown, sources: list[Source]) -> tuple[list[dict], list[str]]:
    """Match citations to retrieved excerpts. This does not prove a claim is true."""
    lookup = {source.id: source for source in sources}
    scene_ids = {scene.id for scene in breakdown.scenes}
    tasks, warnings = [], []
    for index, proposed in enumerate(assessment.tasks, 1):
        data = proposed.model_dump()
        accepted = []
        for citation in proposed.citations:
            source = lookup.get(citation.source_id)
            quote = normalized(citation.quote)
            if source and len(quote) >= 20 and any(quote in normalized(excerpt) for excerpt in source.excerpts):
                accepted.append({**citation.model_dump(), "url": source.url, "title": source.title})
            else:
                warnings.append(f"Task {index}: a citation did not match retrieved evidence and was removed.")
        if any(scene_id not in scene_ids for scene_id in data["scene_ids"]):
            warnings.append(f"Task {index}: an unknown scene reference was removed.")
        data.update(
            id=f"T{index:02d}",
            scene_ids=[item for item in data["scene_ids"] if item in scene_ids],
            citations=accepted,
            evidence_status="excerpt_matched" if accepted else "needs_evidence",
            review_status="open",
            review_note="",
        )
        tasks.append(data)
    return tasks, warnings
