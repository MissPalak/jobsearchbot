import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

KEYWORDS = ["HR Recruiter", "Talent Acquisition"]


def parse_posting_date(text):
    text = text.lower()
    if "today" in text or "just" in text or "hour" in text:
        return 0
    m = re.search(r"(\d+)\+?\s*day", text)
    if m:
        return int(m.group(1))
    return None


def scrape_indeed():
    jobs = []
    seen = set()
    base_url = "https://in.indeed.com/jobs"
    for kw in KEYWORDS:
        params = {"q": kw, "l": "Remote", "fromage": "15"}
        resp = requests.get(base_url, params=params, headers=HEADERS, timeout=30)
        time.sleep(2)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("div.job_seen_beacon"):
            if card.select_one("span.sponsoredGray"):
                continue
            title_span = card.select_one("h2.jobTitle span")
            if not title_span:
                continue
            if title_span.text.lower() == "new":
                title_span = title_span.find_next_sibling("span")
            title = title_span.get_text(strip=True)
            company = card.select_one("span.companyName")
            if company:
                company = company.get_text(strip=True)
            else:
                company = ""
            location = card.select_one("div.companyLocation")
            location = location.get_text(strip=True) if location else ""
            summary = card.select_one("div.job-snippet")
            summary = summary.get_text(" ", strip=True) if summary else ""
            date = card.select_one("span.date")
            date_text = date.get_text(strip=True) if date else ""
            if parse_posting_date(date_text) is not None and parse_posting_date(date_text) > 15:
                continue
            link = card.find("a", href=True)
            link = urljoin("https://in.indeed.com", link['href']) if link else ""
            uid = (title, company)
            if uid in seen:
                continue
            seen.add(uid)
            jobs.append({
                "Job Title": title,
                "Company Name": company,
                "Location": location,
                "Job Summary": summary,
                "Posting Date": date_text,
                "Apply Link": link,
                "Source": "Indeed"
            })
    print(f"Indeed: {len(jobs)} jobs found")
    return jobs


def scrape_naukri():
    jobs = []
    seen = set()
    base_url = "https://www.naukri.com/"
    for kw in KEYWORDS:
        query = kw.replace(" ", "-") + "-jobs"
        url = urljoin(base_url, query)
        params = {"k": kw, "remote": "true", "where": "work from home", "jobAge": "15"}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        time.sleep(2)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("article.jobTuple"):
            if card.get("data-tn-component") == "organicJob" and card.find("span", string=re.compile("Sponsored")):
                continue
            title_tag = card.select_one("a.title")
            title = title_tag.get_text(strip=True) if title_tag else ""
            company = card.select_one("a.subTitle")
            company = company.get_text(strip=True) if company else ""
            location = card.select_one("li.location")
            location = location.get_text(strip=True) if location else ""
            summary = card.select_one("div.job-description")
            summary = summary.get_text(" ", strip=True) if summary else ""
            date = card.select_one("span.type"),
            date_text = card.select_one("span.job-post-date")
            date_text = date_text.get_text(strip=True) if date_text else ""
            if parse_posting_date(date_text) is not None and parse_posting_date(date_text) > 15:
                continue
            link = title_tag['href'] if title_tag else ""
            uid = (title, company)
            if uid in seen:
                continue
            seen.add(uid)
            jobs.append({
                "Job Title": title,
                "Company Name": company,
                "Location": location,
                "Job Summary": summary,
                "Posting Date": date_text,
                "Apply Link": link,
                "Source": "Naukri"
            })
    print(f"Naukri: {len(jobs)} jobs found")
    return jobs


def scrape_shine():
    jobs = []
    seen = set()
    base_url = "https://www.shine.com/job-search/"
    for kw in KEYWORDS:
        query = kw.lower().replace(" ", "-") + "-jobs"
        url = urljoin(base_url, query)
        params = {"q": kw, "location": "work from home", "posted": "15"}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        time.sleep(2)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("li.search_listing"):
            if card.find(string=re.compile("Sponsored")):
                continue
            title_tag = card.select_one("a.job_title")
            title = title_tag.get_text(strip=True) if title_tag else ""
            company = card.select_one("span.companyName")
            company = company.get_text(strip=True) if company else ""
            location = card.select_one("span.loc")
            location = location.get_text(strip=True) if location else ""
            summary = card.select_one("div.job_description")
            summary = summary.get_text(" ", strip=True) if summary else ""
            date_text = card.select_one("span.date").get_text(strip=True) if card.select_one("span.date") else ""
            if parse_posting_date(date_text) is not None and parse_posting_date(date_text) > 15:
                continue
            link = urljoin("https://www.shine.com", title_tag['href']) if title_tag else ""
            uid = (title, company)
            if uid in seen:
                continue
            seen.add(uid)
            jobs.append({
                "Job Title": title,
                "Company Name": company,
                "Location": location,
                "Job Summary": summary,
                "Posting Date": date_text,
                "Apply Link": link,
                "Source": "Shine"
            })
    print(f"Shine: {len(jobs)} jobs found")
    return jobs


