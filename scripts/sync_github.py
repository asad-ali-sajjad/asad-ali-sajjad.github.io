import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
USERNAME = "asad-ali-sajjad"
SCHEMA_VERSION = "2.1.0"

MASTER_FILE = ROOT_DIR / "data" / "github-profile.json"
INDIVIDUAL_DIR = ROOT_DIR / "data" / "individual-repos"
PORTFOLIO_JS_OUT = ROOT_DIR / "js" / "data" / "portfolio-data.js"

# Map old repository slugs -> new slugs so renames self-heal automatically
REPO_ALIASES = {
    "cs-mcq-hub": "reviseloop",
}

LANG_COLORS = {
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "Jupyter Notebook": "#da5b0b",
    "HTML": "#e34c26",
    "HTML / JS": "#e34c26",
    "CSS": "#563d7c",
    "PHP": "#4F5D95",
    "C++": "#f34b7d",
    "TSQL": "#e38c00",
    "T-SQL": "#e38c00",
    "Java": "#b07219",
    "Markdown": "#083fa1",
}

DEFAULT_PORTFOLIO_PRESETS = {
    "mediai-care": {
        "featured": True,
        "order": 1,
        "badge": "Pinned",
        "category": "ai",
        "language": "TypeScript",
        "langColor": "#3178c6",
        "tags": ["Next.js", "PostgreSQL", "AI Screening", "RAG"],
    },
    "plant-disease-diagnostic-system": {
        "featured": True,
        "order": 2,
        "badge": "Pinned",
        "category": "ai",
        "language": "Jupyter Notebook",
        "langColor": "#da5b0b",
        "tags": ["PyTorch", "Streamlit", "Deep Learning", "Computer Vision"],
    },
    "reviseloop": {
        "featured": True,
        "order": 3,
        "badge": "Featured",
        "category": "web",
        "language": "HTML / JS",
        "langColor": "#e34c26",
        "tags": ["Computer Science", "Interactive Quiz", "Study Guide"],
    },
    "clinic-appointment-system": {
        "featured": True,
        "order": 4,
        "badge": "Pinned",
        "category": "web",
        "language": "PHP",
        "langColor": "#4F5D95",
        "tags": ["PHP", "MySQL", "Healthcare", "Booking"],
    },
    "bank-management-system": {
        "featured": True,
        "order": 5,
        "badge": "Pinned",
        "category": "systems",
        "language": "C++",
        "langColor": "#f34b7d",
        "tags": ["C++", "Data Structures", "CLI", "RBAC"],
    },
    "library-management-system-sql": {
        "featured": True,
        "order": 6,
        "badge": "Pinned",
        "category": "systems",
        "language": "TSQL",
        "langColor": "#e38c00",
        "tags": ["MS SQL Server", "T-SQL", "Triggers", "Stored Procedures"],
    },
    "glimpse": {
        "featured": True,
        "order": 7,
        "badge": "Full-Stack",
        "category": "web",
        "language": "JavaScript",
        "langColor": "#f1e05a",
        "tags": ["Next.js", "Supabase", "Social App"],
    },
    "business-nexus-frontend": {
        "featured": True,
        "order": 8,
        "badge": "Full-Stack",
        "category": "web",
        "language": "JavaScript",
        "langColor": "#f1e05a",
        "tags": ["Frontend", "Dashboards", "Real-Time Chat"],
    },
    "business-nexus-backend": {
        "featured": True,
        "order": 9,
        "badge": "Backend API",
        "category": "web",
        "language": "JavaScript",
        "langColor": "#f1e05a",
        "tags": ["Express.js", "MongoDB", "REST API"],
    },
}


class RateLimitError(Exception):
    def __init__(self, reset_time: str | None = None):
        self.reset_time = reset_time
        msg = "GitHub API rate limit exceeded"
        if reset_time:
            msg += f" (resets at {reset_time})"
        super().__init__(msg)


