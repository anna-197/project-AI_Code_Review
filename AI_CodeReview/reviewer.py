#!/usr/bin/env python3
import os
import sys
import requests
from openai import OpenAI

def get_pr_files(repo, pr_number, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def build_prompt(files):
    diffs = []
    for f in files:
        if f.get("patch"):
            diffs.append(f"File: {f['filename']}\n{f['patch']}\n")
    return "You are a senior engineer. Review these code changes:\n\n" + "\n\n".join(diffs)

def get_openai_review(prompt):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert code reviewer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

def post_comment(repo, pr_number, token, review):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}"}
    data = {"body": review}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def main():
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.ent("PR_NUMBER")
    token = os.environ.get("GITHUB_TOKEN")

    if not repo or not pr_number or not token:
        print("Missing required environment variables.")
        sys.exit(1)

    print(f"Fetching PR #{pr_number} from {repo}...")
    files = get_pr_files(repo, pr_number, token)
    prompt = build_prompt(files)
    print("Sending to OpenAI...")
    review = get_openai_review(prompt)
    print("Posting review...")
    post_comment(repo, pr_number, token, review)
    print("✅ Review posted!")

if __name__ == "__main__":
    main()
