#!/usr/bin/env python3
"""采集 TypeRota 的工作数据，写到 data/stats.json。

零第三方依赖：只用标准库。CI 上直接用 runner 自带的 python3。

    GH_TOKEN=xxx python3 tools/collect.py

口径：
  提交 / 新增行 / 删除行 / 文件数 —— 以 typerota@163.com 为 author 的提交，
  逐条查 /repos/{repo}/commits/{sha} 拿 numstat。
  私有仓库（oddity-agent-memory）只有在 token 有读权限时才会被统计到；
  想连私有仓库一起算，就给 workflow 配 GH_PAT。
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
LOGIN = "TypeRota"
EMAIL = "typerota@163.com"

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "stats.json"


def token():
    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(key):
            return os.environ[key]
    return ""


def call(path, payload=None):
    url = path if path.startswith("http") else API + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "TypeRota-profile")
    if token():
        req.add_header("Authorization", "Bearer " + token())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")[:200]
        sys.exit(f"GitHub API {exc.code} on {url}: {body}")


def search_count(query, kind="issues"):
    data = call(f"/search/{kind}?q=" + urllib.parse.quote(query) + "&per_page=1")
    return data.get("total_count", 0)


def commits():
    """返回 (提交列表, 新增行, 删除行, 文件数, 仓库集合)。"""
    items, added, deleted, files, repos = [], 0, 0, 0, set()
    seen = set()
    for page in range(1, 4):
        data = call(f"/search/commits?q=author-email:{EMAIL}&per_page=100&page={page}")
        batch = data.get("items") or []
        if not batch:
            break
        items.extend(batch)
        if len(batch) < 100:
            break
    for item in items:
        key = (item["repository"]["full_name"], item["sha"])
        if key in seen:
            continue
        seen.add(key)
        repos.add(key[0])
        detail = call(f"/repos/{key[0]}/commits/{key[1]}")
        for item in detail.get("files") or []:
            path = item.get("filename", "")
            # 生成物不算代码：画出来的 SVG 和账本 JSON 会把数字撑成噪音
            if path.startswith("assets/") or path.startswith("data/"):
                continue
            added += item.get("additions", 0)
            deleted += item.get("deletions", 0)
            files += 1
    return items, added, deleted, files, repos


def contributions():
    query = ('{user(login:"%s"){contributionsCollection{contributionCalendar{'
             'totalContributions weeks{contributionDays{contributionCount date}}}}}}' % LOGIN)
    data = call("/graphql", {"query": query})
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[{"n": d["contributionCount"], "d": d["date"]} for d in w["contributionDays"]]
             for w in cal["weeks"]]
    flat = [d for w in weeks for d in w]
    return cal["totalContributions"], {"start": flat[0]["d"], "end": flat[-1]["d"], "weeks": weeks}


def main():
    import urllib.parse  # noqa: F401  (search_count 里用到)

    profile = call(f"/users/{LOGIN}")
    items, added, deleted, files, repos = commits()
    total, calendar = contributions()

    stats = {
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone(__import__("datetime").timedelta(hours=8))
        ).strftime("%Y-%m-%d %H:%M +08:00"),
        "login": LOGIN,
        "name": profile.get("name") or LOGIN,
        "born": (profile.get("created_at") or "")[:10],
        "avatars": profile.get("avatar_url"),
        "commits": len(items),
        "added": added,
        "deleted": deleted,
        "files": files,
        "repo_count": len(repos),
        "repos": sorted(repos),
        "reviewed": search_count(f"reviewed-by:{LOGIN}"),
        "commented": search_count(f"commenter:{LOGIN}"),
        "contributions": total,
        "calendar": calendar,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n")
    print(f"data/stats.json · {stats['commits']} 提交 · +{added}/-{deleted} · "
          f"{stats['files']} 文件 · {stats['repo_count']} 仓库 · "
          f"评审 {stats['reviewed']} · 讨论 {stats['commented']} · 贡献 {total}")


if __name__ == "__main__":
    main()