def resolve_github_token() -> tuple[str, str]:
    """Resolve token from env vars, optional .env file, or GitHub CLI (`gh`)."""
    for env_key in ("GITHUB_TOKEN", "GH_TOKEN"):
        val = os.environ.get(env_key, "").strip()
        if val:
            return val, env_key

    env_file = ROOT_DIR / ".env"
    if env_file.is_file():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                k, v = stripped.split("=", 1)
                if k.strip() in ("GITHUB_TOKEN", "GH_TOKEN") and v.strip():
                    return v.strip().strip('"').strip("'"), ".env"
        except OSError:
            pass

    try:
        proc = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        token = proc.stdout.strip()
        if proc.returncode == 0 and token:
            return token, "gh CLI"
    except (OSError, subprocess.SubprocessError):
        pass

    return "", "unauthenticated"


def build_headers(token: str) -> dict:
    headers = {
        "User-Agent": f"{USERNAME}-portfolio-sync",
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def format_reset_timestamp(reset_header: str | None) -> str | None:
    if not reset_header or not reset_header.isdigit():
        return None
    dt = datetime.fromtimestamp(int(reset_header), tz=timezone.utc).astimezone()
    return dt.strftime("%I:%M:%S %p")


def fetch_json(url: str, token: str, allow_not_found: bool = False):
    req = urllib.request.Request(url, headers=build_headers(token))
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        if allow_not_found and err.code == 404:
            return None
        if err.code in (403, 429):
            remaining = err.headers.get("X-RateLimit-Remaining", "")
            if remaining == "0" or "rate limit" in str(err.reason).lower():
                reset_str = format_reset_timestamp(err.headers.get("X-RateLimit-Reset"))
                raise RateLimitError(reset_str) from err
        raise


def infer_category(repo: dict) -> str:
    text = " ".join([
        repo.get("name", ""),
        repo.get("category", ""),
        repo.get("overview", {}).get("description", ""),
        " ".join(repo.get("github_metadata", {}).get("topics", [])),
    ]).lower()

    if any(k in text for k in ("ai", "computer-vision", "computer vision", "deep-learning", "deep learning", "pytorch", "ml")):
        return "ai"
    if any(k in text for k in ("cli", "database", "c++", "sql", "tsql", "systems", "data-structures")):
        return "systems"
    return "web"


def compute_lifecycle(created_iso: str | None, pushed_iso: str | None, is_fork: bool, is_archived: bool, is_template: bool) -> dict:
    now = datetime.now(timezone.utc)
    age_days = None
    days_since_push = None

    if created_iso:
        try:
            created_dt = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
            age_days = max(0, (now - created_dt).days)
        except ValueError:
            pass

    if pushed_iso:
        try:
            pushed_dt = datetime.fromisoformat(pushed_iso.replace("Z", "+00:00"))
            days_since_push = max(0, (now - pushed_dt).days)
        except ValueError:
            pass

    if is_archived:
        status = "archived"
    elif days_since_push is None:
        status = "unknown"
    elif days_since_push <= 45:
        status = "active"
    elif days_since_push <= 180:
        status = "maintained"
    else:
        status = "dormant"

    return {
        "is_fork": is_fork,
        "is_archived": is_archived,
        "is_template": is_template,
        "age_days": age_days,
        "days_since_push": days_since_push,
        "status": status,
    }


def format_language_breakdown(raw_bytes: dict | None) -> dict:
    if not raw_bytes or not isinstance(raw_bytes, dict):
        return {}
    total = sum(v for v in raw_bytes.values() if isinstance(v, (int, float)) and v > 0)
    if total <= 0:
        return {}
    breakdown = {}
    for lang, byte_count in sorted(raw_bytes.items(), key=lambda item: item[1], reverse=True):
        breakdown[lang] = {
            "bytes": int(byte_count),
            "pct": round((byte_count / total) * 100, 1),
        }
    return breakdown


def ensure_uniform_repo_schema(repo: dict) -> dict:
    """Guarantee every repo (including auto-discovered ones) shares the exact master schema."""
    name = repo["name"]
    primary_lang = repo.get("tech_stack", {}).get("primary_language") or "JavaScript"

    repo.setdefault("full_name", f"{USERNAME}/{name}")
    repo.setdefault("owner", USERNAME)
    repo.setdefault("visibility", "public")
    repo.setdefault("is_pinned", False)
    repo.setdefault("status", "wip")
    repo.setdefault("category", primary_lang)

    links = repo.setdefault("links", {})
    links.setdefault("repo_url", f"https://github.com/{USERNAME}/{name}")
    links.setdefault("live_demo_url", None)
    links.setdefault("docs_url", f"https://github.com/{USERNAME}/{name}#readme")
    links.setdefault("clone_url", f"https://github.com/{USERNAME}/{name}.git")
    links.setdefault("has_pages", False)

    overview = repo.setdefault("overview", {})
    overview.setdefault("tagline", "")
    overview.setdefault("description", "")
    overview.setdefault("problem_solved", "")
    overview.setdefault("target_users", "")

    tech = repo.setdefault("tech_stack", {})
    tech.setdefault("primary_language", primary_lang)
    tech.setdefault("languages", [primary_lang] if primary_lang else [])
    tech.setdefault("frameworks_and_libraries", [])
    tech.setdefault("databases_and_storage", [])
    tech.setdefault("apis_and_services", [])
    tech.setdefault("tools_and_deployment", ["Git"])
    tech.setdefault("language_breakdown", {})

    repo.setdefault("key_features", [])

    arch = repo.setdefault("architecture", {})
    arch.setdefault("pattern", "")
    arch.setdefault("folder_structure", [])
    arch.setdefault("entry_points", [])
    arch.setdefault("database_models_or_schema", [])

    setup = repo.setdefault("setup_and_usage", {})
    setup.setdefault("prerequisites", [])
    setup.setdefault("env_variables", [])
    setup.setdefault("install_commands", [f"git clone https://github.com/{USERNAME}/{name}.git"])
    setup.setdefault("run_commands", [])

    meta = repo.setdefault("github_metadata", {})
    meta.setdefault("default_branch", "main")
    meta.setdefault("topics", [])
    meta.setdefault("license", None)
    meta.setdefault("stars", 0)
    meta.setdefault("forks", 0)
    meta.setdefault("watchers", 0)
    meta.setdefault("open_issues", 0)
    meta.setdefault("size_kb", 0)
    meta.setdefault("aliases", [])
    meta.setdefault("full_name", f"{USERNAME}/{name}")
    meta.setdefault("latest_release", None)

    highlights = repo.setdefault("portfolio_highlights", {})
    highlights.setdefault("challenges_solved", [])
    highlights.setdefault("resume_bullets", [])

    if "portfolio" not in repo:
        if name in DEFAULT_PORTFOLIO_PRESETS:
            repo["portfolio"] = DEFAULT_PORTFOLIO_PRESETS[name].copy()
        else:
            repo["portfolio"] = {
                "featured": False,
                "order": 99,
                "badge": "Pinned" if repo.get("is_pinned") else "Project",
                "category": infer_category(repo),
                "language": primary_lang,
                "langColor": LANG_COLORS.get(primary_lang, "#38bdf8"),
                "tags": tech.get("frameworks_and_libraries", [])[:4],
            }

    return repo


def build_new_repo_record(live: dict) -> dict:
    name = live["name"]
    primary_lang = live.get("language") or "JavaScript"
    license_info = live.get("license") or {}
    license_spdx = license_info.get("spdx_id") if license_info.get("spdx_id") not in (None, "NOASSERTION") else None

    record = {
        "name": name,
        "full_name": live.get("full_name") or f"{USERNAME}/{name}",
        "owner": USERNAME,
        "visibility": "private" if live.get("private") else "public",
        "is_pinned": False,
        "status": "wip",
        "category": primary_lang,
        "links": {
            "repo_url": live.get("html_url") or f"https://github.com/{USERNAME}/{name}",
            "live_demo_url": live.get("homepage") or None,
            "docs_url": f"https://github.com/{USERNAME}/{name}#readme",
            "clone_url": live.get("clone_url") or f"https://github.com/{USERNAME}/{name}.git",
            "has_pages": bool(live.get("has_pages", False)),
        },
        "overview": {
            "tagline": "",
            "description": live.get("description") or "",
            "problem_solved": "",
            "target_users": "",
        },
        "tech_stack": {
            "primary_language": primary_lang,
            "languages": [primary_lang],
            "frameworks_and_libraries": live.get("topics", [])[:6],
            "databases_and_storage": [],
            "apis_and_services": [],
            "tools_and_deployment": ["Git"],
            "language_breakdown": {},
        },
        "github_metadata": {
            "github_id": live.get("id"),
            "node_id": live.get("node_id"),
            "full_name": live.get("full_name") or f"{USERNAME}/{name}",
            "aliases": [],
            "default_branch": live.get("default_branch", "main"),
            "topics": live.get("topics", []),
            "stars": live.get("stargazers_count", 0),
            "forks": live.get("forks_count", 0),
            "watchers": live.get("watchers_count", 0),
            "open_issues": live.get("open_issues_count", 0),
            "size_kb": live.get("size", 0),
            "license": license_spdx,
            "latest_release": None,
            "created_at": (live.get("created_at") or "")[:10] or None,
            "last_updated": (live.get("pushed_at") or "")[:10] or None,
        },
        "lifecycle": compute_lifecycle(
            live.get("created_at"),
            live.get("pushed_at"),
            bool(live.get("fork", False)),
            bool(live.get("archived", False)),
            bool(live.get("is_template", False)),
        ),
    }

    return ensure_uniform_repo_schema(record)


def build_tech_summary(repos: list[dict]) -> dict:
    lang_bytes_totals = {}
    lang_repo_counts = {}
    category_counts = {"ai": 0, "web": 0, "systems": 0}

    for repo in repos:
        p_cat = repo.get("portfolio", {}).get("category") or infer_category(repo)
        if p_cat in category_counts:
            category_counts[p_cat] += 1

        breakdown = repo.get("tech_stack", {}).get("language_breakdown") or {}
        if breakdown:
            for lang, stats in breakdown.items():
                lang_bytes_totals[lang] = lang_bytes_totals.get(lang, 0) + stats.get("bytes", 0)
        else:
            primary = repo.get("tech_stack", {}).get("primary_language")
            if primary:
                lang_repo_counts[primary] = lang_repo_counts.get(primary, 0) + 1

    languages = []
    if lang_bytes_totals:
        grand_total = sum(lang_bytes_totals.values())
        for lang, b_count in sorted(lang_bytes_totals.items(), key=lambda x: x[1], reverse=True):
            languages.append({
                "name": lang,
                "color": LANG_COLORS.get(lang, "#38bdf8"),
                "bytes": b_count,
                "pct": round((b_count / grand_total) * 100, 1) if grand_total else 0,
            })
    else:
        total_repos = sum(lang_repo_counts.values())
        for lang, r_count in sorted(lang_repo_counts.items(), key=lambda x: x[1], reverse=True):
            languages.append({
                "name": lang,
                "color": LANG_COLORS.get(lang, "#38bdf8"),
                "repoCount": r_count,
                "pct": round((r_count / total_repos) * 100, 1) if total_repos else 0,
            })

    return {
        "byCategory": category_counts,
        "byLanguage": languages,
    }


def generate_portfolio_js(profile_data: dict, out_path: Path):
    profile = profile_data.get("profile", {})
    links = profile.get("links", {})
    stats = profile.get("stats", {})
    email = links.get("email", "imasad789@gmail.com")
    roles = profile.get(
        "roles",
        [
            "Full-Stack Web Developer",
            "AI & Machine Learning Builder",
            "C++ & Database Engineer",
            "Open-Source Problem Solver",
        ],
    )

    repos = profile_data.get("repositories", [])
    featured_repos = [
        r for r in repos
        if r.get("portfolio", {}).get("featured") is True
    ]
    featured_repos.sort(key=lambda r: r.get("portfolio", {}).get("order", 999))

    total_stars = sum(r.get("github_metadata", {}).get("stars", 0) for r in repos)
    total_forks = sum(r.get("github_metadata", {}).get("forks", 0) for r in repos)
    active_count = sum(1 for r in repos if r.get("lifecycle", {}).get("status") == "active")

    profile_meta = {
        "schemaVersion": SCHEMA_VERSION,
        "username": USERNAME,
        "bio": profile.get("bio", ""),
        "location": profile.get("location", ""),
        "followers": stats.get("followers", 0),
        "publicRepos": stats.get("public_repos", len(repos)),
        "trackedRepos": len(repos),
        "featuredCount": len(featured_repos),
        "activeRepos": active_count,
        "totalStars": total_stars,
        "totalForks": total_forks,
        "lastSynced": profile_data.get("last_synced", date.today().isoformat()),
    }

    tech_summary = build_tech_summary(repos)

    def serialize_project(repo: dict) -> dict:
        p = repo.get("portfolio", {})
        meta = repo.get("github_metadata", {})
        overview = repo.get("overview", {})
        lifecycle = repo.get("lifecycle", {})
        tech = repo.get("tech_stack", {})
        p_highlights = repo.get("portfolio_highlights", {})
        primary_lang = p.get("language") or tech.get("primary_language", "JavaScript")
        lang_color = p.get("langColor") or LANG_COLORS.get(primary_lang, "#38bdf8")
        badge = "Pinned" if repo.get("is_pinned") else p.get("badge", "Featured")

        return {
            "id": meta.get("github_id"),
            "slug": repo["name"],
            "title": repo["name"],
            "aliases": meta.get("aliases", []),
            "badge": badge,
            "projectStatus": repo.get("status", "completed"),
            "category": p.get("category") or infer_category(repo),
            "language": primary_lang,
            "langColor": lang_color,
            "languageBreakdown": tech.get("language_breakdown", {}),
            "tagline": overview.get("tagline", ""),
            "description": p.get("description") or overview.get("description", ""),
            "problemSolved": overview.get("problem_solved", ""),
            "keyFeatures": repo.get("key_features", []),
            "challengesSolved": p_highlights.get("challenges_solved", []),
            "resumeBullets": p_highlights.get("resume_bullets", []),
            "tags": p.get("tags", []),
            "repoUrl": repo.get("links", {}).get("repo_url"),
            "demoUrl": repo.get("links", {}).get("live_demo_url"),
            "stars": meta.get("stars", 0),
            "forks": meta.get("forks", 0),
            "license": meta.get("license"),
            "latestRelease": meta.get("latest_release"),
            "createdAt": meta.get("created_at"),
            "updatedAt": meta.get("last_updated"),
            "activityStatus": lifecycle.get("status", "maintained"),
        }

    project_entries = [serialize_project(r) for r in featured_repos]

    all_repos_index = [
        {
            "slug": r["name"],
            "featured": bool(r.get("portfolio", {}).get("featured")),
            "projectStatus": r.get("status", "wip"),
            "category": r.get("portfolio", {}).get("category") or infer_category(r),
            "language": r.get("tech_stack", {}).get("primary_language"),
            "tagline": r.get("overview", {}).get("tagline", ""),
            "description": r.get("overview", {}).get("description", ""),
            "stars": r.get("github_metadata", {}).get("stars", 0),
            "updatedAt": r.get("github_metadata", {}).get("last_updated"),
            "activityStatus": r.get("lifecycle", {}).get("status", "maintained"),
            "repoUrl": r.get("links", {}).get("repo_url"),
            "demoUrl": r.get("links", {}).get("live_demo_url"),
        }
        for r in sorted(
            repos,
            key=lambda x: x.get("github_metadata", {}).get("last_updated") or "",
            reverse=True,
        )
    ]

    lines = [
        "// AUTO-GENERATED BY sync_github.py FROM github-profile.json — DO NOT EDIT MANUALLY",
        f"export const CONTACT_EMAIL = {json.dumps(email)};",
        "",
        f"export const PROFILE_META = {json.dumps(profile_meta, indent=2, ensure_ascii=False)};",
        "",
        f"export const TECH_SUMMARY = {json.dumps(tech_summary, indent=2, ensure_ascii=False)};",
        "",
        f"export const ROLES = {json.dumps(roles, indent=2)};",
        "",
        f"export const PROJECTS = {json.dumps(project_entries, indent=2, ensure_ascii=False)};",
        "",
        f"export const ALL_REPOS = {json.dumps(all_repos_index, indent=2, ensure_ascii=False)};",
        "",
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Sync GitHub metadata and regenerate structured portfolio data")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip GitHub API network requests and regenerate files from local github-profile.json",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Fetch per-repo language breakdowns and latest release tags (auto-enabled when a token is detected)",
    )
    parser.add_argument(
        "--include-forks",
        action="store_true",
        help="Auto-discover forked repositories in addition to original repositories",
    )
    args = parser.parse_args()

    # Terminal styling (auto-disabled in non-TTY environments like GitHub Actions)
    use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    BOLD   = "\033[1m"  if use_color else ""
    DIM    = "\033[2m"  if use_color else ""
    GREEN  = "\033[92m" if use_color else ""
    YELLOW = "\033[93m" if use_color else ""
    CYAN   = "\033[96m" if use_color else ""
    RESET  = "\033[0m"  if use_color else ""

    token, token_source = ("", "offline") if args.offline else resolve_github_token()
    offline_mode = args.offline
    deep_mode = args.deep or bool(token)

    with open(MASTER_FILE, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

    profile_data["schema_version"] = SCHEMA_VERSION
    profile = profile_data.setdefault("profile", {})
    profile.setdefault(
        "roles",
        [
            "Full-Stack Web Developer",
            "AI & Machine Learning Builder",
            "C++ & Database Engineer",
            "Open-Source Problem Solver",
        ],
    )

    prev_stars_total = sum(
        r.get("github_metadata", {}).get("stars", 0)
        for r in profile_data.get("repositories", [])
    )

    live_by_name = {}
    live_by_id = {}
    live_user = None

    if not offline_mode:
        try:
            live_user = fetch_json(f"https://api.github.com/users/{USERNAME}", token)
            live_repos = fetch_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100", token)
            live_by_name = {repo["name"]: repo for repo in live_repos}
            live_by_id = {repo["id"]: repo for repo in live_repos if "id" in repo}
        except RateLimitError as err:
            print(f"{YELLOW}⚠ {err}.{RESET} Falling back to offline mode ({MASTER_FILE.name}).")
            if not token:
                print(f"{DIM}  Tip: Add GITHUB_TOKEN=... to .env or run `gh auth login` for 5,000 req/hr.{RESET}")
            offline_mode = True
            deep_mode = False
        except urllib.error.URLError as err:
            print(f"{YELLOW}⚠ Network error ({err}).{RESET} Falling back to offline mode.")
            offline_mode = True
            deep_mode = False

    matched_live_ids = set()
    updated_count = 0
    renamed_repos = []
    added_repos = []

    for repo in profile_data.get("repositories", []):
        old_name = repo["name"]
        ensure_uniform_repo_schema(repo)
        meta = repo["github_metadata"]
        links = repo["links"]
        tech = repo["tech_stack"]

        # Resolve renamed repository via stored github_id or REPO_ALIASES
        live = None
        if not offline_mode:
            stored_id = meta.get("github_id")
            if stored_id and stored_id in live_by_id:
                live = live_by_id[stored_id]
            else:
                canonical_name = REPO_ALIASES.get(old_name, old_name)
                live = live_by_name.get(canonical_name)

            if live:
                if "id" in live:
                    matched_live_ids.add(live["id"])
                if live["name"] != old_name:
                    if old_name not in meta["aliases"]:
                        meta["aliases"].append(old_name)
                    repo["name"] = live["name"]
                    repo["full_name"] = live.get("full_name") or f"{USERNAME}/{live['name']}"
                    renamed_repos.append(f"{old_name} -> {live['name']}")
        elif old_name in REPO_ALIASES:
            new_name = REPO_ALIASES[old_name]
            if old_name not in meta["aliases"]:
                meta["aliases"].append(old_name)
            repo["name"] = new_name
            repo["full_name"] = f"{USERNAME}/{new_name}"
            renamed_repos.append(f"{old_name} -> {new_name}")

        name = repo["name"]

        # Sync live GitHub API metadata
        if live:
            meta["github_id"] = live.get("id")
            meta["node_id"] = live.get("node_id")
            meta["full_name"] = live.get("full_name") or f"{USERNAME}/{name}"
            repo["full_name"] = meta["full_name"]
            repo["visibility"] = "private" if live.get("private") else "public"

            if live.get("html_url"):
                links["repo_url"] = live["html_url"]
            if live.get("homepage"):
                links["live_demo_url"] = live["homepage"]
            if live.get("clone_url"):
                links["clone_url"] = live["clone_url"]
            links["has_pages"] = bool(live.get("has_pages", False))

            meta["default_branch"] = live.get("default_branch", meta.get("default_branch"))
            meta["topics"] = live.get("topics", meta.get("topics", []))
            meta["stars"] = live.get("stargazers_count", 0)
            meta["forks"] = live.get("forks_count", 0)
            meta["watchers"] = live.get("watchers_count", 0)
            meta["open_issues"] = live.get("open_issues_count", 0)
            meta["size_kb"] = live.get("size", 0)
            if live.get("created_at"):
                meta["created_at"] = live["created_at"][:10]
            if live.get("pushed_at"):
                meta["last_updated"] = live["pushed_at"][:10]

            license_info = live.get("license")
            if license_info and license_info.get("spdx_id") not in (None, "NOASSERTION"):
                meta["license"] = license_info["spdx_id"]

            repo["lifecycle"] = compute_lifecycle(
                live.get("created_at"),
                live.get("pushed_at"),
                bool(live.get("fork", False)),
                bool(live.get("archived", False)),
                bool(live.get("is_template", False)),
            )

            # Deep enrichment: language byte percentages & latest release tag
            if deep_mode:
                try:
                    raw_langs = fetch_json(f"https://api.github.com/repos/{USERNAME}/{name}/languages", token)
                    tech["language_breakdown"] = format_language_breakdown(raw_langs)

                    latest_rel = fetch_json(
                        f"https://api.github.com/repos/{USERNAME}/{name}/releases/latest",
                        token,
                        allow_not_found=True,
                    )
                    meta["latest_release"] = (
                        {
                            "tag": latest_rel.get("tag_name"),
                            "published_at": (latest_rel.get("published_at") or "")[:10] or None,
                            "url": latest_rel.get("html_url"),
                        }
                        if latest_rel
                        else None
                    )
                except (RateLimitError, urllib.error.URLError) as err:
                    print(f"{YELLOW}⚠ Deep enrichment paused ({err});{RESET} keeping core repo sync.")
                    deep_mode = False

            updated_count += 1
        elif name != old_name:
            links["repo_url"] = f"https://github.com/{USERNAME}/{name}"

    # Auto-discover new repositories on GitHub not yet in github-profile.json
    if not offline_mode and live_by_name:
        existing_names = {r["name"] for r in profile_data.get("repositories", [])}
        for live_name, live in sorted(live_by_name.items()):
            if live.get("id") in matched_live_ids or live_name in existing_names:
                continue
            if live.get("fork") and not args.include_forks:
                continue

            new_record = build_new_repo_record(live)
            if deep_mode:
                try:
                    raw_langs = fetch_json(f"https://api.github.com/repos/{USERNAME}/{live_name}/languages", token)
                    new_record["tech_stack"]["language_breakdown"] = format_language_breakdown(raw_langs)
                except (RateLimitError, urllib.error.URLError):
                    deep_mode = False

            profile_data["repositories"].append(new_record)
            added_repos.append(live_name)

    # Update sync metadata & user profile stats
    today_iso = date.today().isoformat()
    profile_data["last_synced"] = today_iso
    stats = profile.setdefault("stats", {})

    if live_user:
        if live_user.get("bio") is not None:
            profile["bio"] = live_user["bio"]
        if live_user.get("location") is not None:
            profile["location"] = live_user["location"]
        if live_user.get("company") is not None:
            profile["company"] = live_user["company"]
        if isinstance(live_user.get("followers"), int):
            stats["followers"] = live_user["followers"]
        if isinstance(live_user.get("following"), int):
            stats["following"] = live_user["following"]
        if isinstance(live_user.get("public_repos"), int):
            stats["public_repos"] = live_user["public_repos"]

    all_repos = profile_data.get("repositories", [])
    new_stars_total = sum(r.get("github_metadata", {}).get("stars", 0) for r in all_repos)
    stats["extracted_repositories_count"] = len(all_repos)
    stats["total_stars"] = new_stars_total
    stats["total_forks"] = sum(r.get("github_metadata", {}).get("forks", 0) for r in all_repos)
    profile["repository_index"] = [r["name"] for r in all_repos]

    # Append rolling 10-entry audit log
    history = profile_data.setdefault("sync_history", [])
    history.insert(
        0,
        {
            "date": today_iso,
            "mode": "offline" if offline_mode else ("deep" if deep_mode else "standard"),
            "auth": token_source,
            "tracked_repos": len(all_repos),
            "total_stars": new_stars_total,
            "star_delta": new_stars_total - prev_stars_total,
            "added": added_repos,
            "renamed": renamed_repos,
        },
    )
    del history[10:]

    # 1. Save updated master JSON
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2, ensure_ascii=False)

    # 2. Export individual JSONs & clean up orphaned files from renamed/removed repos
    INDIVIDUAL_DIR.mkdir(parents=True, exist_ok=True)
    active_filenames = set()
    for repo in all_repos:
        filename = f"{repo['name']}.json"
        active_filenames.add(filename)
        with open(INDIVIDUAL_DIR / filename, "w", encoding="utf-8") as f:
            json.dump(repo, f, indent=2, ensure_ascii=False)

    removed_orphans = 0
    for existing_file in INDIVIDUAL_DIR.glob("*.json"):
        if existing_file.name not in active_filenames:
            existing_file.unlink()
            removed_orphans += 1

    # 3. Generate portfolio-data.js for your website
    generate_portfolio_js(profile_data, PORTFOLIO_JS_OUT)

    mode_label = (
        f"{YELLOW}Offline mode{RESET}"
        if offline_mode
        else f"Synced {BOLD}{updated_count}{RESET} live repos {DIM}({token_source}){RESET}"
    )
    exports_rel = INDIVIDUAL_DIR.relative_to(ROOT_DIR).as_posix()
    bundle_rel = PORTFOLIO_JS_OUT.relative_to(ROOT_DIR).as_posix()

    print(f"\n{BOLD}{GREEN}✔ Portfolio Sync Complete{RESET}")
    print(f"{DIM}{'─' * 50}{RESET}")
    print(f"  {DIM}Mode:{RESET}      {mode_label}")
    print(
        f"  {DIM}Changes:{RESET}   "
        f"{GREEN}+{len(added_repos)} added{RESET}  "
        f"{DIM}•{RESET}  {len(renamed_repos)} renamed  "
        f"{DIM}•{RESET}  {removed_orphans} cleaned"
    )
    print(f"  {DIM}Exports:{RESET}   {CYAN}{len(active_filenames)}{RESET} files → {exports_rel}/")
    print(f"  {DIM}Bundle:{RESET}    {bundle_rel} {DIM}(schema v{SCHEMA_VERSION}){RESET}")
    print(f"{DIM}{'─' * 50}{RESET}\n")


if __name__ == "__main__":
    main()