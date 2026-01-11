# Legal Compliance Summary

## Decision: nba_api Removal

**Date:** January 10, 2026  
**Status:** ✅ COMPLETED

### Issue Identified

The `nba_api` library (https://github.com/swar/nba_api) scrapes NBA.com public endpoints, which is governed by **NBA.com Terms of Service Section 9**.

### NBA.com ToS Section 9 Restrictions

NBA Statistics may only be used for:
- "Legitimate news reporting or private, non-commercial purposes"
- With prominent attribution to NBA.com

**Prohibited uses:**
1. ❌ Any gambling activity (including legal gambling)
2. ❌ Any fantasy game or other commercial product or service
3. ❌ Creating database of comprehensive, regularly updated statistics without express consent
4. ❌ Any use without prominent NBA.com attribution

### Why LineLogic Cannot Use nba_api

- **Gambling analysis:** Paper trading and backtesting constitute gambling activity analysis
- **Database creation:** Storing comprehensive NBA stats violates ToS
- **Commercial intent:** Even non-profit projects with commercial potential are restricted
- **Legal risk:** NBA actively enforces ToS, risk of legal action and IP bans

### Actions Taken

1. ❌ **REMOVED:** `src/linelogic/data/providers/nba_api_provider.py`
2. ❌ **REMOVED:** `USE_NBA_API` config flag from `settings.py`
3. ❌ **REMOVED:** `nba-api` optional dependency from `pyproject.toml`
4. ❌ **REMOVED:** nba_api references from CLI, README, tests
5. ✅ **UPDATED:** Documentation with comprehensive legal analysis
6. ✅ **ADDED:** Free, legal alternatives for all sports

### Replacement Strategy

#### M0 (POC - Current)
- **BALLDONTLIE Free Tier:** 5 rpm, players/teams/games only
- **Cost:** $0/mo
- **Limitation:** No player stats (can't build models yet)

#### M1 (Modeling Phase - Required)
- **BALLDONTLIE All-Star:** $5/mo, 30 rpm, player game logs
- **The Odds API Basic:** $20/mo for odds data
- **Cost:** $25/mo
- **Milestone:** Required to build prop models

#### M2 (Multi-Sport Expansion)
- **BALLDONTLIE All-Star:** $5/mo (NBA)
- **The Odds API Pro:** $50/mo (multi-sport odds)
- **nflverse:** Free (NFL historical, open source)
- **Retrosheet/Chadwick:** Free (MLB historical, open source)
- **WeatherAPI:** Free (outdoor sports)
- **Cost:** $55/mo

#### M3 (Social/News Signals)
- Add Twitter API ($100/mo) and NewsAPI ($50/mo)
- **Cost:** $119-219/mo

#### M4 (Licensed Production Feeds)
- **Sportradar/Genius Sports:** $3,000-5,000/mo
- Only when revenue justifies (>$10k/mo)
- **Cost:** $3,204/mo

### Legal Compliance for Other Sports

#### ✅ APPROVED
- **BALLDONTLIE** - Primary NBA source (legal, community-run)
- **TheSportsDB** - Multi-sport fallback (non-commercial OK)
- **nflverse** - NFL historical (open source, permissive license)
- **Retrosheet/Chadwick** - MLB historical (explicitly free/open)
- **The Odds API** - Odds aggregator (legitimate, paid)
- **WeatherAPI** - Weather data (official API)
- **Twitter API** - Social data (official API)
- **NewsAPI** - News aggregation (legitimate, paid)

#### ⚠️ USE WITH CAUTION (POC ONLY)
- **MLB Stats API** - Public but ToS-restricted (non-commercial only)
- **NHL Stats API** - Public but ToS-restricted (non-commercial only)
- **ESPN Injury Reports** - Manual checks only (no automated scraping)

#### ❌ DO NOT USE
- **nba_api** - Violates NBA.com ToS Section 9
- **Unofficial NFL.com/ESPN scrapers** - ToS violations
- **UFC Stats scrapers** - ToS violations, high IP ban risk

## NBA Data Sources & Compliance (Detailed)

- **BALLDONTLIE API** (Approved)
	- Usage: Historical NBA games and (with higher tiers) player stats.
	- Authentication: HTTP header `Authorization: <API_KEY>`.
	- Pagination: Cursor-based via `meta.next_cursor`; `per_page=100`.
	- Rate limits: Honor provider constraints; we enforce ~12 seconds between requests on free tier.

- **Open-Access Advanced Metrics (Approved)**
	- Source Examples: Basketball-Reference public pages used to create CSV files.
	- Storage: `.linelogic/players_advanced_metrics.csv` with documented schema.
	- Restriction: Do not scrape or redistribute paywalled datasets; respect robots.txt and site ToS.

- **ESPN Insider/Hollinger Index** (Prohibited)
	- Paywalled content; scraping or redistribution violates ToS and copyright.
	- Not used in the codebase.

For implementation details and current feature list, see [docs/16_player_features_and_sources.md](docs/16_player_features_and_sources.md).

### Cost Impact Summary

| Phase | Description | Monthly Cost | Legal Status |
|-------|-------------|--------------|--------------|
| M0 | POC (current) | $0 | ✅ Compliant |
| M1 | Modeling MVP | $25 | ✅ Compliant |
| M2 | Multi-sport | $55 | ✅ Compliant |
| M3 | Social/news | $119-219 | ✅ Compliant |
| M4 | Licensed feeds | $3,204+ | ✅ Compliant |

### Lessons Learned

1. **Always check ToS before integrating:** Even "public" APIs may have restrictions
2. **Gambling/fantasy use is heavily restricted:** Most sports leagues prohibit it
3. **Budget for licensed data:** Free sources have limitations and legal risks
4. **Open source datasets exist:** nflverse, Retrosheet are legally safe alternatives
5. **When in doubt, ask a lawyer:** Sports data licensing is complex

### Next Steps

1. ✅ GitHub repo configured: https://github.com/bbrennan/linelogic
2. ✅ Legal compliance documented
3. ✅ Cost roadmap established
4. 📋 **TODO:** Upgrade to BALLDONTLIE All-Star ($5/mo) when starting M1 modeling
5. 📋 **TODO:** Integrate The Odds API ($20/mo) for M1
6. 📋 **TODO:** Monitor for official NBA API availability

### References

- **NBA.com ToS:** https://www.nba.com/termsofuse (Section 9: NBA Statistics)
- **BALLDONTLIE:** https://www.balldontlie.io/
- **The Odds API:** https://the-odds-api.com/
- **nflverse:** https://github.com/nflverse/nflverse-data
- **Retrosheet:** https://www.retrosheet.org/

---

**Last Updated:** January 10, 2026  
**Status:** ✅ All nba_api code removed, legal compliance achieved  
**Next Review:** Before M1 (when upgrading to BALLDONTLIE All-Star)
