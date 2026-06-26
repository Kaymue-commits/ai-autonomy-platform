"""
全球数据源注册表 - 参考 worldmonitor 170+ 分类 RSS 源
每个源结构: name, url, lang, region, category, variant(可选)

variant 分类:
- full   : 地缘/军事/冲突 (默认)
- tech   : 创业/AI/融资
- finance: 市场/外汇/加密
- energy : 能源/电网
- happy  : 正面新闻/科学

category 详细分类:
politics, us, europe, middle_east, africa, asia, latam,
tech, ai, finance, gov, thinktank, crisis, intel,
startups, security, hardware,
markets, forex, bonds, crypto, regulation,
gcc_news, defense,
energy_grid, energy_oil, energy_renewable
"""

# ============================================================
# 政治 / 国际新闻 (Politics)
# ============================================================
POLITICS = [
    {"name": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "lang": "en", "region": "global", "category": "politics"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss", "lang": "en", "region": "global", "category": "politics"},
    {"name": "AP News", "url": "https://rsshub.app/apnews/topics/news", "lang": "en", "region": "global", "category": "politics"},
    {"name": "Reuters World", "url": "https://www.reutersagency.com/feed/?best-topics=top-news&post_type=best", "lang": "en", "region": "global", "category": "politics"},
    {"name": "CNN Top Stories", "url": "http://rss.cnn.com/rss/edition.rss", "lang": "en", "region": "global", "category": "politics"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "lang": "en", "region": "middle_east", "category": "politics"},
    {"name": "RT News", "url": "https://www.rt.com/rss/", "lang": "en", "region": "global", "category": "politics"},
    {"name": "DW News", "url": "https://rss.dw.com/rdf/rss-en-all", "lang": "en", "region": "europe", "category": "politics"},
]

# ============================================================
# 美国新闻 (US)
# ============================================================
US = [
    {"name": "NPR News", "url": "https://feeds.npr.org/1001/rss.xml", "lang": "en", "region": "us", "category": "us"},
    {"name": "PBS NewsHour", "url": "https://www.pbs.org/newshour/feeds/rss/headlines", "lang": "en", "region": "us", "category": "us"},
    {"name": "ABC News", "url": "https://abcnews.go.com/abcnews/topstories", "lang": "en", "region": "us", "category": "us"},
    {"name": "CBS News", "url": "https://www.cbsnews.com/latest/rss/main", "lang": "en", "region": "us", "category": "us"},
    {"name": "NBC News", "url": "https://feeds.nbcnews.com/nbcnews/public/news", "lang": "en", "region": "us", "category": "us"},
    {"name": "WSJ World", "url": "https://feeds.a.owler.com/news?uid=8484706", "lang": "en", "region": "us", "category": "us"},
    {"name": "Politico", "url": "https://rss.politico.com/politics-news.xml", "lang": "en", "region": "us", "category": "us"},
    {"name": "USA Today", "url": "https://rssfeeds.usatoday.com/UsatodaycomNation-TopStories", "lang": "en", "region": "us", "category": "us"},
    {"name": "Time", "url": "https://time.com/feed/", "lang": "en", "region": "us", "category": "us"},
    {"name": "The Atlantic", "url": "https://www.theatlantic.com/feed/all/", "lang": "en", "region": "us", "category": "us"},
]

# ============================================================
# 欧洲 (Europe)
# ============================================================
EUROPE = [
    {"name": "France24", "url": "https://www.france24.com/en/rss", "lang": "en", "region": "europe", "category": "europe"},
    {"name": "EuroNews", "url": "https://www.euronews.com/rss", "lang": "en", "region": "europe", "category": "europe"},
    {"name": "Le Monde", "url": "https://www.lemonde.fr/rss/une.xml", "lang": "fr", "region": "europe", "category": "europe"},
    {"name": "Der Spiegel", "url": "https://www.spiegel.de/international/index.rss", "lang": "en", "region": "europe", "category": "europe"},
    {"name": "El Pais English", "url": "https://elpais.com/elpaisinenglish.xml", "lang": "en", "region": "europe", "category": "europe"},
    {"name": "RAI News", "url": "https://www.rai.it/dl/grr/RssFeed.html?ch=bunews", "lang": "it", "region": "europe", "category": "europe"},
]

# ============================================================
# 中东 (Middle East)
# ============================================================
MIDDLE_EAST = [
    {"name": "BBC Middle East", "url": "http://feeds.bbci.co.uk/news/world/middle_east/rss.xml", "lang": "en", "region": "middle_east", "category": "middle_east"},
    {"name": "Guardian ME", "url": "https://www.theguardian.com/world/middleeast/rss", "lang": "en", "region": "middle_east", "category": "middle_east"},
    {"name": "Times of Israel", "url": "https://www.timesofisrael.com/feed/", "lang": "en", "region": "middle_east", "category": "middle_east"},
    {"name": "Jerusalem Post", "url": "https://www.jpost.com/Rss/RssFeedsHeadlines.aspx", "lang": "en", "region": "middle_east", "category": "middle_east"},
    {"name": "Tehran Times", "url": "https://www.tehrantimes.com/rss", "lang": "en", "region": "middle_east", "category": "middle_east"},
    {"name": "Daily Sabah", "url": "https://www.dailysabah.com/rssFeed/home", "lang": "en", "region": "middle_east", "category": "middle_east"},
]

# ============================================================
# 非洲 / 拉美 / 亚洲 (Africa / LatAm / Asia)
# ============================================================
AFRICA = [
    {"name": "BBC Africa", "url": "http://feeds.bbci.co.uk/news/world/africa/rss.xml", "lang": "en", "region": "africa", "category": "africa"},
    {"name": "Africa News", "url": "https://www.africanews.com/feed/", "lang": "en", "region": "africa", "category": "africa"},
    {"name": "Daily Maverick", "url": "https://www.dailymaverick.co.za/feed/", "lang": "en", "region": "africa", "category": "africa"},
]
LATAM = [
    {"name": "BBC Latin America", "url": "http://feeds.bbci.co.uk/news/world/latin_america/rss.xml", "lang": "en", "region": "latam", "category": "latam"},
    {"name": "MercoPress", "url": "https://en.mercopress.com/feed/news", "lang": "en", "region": "latam", "category": "latam"},
    {"name": "Rio Times", "url": "https://riotimes.com/feed/", "lang": "en", "region": "latam", "category": "latam"},
]
ASIA = [
    {"name": "BBC Asia", "url": "http://feeds.bbci.co.uk/news/world/asia/rss.xml", "lang": "en", "region": "asia", "category": "asia"},
    {"name": "Nikkei Asia", "url": "https://asia.nikkei.com/rss/feed/nar", "lang": "en", "region": "asia", "category": "asia"},
    {"name": "Global Times", "url": "https://www.globaltimes.cn/rss/outbound.xml", "lang": "en", "region": "asia", "category": "asia"},
    {"name": "South China Morning Post", "url": "https://www.scmp.com/rss/91/feed", "lang": "en", "region": "asia", "category": "asia"},
    {"name": "Japan Times", "url": "https://www.japantimes.co.jp/feed/topstories/", "lang": "en", "region": "asia", "category": "asia"},
    {"name": "Hindu Times", "url": "https://www.thehindu.com/news/national/feeder/default.rss", "lang": "en", "region": "asia", "category": "asia"},
]

# ============================================================
# 科技 (Tech)
# ============================================================
TECH = [
    {"name": "HackerNews", "url": "https://hnrss.org/frontpage", "lang": "en", "region": "global", "category": "tech"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "lang": "en", "region": "us", "category": "tech"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "lang": "en", "region": "us", "category": "tech"},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/", "lang": "en", "region": "us", "category": "tech"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "lang": "en", "region": "us", "category": "tech"},
    {"name": "VentureBeat", "url": "https://venturebeat.com/feed/", "lang": "en", "region": "us", "category": "tech"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss", "lang": "en", "region": "us", "category": "tech"},
    {"name": "Engadget", "url": "https://www.engadget.com/rss.xml", "lang": "en", "region": "us", "category": "tech"},
    {"name": "The Information", "url": "https://www.theinformation.com/feed", "lang": "en", "region": "us", "category": "tech"},
    {"name": "Stratechery", "url": "https://stratechery.com/feed/", "lang": "en", "region": "us", "category": "tech"},
]

# ============================================================
# AI 专源 (AI)
# ============================================================
AI = [
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "lang": "en", "region": "global", "category": "ai"},
    {"name": "Anthropic News", "url": "https://www.anthropic.com/news/rss.xml", "lang": "en", "region": "global", "category": "ai"},
    {"name": "DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml", "lang": "en", "region": "global", "category": "ai"},
    {"name": "HuggingFace Blog", "url": "https://huggingface.co/blog/feed.xml", "lang": "en", "region": "global", "category": "ai"},
    {"name": "MIT TechReview AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed", "lang": "en", "region": "global", "category": "ai"},
    {"name": "The Decoder", "url": "https://the-decoder.com/feed/", "lang": "en", "region": "global", "category": "ai"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "lang": "en", "region": "global", "category": "ai"},
    {"name": "Arxiv CS.AI", "url": "https://export.arxiv.org/rss/cs.AI", "lang": "en", "region": "global", "category": "ai"},
    {"name": "Arxiv CS.LG", "url": "https://export.arxiv.org/rss/cs.LG", "lang": "en", "region": "global", "category": "ai"},
    {"name": "Arxiv CS.CL", "url": "https://export.arxiv.org/rss/cs.CL", "lang": "en", "region": "global", "category": "ai"},
    {"name": "Arxiv CS.CV", "url": "https://export.arxiv.org/rss/cs.CV", "lang": "en", "region": "global", "category": "ai"},
    {"name": "Reddit LocalLLaMA", "url": "https://www.reddit.com/r/LocalLLaMA/.rss", "lang": "en", "region": "global", "category": "ai"},
    {"name": "Reddit singularity", "url": "https://www.reddit.com/r/singularity/.rss", "lang": "en", "region": "global", "category": "ai"},
    {"name": "Reddit ML", "url": "https://www.reddit.com/r/MachineLearning/.rss", "lang": "en", "region": "global", "category": "ai"},
    {"name": "AI Brews", "url": "https://aibrews.com/feed.xml", "lang": "en", "region": "global", "category": "ai"},
]

# ============================================================
# 金融 (Finance) - variant=finance
# ============================================================
FINANCE = [
    {"name": "CNBC Top News", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "lang": "en", "region": "global", "category": "finance", "variant": "finance"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex", "lang": "en", "region": "global", "category": "finance", "variant": "finance"},
    {"name": "Financial Times", "url": "https://www.ft.com/rss/home", "lang": "en", "region": "global", "category": "finance", "variant": "finance"},
    {"name": "Reuters Business", "url": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best", "lang": "en", "region": "global", "category": "finance", "variant": "finance"},
    {"name": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss", "lang": "en", "region": "global", "category": "finance", "variant": "finance"},
    {"name": "MarketWatch", "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories", "lang": "en", "region": "global", "category": "finance", "variant": "finance"},
    {"name": "Investing News", "url": "https://www.investing.com/rss/news_25.rss", "lang": "en", "region": "global", "category": "finance", "variant": "finance"},
    {"name": "Barrons", "url": "https://feeds.content.dowjones.io/public/rss/rssbarrons", "lang": "en", "region": "global", "category": "finance", "variant": "finance"},
]

# ============================================================
# 政府机构 (Gov)
# ============================================================
GOV = [
    {"name": "WhiteHouse Briefing", "url": "https://www.whitehouse.gov/feed/", "lang": "en", "region": "us", "category": "gov"},
    {"name": "State Department", "url": "https://www.state.gov/rss-feeds/", "lang": "en", "region": "us", "category": "gov"},
    {"name": "Defense.gov", "url": "https://www.defense.gov/News/News-Stories/RSS/News.xml", "lang": "en", "region": "us", "category": "gov"},
    {"name": "Federal Reserve", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "lang": "en", "region": "us", "category": "gov"},
    {"name": "SEC News", "url": "https://www.sec.gov/rss/news/press.xml", "lang": "en", "region": "us", "category": "gov"},
    {"name": "UN News", "url": "https://news.un.org/en/news/region/middle-east/feed", "lang": "en", "region": "global", "category": "gov"},
    {"name": "CISA Alerts", "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml", "lang": "en", "region": "us", "category": "gov"},
    {"name": "EU Commission", "url": "https://ec.europa.eu/newsroom/rss_en", "lang": "en", "region": "europe", "category": "gov"},
    {"name": "NATO News", "url": "https://www.nato.int/cps/en/rss/RSS_NEWS.xml", "lang": "en", "region": "europe", "category": "gov"},
]

# ============================================================
# 智库 (Think Tanks)
# ============================================================
THINK_TANKS = [
    {"name": "Foreign Policy", "url": "https://foreignpolicy.com/feed/", "lang": "en", "region": "us", "category": "thinktank"},
    {"name": "Atlantic Council", "url": "https://www.atlanticcouncil.org/feed/", "lang": "en", "region": "us", "category": "thinktank"},
    {"name": "Foreign Affairs", "url": "https://www.foreignaffairs.com/rss.xml", "lang": "en", "region": "us", "category": "thinktank"},
    {"name": "Brookings", "url": "https://www.brookings.edu/feed/", "lang": "en", "region": "us", "category": "thinktank"},
    {"name": "CSIS", "url": "https://www.csis.org/analysis/feed", "lang": "en", "region": "us", "category": "thinktank"},
    {"name": "RAND Blog", "url": "https://www.rand.org/blog/feed.xml", "lang": "en", "region": "us", "category": "thinktank"},
    {"name": "War on the Rocks", "url": "https://warontherocks.com/feed/", "lang": "en", "region": "us", "category": "thinktank"},
]

# ============================================================
# 危机监测 (Crisis)
# ============================================================
CRISIS = [
    {"name": "CrisisWatch", "url": "https://www.crisisgroup.org/crisiswatch/feed", "lang": "en", "region": "global", "category": "crisis"},
    {"name": "IAEA News", "url": "https://www.iaea.org/feeds/press-releases", "lang": "en", "region": "global", "category": "crisis"},
    {"name": "WHO News", "url": "https://www.who.int/rss-feeds/news-english.xml", "lang": "en", "region": "global", "category": "crisis"},
    {"name": "ReliefWeb", "url": "https://api.reliefweb.int/v1/reports?appname=rss&filter[field]=country&filter[value][0]=world", "lang": "en", "region": "global", "category": "crisis"},
    {"name": "UN OCHA", "url": "https://reliefweb.int/rss/country/world", "lang": "en", "region": "global", "category": "crisis"},
]

# ============================================================
# 情报源 (Intel) - defense/military
# ============================================================
INTEL = [
    {"name": "Defense One", "url": "https://www.defenseone.com/rss/", "lang": "en", "region": "us", "category": "intel"},
    {"name": "Breaking Defense", "url": "https://breakingdefense.com/feed/", "lang": "en", "region": "us", "category": "intel"},
    {"name": "The War Zone", "url": "https://www.thedrive.com/the-war-zone/feed", "lang": "en", "region": "us", "category": "intel"},
    {"name": "Defense News", "url": "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml", "lang": "en", "region": "us", "category": "intel"},
    {"name": "Janes News", "url": "https://www.janes.com/feeds/news", "lang": "en", "region": "global", "category": "intel"},
    {"name": "Defense Blog", "url": "https://defence-blog.com/feed", "lang": "en", "region": "global", "category": "intel"},
    {"name": "Oryx OSINT", "url": "https://www.oryxspioenkop.com/feeds/posts/default", "lang": "en", "region": "global", "category": "intel"},
    {"name": "Bellingcat", "url": "https://www.bellingcat.com/feed/", "lang": "en", "region": "global", "category": "intel"},
    {"name": "ISW", "url": "https://www.understandingwar.org/feeds/blog", "lang": "en", "region": "global", "category": "intel"},
]

# ============================================================
# 创业 / VC (Startups) - variant=tech
# ============================================================
STARTUPS = [
    {"name": "Y Combinator", "url": "https://www.ycombinator.com/blog/feed", "lang": "en", "region": "us", "category": "startups", "variant": "tech"},
    {"name": "a16z", "url": "https://a16z.com/feed/", "lang": "en", "region": "us", "category": "startups", "variant": "tech"},
    {"name": "Sequoia", "url": "https://www.sequoiacap.com/feed/", "lang": "en", "region": "us", "category": "startups", "variant": "tech"},
    {"name": "IndieHackers", "url": "https://www.indiehackers.com/feed.xml", "lang": "en", "region": "global", "category": "startups", "variant": "tech"},
    {"name": "ProductHunt", "url": "https://www.producthunt.com/feed", "lang": "en", "region": "global", "category": "startups", "variant": "tech"},
    {"name": "Crunchbase News", "url": "https://news.crunchbase.com/feed/", "lang": "en", "region": "global", "category": "startups", "variant": "tech"},
    {"name": "TechCrunch Startups", "url": "https://techcrunch.com/category/startups/feed/", "lang": "en", "region": "us", "category": "startups", "variant": "tech"},
    {"name": "Acquired FM", "url": "https://feeds.acquiredfm.com/acquired", "lang": "en", "region": "us", "category": "startups", "variant": "tech"},
]

# ============================================================
# 安全 / 网络战 (Security)
# ============================================================
SECURITY = [
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/", "lang": "en", "region": "us", "category": "security"},
    {"name": "Dark Reading", "url": "https://www.darkreading.com/rss.xml", "lang": "en", "region": "us", "category": "security"},
    {"name": "The Hacker News", "url": "https://feeds.feedburner.com/TheHackersNews", "lang": "en", "region": "global", "category": "security"},
    {"name": "BleepingComputer", "url": "https://www.bleepingcomputer.com/feed/", "lang": "en", "region": "global", "category": "security"},
    {"name": "Schneier on Security", "url": "https://www.schneier.com/feed/atom/", "lang": "en", "region": "us", "category": "security"},
    {"name": "Threatpost", "url": "https://threatpost.com/feed/", "lang": "en", "region": "global", "category": "security"},
    {"name": "Recorded Future", "url": "https://www.recordedfuture.com/feed", "lang": "en", "region": "global", "category": "security"},
]

# ============================================================
# 硬件 / 半导体 (Hardware)
# ============================================================
HARDWARE = [
    {"name": "Tom's Hardware", "url": "https://www.tomshardware.com/feeds/all", "lang": "en", "region": "us", "category": "hardware"},
    {"name": "AnandTech", "url": "https://www.anandtech.com/rss/", "lang": "en", "region": "us", "category": "hardware"},
    {"name": "SemiAnalysis", "url": "https://www.semianalysis.com/feed", "lang": "en", "region": "global", "category": "hardware"},
    {"name": "EE Times", "url": "https://www.eetimes.com/feed/", "lang": "en", "region": "global", "category": "hardware"},
]

# ============================================================
# 加密货币 (Crypto) - variant=finance
# ============================================================
CRYPTO = [
    {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "lang": "en", "region": "global", "category": "crypto", "variant": "finance"},
    {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss", "lang": "en", "region": "global", "category": "crypto", "variant": "finance"},
    {"name": "Bitcoin Magazine", "url": "https://bitcoinmagazine.com/.rss/full/", "lang": "en", "region": "global", "category": "crypto", "variant": "finance"},
    {"name": "CryptoSlate", "url": "https://cryptoslate.com/feed/", "lang": "en", "region": "global", "category": "crypto", "variant": "finance"},
    {"name": "Decrypt", "url": "https://decrypt.co/feed", "lang": "en", "region": "global", "category": "crypto", "variant": "finance"},
    {"name": "The Block", "url": "https://www.theblock.co/rss.xml", "lang": "en", "region": "global", "category": "crypto", "variant": "finance"},
]

# ============================================================
# GCC 海湾国家新闻 (GCC News)
# ============================================================
GCC = [
    {"name": "Arabian Business", "url": "https://www.arabianbusiness.com/rss", "lang": "en", "region": "middle_east", "category": "gcc_news"},
    {"name": "The National", "url": "https://www.thenationalnews.com/rss/arab", "lang": "en", "region": "middle_east", "category": "gcc_news"},
    {"name": "Arab News", "url": "https://www.arabnews.com/rss.xml", "lang": "en", "region": "middle_east", "category": "gcc_news"},
    {"name": "Gulf News", "url": "https://gulfnews.com/rss/gulf", "lang": "en", "region": "middle_east", "category": "gcc_news"},
    {"name": "Khaleej Times", "url": "https://www.khaleejtimes.com/rss/home", "lang": "en", "region": "middle_east", "category": "gcc_news"},
    {"name": "Al Arabiya", "url": "https://www.alarabiya.net/tools/rss", "lang": "en", "region": "middle_east", "category": "gcc_news"},
]

# ============================================================
# 能源 (Energy)
# ============================================================
ENERGY = [
    {"name": "OilPrice.com", "url": "https://oilprice.com/rss/main", "lang": "en", "region": "global", "category": "energy_oil"},
    {"name": "Reuters Energy", "url": "https://www.reutersagency.com/feed/?best-topics=energy&post_type=best", "lang": "en", "region": "global", "category": "energy_oil"},
    {"name": "S&P Global Platts", "url": "https://platts.com/rssFeed", "lang": "en", "region": "global", "category": "energy_oil"},
    {"name": "Energy Voice", "url": "https://www.energyvoice.com/feed/", "lang": "en", "region": "global", "category": "energy_oil"},
    {"name": "Renewable Energy World", "url": "https://www.renewableenergyworld.com/feed/", "lang": "en", "region": "global", "category": "energy_renewable"},
    {"name": "PV Magazine", "url": "https://www.pv-magazine.com/feed/", "lang": "en", "region": "global", "category": "energy_renewable"},
    {"name": "CleanTechnica", "url": "https://cleantechnica.com/feed/", "lang": "en", "region": "global", "category": "energy_renewable"},
    {"name": "Power Engineering", "url": "https://www.power-eng.com/rss", "lang": "en", "region": "global", "category": "energy_grid"},
]

# ============================================================
# 中国新闻 (Chinese)
# ============================================================
CHINESE = [
    {"name": "36Kr", "url": "https://36kr.com/feed", "lang": "zh", "region": "asia", "category": "tech"},
    {"name": "Huxiu", "url": "https://www.huxiu.com/rss/0.xml", "lang": "zh", "region": "asia", "category": "tech"},
    {"name": "PingWest", "url": "https://www.pingwest.com/feed", "lang": "zh", "region": "asia", "category": "tech"},
    {"name": "Solidot", "url": "https://www.solidot.org/index.rss", "lang": "zh", "region": "asia", "category": "tech"},
    {"name": "cnBeta", "url": "https://rss.cnbeta.com/rss", "lang": "zh", "region": "asia", "category": "tech"},
]

# ============================================================
# 汇总: 所有源
# ============================================================
ALL_SOURCES = (
    POLITICS + US + EUROPE + MIDDLE_EAST + AFRICA + LATAM + ASIA +
    TECH + AI + FINANCE + GOV + THINK_TANKS + CRISIS + INTEL +
    STARTUPS + SECURITY + HARDWARE + CRYPTO + GCC + ENERGY + CHINESE
)

# 按 category 分组的索引
BY_CATEGORY = {}
for src in ALL_SOURCES:
    cat = src["category"]
    BY_CATEGORY.setdefault(cat, []).append(src)

# 按 region 分组的索引
BY_REGION = {}
for src in ALL_SOURCES:
    region = src["region"]
    BY_REGION.setdefault(region, []).append(src)

# 按 variant 分组的索引
BY_VARIANT = {"full": [], "tech": [], "finance": [], "energy": [], "happy": []}
for src in ALL_SOURCES:
    v = src.get("variant", "full")
    BY_VARIANT["full"].append(src)  # full variant 包含全部
    if v != "full":
        BY_VARIANT.setdefault(v, []).append(src)


def get_sources_by_variant(variant: str = "full") -> list[dict]:
    """获取指定变体的所有源"""
    if variant == "full":
        return ALL_SOURCES
    return BY_VARIANT.get(variant, [])


def get_sources_by_category(category: str) -> list[dict]:
    """获取指定分类的所有源"""
    return BY_CATEGORY.get(category, [])


def get_sources_by_region(region: str) -> list[dict]:
    """获取指定地区的所有源"""
    return BY_REGION.get(region, [])


def get_source_stats() -> dict:
    """数据源统计"""
    return {
        "total_sources": len(ALL_SOURCES),
        "by_category": {k: len(v) for k, v in BY_CATEGORY.items()},
        "by_region": {k: len(v) for k, v in BY_REGION.items()},
        "by_variant": {k: len(v) for k, v in BY_VARIANT.items()},
        "categories": sorted(BY_CATEGORY.keys()),
        "regions": sorted(BY_REGION.keys()),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_source_stats(), indent=2, ensure_ascii=False))
