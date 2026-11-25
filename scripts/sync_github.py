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

HEADERS = {"User-Agent": f"{USERNAME}-portfolio-sync"}

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

# Initial portfolio display presets matching your exact current portfolio-data.js
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
    "cs-mcq-hub": {
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


def fetch_json(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def infer_category(repo: dict) -> str:
    cat = repo.get("category", "").lower()
    if any(k in cat for k in ("ai", "computer vision", "deep learning", "ml")):
        return "ai"
    if any(k in cat for k in ("cli", "database", "c++", "sql", "systems")):
        return "systems"
    return "web"


def generate_portfolio_js(profile_data: dict, out_path: str):
    email = profile_data.get("profile", {}).get("links", {}).get("email", "imasad789@gmail.com")
    roles = profile_data.get("profile", {}).get(
        "roles",
        [
            "Full-Stack Web Developer",
            "AI & Machine Learning Builder",
            "C++ & Database Engineer",
            "Open-Source Problem Solver",
        ],
    )

    featured_repos = [
        r for r in profile_data.get("repositories", [])
        if r.get("portfolio", {}).get("featured") is True
    ]
    featured_repos.sort(key=lambda r: r.get("portfolio", {}).get("order", 999))

    project_entries = []
    for repo in featured_repos:
        p = repo.get("portfolio", {})
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
        })

    lines = [
        "// AUTO-GENERATED BY sync_github.py FROM github-profile.json — DO NOT EDIT MANUALLY",
        f"export const CONTACT_EMAIL = {json.dumps(email)};",
        "",
        f"export const ROLES = {json.dumps(roles, indent=2)};",
        "",
        f"export const PROJECTS = {json.dumps(project_entries, indent=2, ensure_ascii=False)};",
        "",
    ]

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    with open(MASTER_FILE, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

    # Ensure profile.roles is stored in master JSON
    profile_data.setdefault("profile", {}).setdefault(
        "roles",
        [
            "Full-Stack Web Developer",
            "AI & Machine Learning Builder",
            "C++ & Database Engineer",
            "Open-Source Problem Solver",
        ],
    )

    # Fetch live GitHub stats
    api_url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100"
    live_repos = fetch_json(api_url)
    live_by_name = {repo["name"]: repo for repo in live_repos}

    updated_count = 0
    for repo in profile_data.get("repositories", []):
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

        # Sync live GitHub API metadata
        if name in live_by_name:
            live = live_by_name[name]
            meta = repo.setdefault("github_metadata", {})
            repo["visibility"] = "private" if live.get("private") else "public"
            if live.get("homepage"):
                repo["links"]["live_demo_url"] = live["homepage"]
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

    # Update sync metadata
    profile_data["last_synced"] = date.today().isoformat()
    stats = profile_data["profile"].setdefault("stats", {})
    stats["extracted_repositories_count"] = len(profile_data.get("repositories", []))
    profile_data["profile"]["repository_index"] = [
        r["name"] for r in profile_data.get("repositories", [])
    ]

    # 1. Save updated master JSON
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2, ensure_ascii=False)

    # 2. Export individual JSONs for Google Drive backup
    os.makedirs(INDIVIDUAL_DIR, exist_ok=True)
    for repo in profile_data.get("repositories", []):
        out_path = os.path.join(INDIVIDUAL_DIR, f"{repo['name']}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(repo, f, indent=2, ensure_ascii=False)

    # 3. Generate portfolio-data.js for your website
    generate_portfolio_js(profile_data, PORTFOLIO_JS_OUT)

    print(f"✅ Synced {updated_count} repos in '{MASTER_FILE}'.")
    print(f"📁 Exported {len(profile_data['repositories'])} files to '{INDIVIDUAL_DIR}/'.")
    print(f"🌐 Generated '{PORTFOLIO_JS_OUT}' for your portfolio site.")


if __name__ == "__main__":
    main()