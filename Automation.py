from pathlib import Path
import re
import subprocess
import urllib.request
from datetime import datetime

REPO_PATH=Path.home()/"30-days-of-cybersecurity"
README_PATH=REPO_PATH/"README.md"
AUTO_PUSH=False
GENERATE_X_POST=True

IGNORED_NAMES={
    ".git",
    ".github",
    ".gitignore",
    ".DS_Store",
    "Thumbs.db",
}

def print_header():
    print()
    print("="*60)
    print("🛡️ 30 DAYS OF CYBERSECURITY AUTOMATION")
    print("="*60)
    print()

def success(message):
    print(f"✅ {message}")

def info(message):
    print(f"ℹ️ {message}")

def warning(message):
    print(f"⚠️ {message}")

def error(message):
    print(f"❌ {message}")

def check_repository():
    if not REPO_PATH.exists():
        error("Repository not found:")
        print(f"   {REPO_PATH}")
        print()
        print("Edit REPO_PATH at the top of automate.py.")
        return False

    if not README_PATH.exists():
        error("README.md was not found.")
        print(f"Expected: {README_PATH}")
        return False

    return True

def internet_available():
    try:
        urllib.request.urlopen("https://www.google.com",timeout=3)
        return True
    except Exception:
        return False

def get_day_folders():
    days={}

    for item in REPO_PATH.iterdir():
        if not item.is_dir():
            continue

        match=re.match(r"^Day-(\d{2})-(.+)$",item.name,re.IGNORECASE)

        if not match:
            continue

        day_number=int(match.group(1))
        topic=match.group(2).replace("-"," ")

        days[day_number]={
            "folder":item,
            "topic":topic
        }

    return days

def folder_has_work(folder):
    for item in folder.rglob("*"):
        if not item.is_file():
            continue

        if item.name in IGNORED_NAMES:
            continue

        if item.suffix.lower() in {".tmp",".temp",".log"}:
            continue

        return True

    return False

def get_readme_days():
    content=README_PATH.read_text(encoding="utf-8")
    days={}

    pattern=re.compile(
        r"\|\s*Day\s+(\d{2})\s*\|"
        r"\s*(.*?)\s*\|"
        r"\s*(.*?)\s*\|?",
        re.IGNORECASE
    )

    for match in pattern.finditer(content):
        day=int(match.group(1))
        topic=match.group(2).strip()
        status=match.group(3).strip()

        days[day]={
            "topic":topic,
            "status":status
        }

    return days

def determine_status(day_number,day_folders,readme_days):
    folder_data=day_folders.get(day_number)

    if folder_data is None:
        return "⬜"

    folder=folder_data["folder"]

    if not folder_has_work(folder):
        return "⬜"

    return "🟨 In Progress"

def find_completed_days(day_folders):
    completed=[]

    for day_number,data in day_folders.items():
        folder=data["folder"]

        if folder_has_work(folder):
            completed.append(day_number)

    return sorted(completed)

def find_current_day(day_folders):
    for day in range(1,31):
        if day not in day_folders:
            continue

        folder=day_folders[day]["folder"]

        if not folder_has_work(folder):
            return day

    completed=find_completed_days(day_folders)

    if not completed:
        return 1

    next_day=max(completed)+1

    if next_day<=30:
        return next_day

    return None

def update_readme(day_folders):
    content=README_PATH.read_text(encoding="utf-8")
    original_content=content

    completed_days=set(find_completed_days(day_folders))
    current_day=find_current_day(day_folders)

    for day in range(1,31):
        if day in completed_days:
            new_status="✅ Completed"
        elif current_day==day:
            new_status="🟨 In Progress"
        else:
            new_status="⬜"

        pattern=re.compile(
            rf"(\|\s*Day\s+{day:02d}\s*\|"
            rf".*?\|)\s*.*?(\s*\|?)\s*$",
            re.MULTILINE
        )

        match=pattern.search(content)

        if not match:
            continue

        line=match.group(0)
        parts=line.split("|")

        if len(parts)<4:
            continue

        parts[3]=f" {new_status} "
        new_line="|".join(parts)

        content=(
            content[:match.start()]
            +new_line
            +content[match.end():]
        )

    if content!=original_content:
        README_PATH.write_text(content,encoding="utf-8")
        success("README.md updated.")
    else:
        info("README.md already up to date.")

    return current_day

def generate_x_post(day_number,day_data):
    topic=day_data["topic"]
    today=datetime.now().strftime("%B %d, %Y")

    post=f"""Day {day_number}/30 🛡️

Completed: {topic}

Today I continued my 30 Days of Cybersecurity challenge by learning, practicing, and documenting what I learned.

The goal isn't just to consume information — it's to build real skills and proof of work.

One day at a time. 🔐

#{topic.replace(" ","").replace("-","")} #Cybersecurity #Python #LearningInPublic

Date: {today}
"""

    x_folder=REPO_PATH/".automation"
    x_folder.mkdir(exist_ok=True)

    post_file=x_folder/f"Day-{day_number:02d}-X-Post.txt"

    post_file.write_text(post,encoding="utf-8")

    success(f"X post saved to {post_file}")

    print()
    print("-"*60)
    print("📝 X POST")
    print("-"*60)
    print(post)
    print("-"*60)

    return post

def run_git(command):
    try:
        result=subprocess.run(
            command,
            cwd=REPO_PATH,
            capture_output=True,
            text=True
        )

        if result.returncode!=0:
            error(
                result.stderr.strip()
                or "Git command failed."
            )
            return False

        if result.stdout.strip():
            print(result.stdout.strip())

        return True

    except Exception as e:
        error(str(e))
        return False

def git_status():
    result=subprocess.run(
        ["git","status","--porcelain"],
        cwd=REPO_PATH,
        capture_output=True,
        text=True
    )

    return result.stdout.strip()

def git_commit_and_push(day_number):
    if not git_status():
        info("No Git changes detected.")
        return

    success("Git changes detected.")

    if not run_git(["git","add","."]):
        return

    commit_message=(
        f"Day {day_number:02d}: "
        f"Cybersecurity Challenge Update"
    )

    if not run_git(["git","commit","-m",commit_message]):
        return

    success("Git commit created.")

    if not AUTO_PUSH:
        warning(
            "AUTO_PUSH is disabled. "
            "Nothing was pushed to GitHub."
        )
        return

    if not internet_available():
        warning(
            "No internet connection. "
            "GitHub push skipped."
        )
        return

    if run_git(["git","push"]):
        success("Successfully pushed to GitHub.")

def main():
    print_header()

    if not check_repository():
        return

    success("Cybersecurity repository found.")

    day_folders=get_day_folders()

    if not day_folders:
        error("No Day folders were found.")
        print("Expected folders such as:")
        print("Day-01-Networking/")
        return

    print(f"📁 Found {len(day_folders)} Day folders.")

    completed=find_completed_days(day_folders)

    print(f"📊 Days with work: {completed}")

    current_day=find_current_day(day_folders)

    if current_day:
        print(f"🎯 Current day: Day {current_day:02d}")
    else:
        print("🏆 All available days completed!")

    update_readme(day_folders)

    if GENERATE_X_POST and completed:
        latest_day=completed[-1]

        if latest_day in day_folders:
            generate_x_post(
                latest_day,
                day_folders[latest_day]
            )

    if completed:
        latest_day=completed[-1]
        git_commit_and_push(latest_day)

    if internet_available():
        success("Internet connection detected.")
    else:
        warning("No internet connection detected.")

    print()
    print("="*60)
    print("🎉 AUTOMATION COMPLETE")
    print("="*60)
    print()

if __name__=="__main__":
    main()
