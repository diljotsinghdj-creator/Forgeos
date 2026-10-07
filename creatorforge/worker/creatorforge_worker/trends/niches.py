"""Niche definitions: which communities, news searches and YouTube categories feed each niche.
Every source is free; YouTube needs a free API key (CF_YOUTUBE_API_KEY), the rest need none."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Niche:
    id: str
    name: str
    subreddits: tuple[str, ...] = ()
    news_query: str = ""  # empty -> top stories
    hn_query: str | None = None  # None -> skip Hacker News for this niche
    youtube_category: str = ""  # YouTube videoCategoryId for the most-popular chart
    youtube_query: str = ""  # used for month/year (most viewed uploads matching this query)
    wikipedia: bool = False  # Wikipedia's most-read list is general, so only some niches use it
    keywords: tuple[str, ...] = field(default=())  # filters general lists (Wikipedia, Google Trends) for this niche


NICHES: dict[str, Niche] = {n.id: n for n in [
    Niche("all", "Everything", ("popular",), "", "", "", "", True),
    Niche("tech", "Tech & Gadgets", ("technology", "gadgets", "Futurology"), "technology", "", "28", "tech news"),
    Niche("ai", "AI", ("artificial", "OpenAI", "singularity", "LocalLLaMA"), "artificial intelligence", "AI", "28",
          "artificial intelligence",
          keywords=("ai", "artificial", "openai", "chatgpt", "gemini", "claude", "llm", "robot", "nvidia")),
    Niche("money", "Money & Finance", ("personalfinance", "investing", "stocks", "Economics"),
          "economy OR stock market OR inflation", None, "", "personal finance",
          keywords=("stock", "market", "economy", "inflation", "bank", "tax", "price", "dollar", "pound")),
    Niche("business", "Business & Side Hustles", ("Entrepreneur", "sidehustle", "smallbusiness", "startups"),
          "business", "startup", "", "side hustle"),
    Niche("crypto", "Crypto", ("CryptoCurrency", "Bitcoin", "ethereum"), "crypto OR bitcoin", "crypto", "", "bitcoin",
          keywords=("bitcoin", "crypto", "ethereum", "coin", "blockchain")),
    Niche("science", "Science & Space", ("science", "space", "Physics", "EarthPorn"), "science OR space OR NASA", "",
          "28", "science explained",
          keywords=("nasa", "space", "planet", "science", "species", "comet", "asteroid", "moon", "mars")),
    Niche("history", "History", ("history", "AskHistorians", "ArtefactPorn", "HistoryPorn"),
          "history OR archaeology OR ancient", None, "27", "history documentary", True,
          keywords=("history", "ancient", "war", "empire", "king", "queen", "battle", "century", "dynasty")),
    Niche("mystery", "Mystery & True Crime", ("UnresolvedMysteries", "TrueCrime", "RBI", "Paranormal"),
          "mystery OR unsolved OR investigation", None, "", "unsolved mystery", True,
          keywords=("murder", "case", "missing", "killer", "mystery", "trial", "crime")),
    Niche("facts", "Facts & Curiosities", ("todayilearned", "interestingasfuck", "Damnthatsinteresting",
                                           "coolguides"), "", None, "27", "facts you didn't know"),
    Niche("motivation", "Motivation & Self-improvement", ("getdisciplined", "selfimprovement", "GetMotivated",
                                                         "productivity"), "productivity OR motivation", None, "26",
          "motivation"),
    Niche("health", "Health & Fitness", ("Fitness", "nutrition", "loseit", "running"), "health OR fitness OR diet",
          None, "26", "fitness tips"),
    Niche("gaming", "Gaming", ("gaming", "Games", "pcgaming", "NintendoSwitch"), "video games", "game", "20", "gaming"),
    Niche("entertainment", "Movies, TV & Music", ("movies", "television", "Music", "popculturechat"),
          "film OR TV series OR album", None, "24", "trailer", True),
    Niche("sports", "Sports", ("sports", "soccer", "nba", "formula1"), "sport", None, "17", "highlights", True,
          keywords=("fc", "football", "league", "cup", "championship", "grand prix", "nba", "nfl", "season")),
    Niche("custom", "My keyword", ()),
]}

# Google News edition + YouTube region per country.
REGIONS: dict[str, dict[str, str]] = {
    "GB": {"name": "United Kingdom", "hl": "en-GB", "ceid": "GB:en", "wiki": "en.wikipedia"},
    "US": {"name": "United States", "hl": "en-US", "ceid": "US:en", "wiki": "en.wikipedia"},
    "IN": {"name": "India", "hl": "en-IN", "ceid": "IN:en", "wiki": "en.wikipedia"},
    "CA": {"name": "Canada", "hl": "en-CA", "ceid": "CA:en", "wiki": "en.wikipedia"},
    "AU": {"name": "Australia", "hl": "en-AU", "ceid": "AU:en", "wiki": "en.wikipedia"},
}