def scrape_linkedin():
    jobs = []
    seen = set()
    base_url = "https://www.linkedin.com/jobs/search"
    for kw in KEYWORDS:
        params = {
            "keywords": kw,
            "location": "India",
            "f_WT": "2",
            "f_TPR": "r1296000",  # 15 days
            "f_WRA": "1"
        }
        resp = requests.get(base_url, params=params, headers=HEADERS, timeout=30)
        time.sleep(2)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("div.base-card"):
            title_tag = card.select_one("h3.base-search-card__title")
            title = title_tag.get_text(strip=True) if title_tag else ""
            company = card.select_one("h4.base-search-card__subtitle")
            company = company.get_text(strip=True) if company else ""
            location = card.select_one("span.job-search-card__location")
            location = location.get_text(strip=True) if location else ""
            summary = ""
            date_tag = card.select_one("time")
            date_text = date_tag.get("datetime", "") if date_tag else ""
            if parse_posting_date(date_text) is not None and parse_posting_date(date_text) > 15:
                continue
            link_tag = card.select_one("a.base-card__full-link")
            link = link_tag['href'] if link_tag else ""
            uid = (title, company)
            if uid in seen:
                continue
            seen.add(uid)
            jobs.append({
                "Job Title": title,
                "Company Name": company,
                "Location": location,
                "Job Summary": summary,
                "Posting Date": date_text,
                "Apply Link": link,
                "Source": "LinkedIn"
            })
    print(f"LinkedIn: {len(jobs)} jobs found")
    return jobs


def scrape_glassdoor():
    jobs = []
    seen = set()
    base_url = "https://www.glassdoor.co.in/Job/jobs.htm"
    for kw in KEYWORDS:
        params = {
            "sc.keyword": kw,
            "locT": "C",
            "locId": "0",
            "jobType": "",
            "radius": "0",
            "fromAge": "15",
            "remoteWorkType": "1"
        }
        resp = requests.get(base_url, params=params, headers=HEADERS, timeout=30)
        time.sleep(2)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("li.react-job-listing"):
            if card.get("data-sponsored") == "true":
                continue
            title_tag = card.select_one("a.jobLink")
            title = title_tag.get_text(strip=True) if title_tag else ""
            company = card.select_one("div.jobHeader a")
            company = company.get_text(strip=True) if company else ""
            location = card.select_one("span.pr-xxsm")
            location = location.get_text(strip=True) if location else ""
            summary = ""
            date_text = card.select_one("div.d-flex div.css-1d3xvsm").get_text(strip=True) if card.select_one("div.d-flex div.css-1d3xvsm") else ""
            if parse_posting_date(date_text) is not None and parse_posting_date(date_text) > 15:
                continue
            link = urljoin("https://www.glassdoor.co.in", title_tag['href']) if title_tag else ""
            uid = (title, company)
            if uid in seen:
                continue
            seen.add(uid)
            jobs.append({
                "Job Title": title,
                "Company Name": company,
                "Location": location,
                "Job Summary": summary,
                "Posting Date": date_text,
                "Apply Link": link,
                "Source": "Glassdoor"
            })
    print(f"Glassdoor: {len(jobs)} jobs found")
    return jobs


def main():
    all_jobs = []
    for scraper in [scrape_indeed, scrape_naukri, scrape_shine, scrape_linkedin, scrape_glassdoor]:
        try:
            jobs = scraper()
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"Error scraping {scraper.__name__}: {e}")
    if all_jobs:
        df = pd.DataFrame(all_jobs)
        df.drop_duplicates(subset=["Job Title", "Company Name"], inplace=True)
        df.to_csv("remote_hr_jobs_india.csv", index=False)
        print(f"Total jobs saved: {len(df)}")
    else:
        print("No jobs found")


if __name__ == "__main__":
    main()
