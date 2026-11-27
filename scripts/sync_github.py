import argparse
import json
import os
import urllib.request
from datetime import date
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
USERNAME = "asad-ali-sajjad"
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


def build_headers() -> dict:
    headers = {
        "User-Agent": f"{USERNAME}-portfolio-sync",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_json(url: str):
    req = urllib.request.Request(url, headers=build_headers())
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def infer_category(repo: dict) -> str:
    cat = repo.get("category", "").lower()
    if any(k in cat for k in ("ai", "computer vision", "deep learning", "ml")):
        return "ai"
    if any(k in cat for k in ("cli", "database", "c++", "sql", "systems")):
        return "systems"
    return "web"


def generate_portfolio_js(profile_data: dict, out_path: Path):
    profile = profile_data.get("profile", {})
    email = profile.get("links", {}).get("email", "imasad789@gmail.com")
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

    total_stars = sum(
        r.get("github_metadata", {}).get("stars", 0) for r in repos
    )
    profile_meta = {
        "username": USERNAME,
        "publicRepos": profile.get("stats", {}).get("public_repos", len(repos)),
        "featuredCount": len(featured_repos),
        "totalStars": total_stars,
        "lastSynced": profile_data.get("last_synced", date.today().isoformat()),
    }

    project_entries = []
    for repo in featured_repos:
        p = repo.get("portfolio", {})
        meta = repo.get("github_metadata", {})
        primary_lang = p.get("language") or repo.get("tech_stack", {}).get("primary_language", "JavaScript")
        lang_color = p.get("langColor") or LANG_COLORS.get(primary_lang, "#38bdf8")
        badge = "Pinned" if repo.get("is_pinned") else p.get("badge", "Featured")

        project_entries.append({
            "title": repo["name"],
            "badge": badge,
            "category": p.get("category") or infer_category(repo),
            "language": primary_lang,
            "langColor": lang_color,
            "description": p.get("description") or repo.get("overview", {}).get("description", ""),
            "tags": p.get("tags", []),
            "repoUrl": repo.get("links", {}).get("repo_url"),
            "demoUrl": repo.get("links", {}).get("live_demo_url"),
            "stars": meta.get("stars", 0),
            "forks": meta.get("forks", 0),
            "updatedAt": meta.get("last_updated"),
        })

    lines = [
        "// AUTO-GENERATED BY sync_github.py FROM github-profile.json — DO NOT EDIT MANUALLY",
        f"export const CONTACT_EMAIL = {json.dumps(email)};",
        "",
        f"export const PROFILE_META = {json.dumps(profile_meta, indent=2)};",
        "",
        f"export const ROLES = {json.dumps(roles, indent=2)};",
        "",
        f"export const PROJECTS = {json.dumps(project_entries, indent=2, ensure_ascii=False)};",
        "",
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Sync GitHub metadata and regenerate portfolio-data.js")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip GitHub API network requests and regenerate files from local github-profile.json",
    )
    args = parser.parse_args()

    with open(MASTER_FILE, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

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

    live_by_name = {}
    live_by_id = {}
    live_user = None

    if not args.offline:
        live_user = fetch_json(f"https://api.github.com/users/{USERNAME}")
        live_repos = fetch_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100")
        live_by_name = {repo["name"]: repo for repo in live_repos}
        live_by_id = {repo["id"]: repo for repo in live_repos if "id" in repo}

    updated_count = 0
    renamed_count = 0

    for repo in profile_data.get("repositories", []):
        old_name = repo["name"]
        meta = repo.setdefault("github_metadata", {})
        links = repo.setdefault("links", {})

        # Resolve renamed repository via stored github_id or REPO_ALIASES
        live = None
        if not args.offline:
            stored_id = meta.get("github_id")
            if stored_id and stored_id in live_by_id:
                live = live_by_id[stored_id]
            else:
                canonical_name = REPO_ALIASES.get(old_name, old_name)
                live = live_by_name.get(canonical_name)

            if live and live["name"] != old_name:
                repo["name"] = live["name"]
                renamed_count += 1
        elif old_name in REPO_ALIASES:
            repo["name"] = REPO_ALIASES[old_name]
            renamed_count += 1

        name = repo["name"]

        # Seed or preserve the portfolio block on every repository
        if "portfolio" not in repo:
            if name in DEFAULT_PORTFOLIO_PRESETS:
                repo["portfolio"] = DEFAULT_PORTFOLIO_PRESETS[name].copy()
            else:
                primary_lang = repo.get("tech_stack", {}).get("primary_language", "JavaScript")
                repo["portfolio"] = {
                    "featured": False,
                    "order": 99,
                    "badge": "Pinned" if repo.get("is_pinned") else "Project",
                    "category": infer_category(repo),
                    "language": primary_lang,
                    "langColor": LANG_COLORS.get(primary_lang, "#38bdf8"),
                    "tags": repo.get("tech_stack", {}).get("frameworks_and_libraries", [])[:4],
                }

        # Sync live GitHub API metadata (including repo_url & live_demo_url)
        if live:
            meta["github_id"] = live.get("id")
            repo["visibility"] = "private" if live.get("private") else "public"
            if live.get("html_url"):
                links["repo_url"] = live["html_url"]
            if live.get("homepage"):
                links["live_demo_url"] = live["homepage"]
            meta["default_branch"] = live.get("default_branch", meta.get("default_branch"))
            meta["topics"] = live.get("topics", meta.get("topics", []))
            meta["stars"] = live.get("stargazers_count", 0)
            meta["forks"] = live.get("forks_count", 0)
            if live.get("pushed_at"):
                meta["last_updated"] = live["pushed_at"][:10]
            license_info = live.get("license")
            if license_info and license_info.get("spdx_id") not in (None, "NOASSERTION"):
                meta["license"] = license_info["spdx_id"]
            updated_count += 1
        elif name != old_name:
            links["repo_url"] = f"https://github.com/{USERNAME}/{name}"

    # Update sync metadata & profile stats
    profile_data["last_synced"] = date.today().isoformat()
    stats = profile.setdefault("stats", {})
    if live_user and isinstance(live_user.get("public_repos"), int):
        stats["public_repos"] = live_user["public_repos"]
    stats["extracted_repositories_count"] = len(profile_data.get("repositories", []))
    profile["repository_index"] = [r["name"] for r in profile_data.get("repositories", [])]

    # 1. Save updated master JSON
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2, ensure_ascii=False)

    # 2. Export individual JSONs & clean up orphaned files from renamed/removed repos
    INDIVIDUAL_DIR.mkdir(parents=True, exist_ok=True)
    active_filenames = set()
    for repo in profile_data.get("repositories", []):
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

    mode_label = "offline mode" if args.offline else f"synced {updated_count} live repos"
    print(f"✅ Completed ({mode_label}; renamed: {renamed_count}; cleaned orphans: {removed_orphans}).")
    print(f"📁 Exported {len(active_filenames)} files to '{INDIVIDUAL_DIR}'.")
    print(f"🌐 Generated '{PORTFOLIO_JS_OUT}'.")


if __name__ == "__main__":
    main()