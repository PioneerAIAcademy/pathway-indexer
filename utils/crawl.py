import asyncio
import datetime
import hashlib
import json
import os
import time
import zlib

import nest_asyncio
import pandas as pd
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from utils.tools import create_folder

nest_asyncio.apply()


def generate_content_hash(content):
    """Generate a SHA-256 hash of the content."""
    return hashlib.sha256(content).hexdigest()


def generate_hash_filename(url):
    """Generate a hash of the URL to use as a filename."""
    url_hash = zlib.crc32(url.encode())
    file_name = f"{url_hash:x}"
    return file_name


# whatsapp function
async def get_whatsapp_content(url):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()

    post_xpath = "/html/body/div[1]/div/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div[2]/div/div/div[1]/div/div/div/div/div/div/div"

    print(url)
    await page.goto(url)
    await page.wait_for_load_state()
    post = await page.query_selector(f"xpath={post_xpath}")
    post_content = await post.inner_html()
    await browser.close()
    if post:
        return post_content
    else:
        print(f"Error with {url}")
        return None


async def fetch_content_with_playwright(url, filepath):
    """Fetch the content of a URL using Playwright and save it to a file."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)  # 60 seconds timeout
            time.sleep(5)
            content = await page.content()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Error loading {url}: {e}")
        await browser.close()


async def fetch_content_from_student_services(urls):
    """
    Extract all tabs from CourseDog student services pages.

    Args:
        urls: List of dicts with 'url' and 'title' for each tab

    Returns:
        Combined HTML content from all tabs
    """
    plw = await async_playwright().start()
    brwsr = await plw.chromium.launch(headless=True)
    pg = await brwsr.new_page()

    all_content = []

    for url_info in urls:
        tab_url = url_info["url"]
        tab_title = url_info["title"]
        print(f"crawling subpage: {tab_url}")

        try:
            # Navigate and wait for network to be idle
            await pg.goto(tab_url, wait_until="networkidle", timeout=30000)
            await pg.wait_for_selector("article.main-content", timeout=10000)
            # Wait for JS-rendered content to stabilize
            await pg.wait_for_timeout(1500)

            cntnt = await pg.content()
            soup = BeautifulSoup(cntnt, "html.parser")

            art = soup.find("article", class_="main-content")

            if art:
                # Wrap tab content with heading
                section = soup.new_tag("div", attrs={"class": "tab-section"})
                h1 = soup.new_tag("h1")
                h1.string = tab_title
                section.append(h1)
                section.append(art)

                all_content.append(str(section))
                print(f"   ✓ Extracted {len(str(art))} characters from: {tab_title}")
            else:
                print(f"   ⚠ No main content found for: {tab_title}")

        except Exception as e:
            # Log error but continue processing other tabs
            print(f"   ✗ Error crawling {tab_url}: {e}")
            continue

    await brwsr.close()

    combined = "\n\n".join(all_content)
    return combined


async def crawl_csv(df, base_dir, output_file="output_data.csv", detailed_log_path=None):
    """Takes CSV file in the format Heading, Subheading, Title, URL and processes each URL."""

    # Define a base directory within the user's space
    # base_dir = "../data/data_16_09_24/crawl/"

    # Create directories if they don't exist
    crawl_path = os.path.join(base_dir, "crawl")
    print(crawl_path)
    create_folder(crawl_path, is_full=True)
    create_folder(crawl_path, "html")
    create_folder(crawl_path, "pdf")
    create_folder(crawl_path, "others")

    output_data = []

    async def process_row(row):
        url = row["URL"]
        heading = row["Section"]
        sub_heading = row["Subsection"]
        title = row["Title"]
        filename = row["filename"]
        role = row["Role"]

        if "sharepoint.com" in url or url == "https://www.byupathway.edu/pathwayconnect-block-academic-calendar":
            return

        # Edit the title to become filename

        # Determine the filepaths
        html_filepath = os.path.join(crawl_path, "html", f"{filename}.html")
        pdf_filepath = os.path.join(crawl_path, "pdf", f"{filename}.pdf")

        # Skip fetching if the file already exists
        if os.path.exists(html_filepath) or os.path.exists(pdf_filepath):
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "stage": "crawl",
                "url": url,
                "status": "SKIPPED",
                "reason": "File already exists",
                "filepath": html_filepath if os.path.exists(html_filepath) else pdf_filepath,
            }
            if detailed_log_path:
                with open(detailed_log_path, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
            print(f"File already exists for {filename}. Skipping fetch.")
            return

        retry_attempts = 3

        print("Working on ", url)
        while retry_attempts > 0:
            try:
                time.sleep(3)
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # http errors
                content_type = response.headers.get("content-type", "")

                log_status = "SUCCESS"
                log_reason = f"Content Type: {content_type}"
                log_filepath = ""

                if any(domain in url for domain in ["faq.whatsapp"]):
                    content = await get_whatsapp_content(url)
                    filepath = html_filepath
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    content = content.encode("utf-8")
                    log_filepath = filepath
                elif any(
                    domain in url
                    for domain in [
                        "articulate.com",
                        "myinstitute.churchofjesuschrist.org",
                    ]
                ):
                    # raise HTTPError
                    response.status_code = 403

                    log_status = "HTTP_ERROR"
                    log_reason = "Access forbidden (403) - using Playwright fallback"
                    raise requests.exceptions.HTTPError(response)

                elif "text/html" in content_type:
                    content = response.text.encode("utf-8")
                    text_content = response.text
                    filepath = html_filepath
                    if "help.byupathway.edu" in url:
                        # from the content, get the information from the .wrapper-body
                        content = response.text
                        soup = BeautifulSoup(content, "html.parser")
                        content = soup.find("div", class_="wrapper-body").prettify()
                        text_content = content
                        content = content.encode("utf-8")
                    elif "student-services.catalog.prod.coursedog.com" in url:
                        # Student services tab handling
                        content = response.text
                        soup = BeautifulSoup(content, "html.parser")

                        # Check for tabs using ARIA role
                        tablist = soup.find("div", {"role": "tablist"})

                        if tablist:
                            print(f"   ⚡ Detected tabs on {url}, extracting all content...")

                            tab_links = tablist.find_all("a")

                            # Build list of tab URLs and titles
                            tab_info = [
                                {
                                    "title": link.text.strip(),
                                    "url": url + "#" + link.get("href").split("#")[1],
                                }
                                for link in tab_links
                                if "#" in link.get("href")
                            ]

                            if tab_info:
                                # Extract all tabs with Playwright
                                tab_content = await fetch_content_from_student_services(tab_info)

                                if tab_content:
                                    content = tab_content
                                    text_content = content
                                    log_status = "SUCCESS"
                                    log_reason = f"Extracted {len(tab_info)} tabs successfully"
                                else:
                                    # Fallback to main content
                                    print("   ⚠ Tab extraction failed, using main content")
                                    try:
                                        content = soup.find("article", class_="main-content").prettify()
                                        text_content = content
                                    except AttributeError:
                                        print("Error with ", url)
                                        log_status = "PARSE_ERROR"
                                        log_reason = "Error finding main content in HTML"
                                        content = response.text
                                        text_content = content
                            else:
                                # No valid tabs found, use main content
                                try:
                                    content = soup.find("article", class_="main-content").prettify()
                                    text_content = content
                                except AttributeError:
                                    print("Error with ", url)
                                    log_status = "PARSE_ERROR"
                                    log_reason = "Error finding main content in HTML"
                                    content = response.text
                                    text_content = content
                        else:
                            # No tabs, extract main content
                            try:
                                content = soup.find("article", class_="main-content").prettify()
                                text_content = content
                            except AttributeError:
                                print("Error with ", url)
                                log_status = "PARSE_ERROR"
                                log_reason = "Error finding main content in HTML"
                                content = response.text
                                text_content = content

                        content = content.encode("utf-8")
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(text_content)
                    log_filepath = filepath

                elif "application/pdf" in content_type:
                    content = response.content
                    filepath = pdf_filepath
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    log_filepath = filepath

                else:
                    # Handle other content types by saving with the correct extension
                    file_extension = content_type.split("/")[-1].split(";")[0]
                    filepath = os.path.join(crawl_path, "others", f"{filename}.{file_extension}")
                    content = response.content
                    with open(filepath, "wb") as f:
                        f.write(content)
                    log_filepath = filepath

                # Create content hash
                content_hash = generate_content_hash(content)

                # Append to the output list
                output_data.append([
                    heading,
                    sub_heading,
                    title,
                    url,
                    filepath,
                    content_type.split("/")[1].split(";")[0],
                    content_hash,
                    datetime.datetime.now().isoformat(),
                    role,
                ])

                log_entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "stage": "crawl",
                    "url": url,
                    "status": log_status,
                    "reason": log_reason,
                    "filepath": log_filepath,
                }
                if detailed_log_path:
                    with open(detailed_log_path, "a") as f:
                        f.write(json.dumps(log_entry) + "\n")

                break  # Exit retry loop after successful fetch

            except requests.exceptions.HTTPError as http_err:
                print(response.status_code)
                log_entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "stage": "crawl",
                    "url": url,
                    "status": "HTTP_ERROR",
                    "reason": f"HTTP Error {response.status_code}: {http_err}",
                    "filepath": None,
                }
                if response.status_code == 403:
                    print(f"Access forbidden for {url}: {http_err}. Using Playwright to fetch HTML.")
                    html_filepath = os.path.join(crawl_path, "html", f"{filename}.html")
                    await fetch_content_with_playwright(url, html_filepath)
                    output_data.append([
                        heading,
                        sub_heading,
                        title,
                        url,
                        html_filepath,
                        "text/html",
                        None,
                        datetime.datetime.now().isoformat(),
                        role,
                    ])

                    log_entry["status"] = "SUCCESS_WITH_PLAYWRIGHT_FALLBACK"
                    log_entry["reason"] = "Access forbidden (403), rescued with Playwright"
                    log_entry["filepath"] = html_filepath
                    if detailed_log_path:
                        with open(detailed_log_path, "a") as f:
                            f.write(json.dumps(log_entry) + "\n")

                    break  # Don't retry if it's a 403 error
                else:
                    print(f"HTTP error occurred for {url}: {http_err}")
                    retry_attempts -= 1
                    if retry_attempts > 0:
                        print("Retrying in 10 seconds...")
                        log_entry["reason"] += " Retrying..."
                        time.sleep(10)
                    else:
                        output_data.append([
                            heading,
                            sub_heading,
                            title,
                            url,
                            str(http_err),
                            str(response.status_code),
                            None,
                            datetime.datetime.now().isoformat(),
                            role,
                        ])

                        log_entry["status"] = "FAILED_HTTP_ERROR"
                        log_entry["reason"] = f"HTTP Error {response.status_code}: {http_err}. Max retries reached."
                        if detailed_log_path:
                            with open(detailed_log_path, "a") as f:
                                f.write(json.dumps(log_entry) + "\n")

            except requests.exceptions.RequestException as err:
                print(f"Error occurred for {url}: {err}")
                log_entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "stage": "crawl",
                    "url": url,
                    "status": "REQUEST_ERROR",
                    "reason": f"Request Exception: {err}",
                    "filepath": None,
                }
                retry_attempts -= 1
                if retry_attempts > 0:
                    print("Retrying in 10 seconds...")
                    log_entry["reason"] += " Retrying..."
                    time.sleep(10)
                else:
                    print(f"No content-type header found for {url}: {err}")
                    output_data.append([
                        heading,
                        sub_heading,
                        title,
                        url,
                        str(err),
                        "Error",
                        None,
                        datetime.datetime.now().isoformat(),
                        role,
                    ])

                    log_entry["status"] = "FAILED_REQUEST_ERROR"
                    log_entry["reason"] = f"Request Exception: {err}. Max retries reached."
                    if detailed_log_path:
                        with open(detailed_log_path, "a") as f:
                            f.write(json.dumps(log_entry) + "\n")

    # Process rows in batches of 10 to manage memory usage efficiently
    batch_size = 10
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i : i + batch_size]  # Get next batch of rows
        tasks = [process_row(row) for _, row in batch.iterrows()]  # Create tasks for batch
        await asyncio.gather(*tasks)  # Process batch before continuing

    # Create a DataFrame from the output data
    output_df = pd.DataFrame(
        output_data,
        columns=[
            "Heading",
            "Subheading",
            "Title",
            "URL",
            "Filepath",
            "Content Type",
            "Content Hash",
            "Last Update",
            "Role",
        ],
    )
    # Filtering rows where 'Content Hash' is None
    error_df = output_df[output_df["Content Hash"].isnull()]

    # Create error folder if it doesn't exist
    error_folder = os.path.join(base_dir, "error")
    os.makedirs(error_folder, exist_ok=True)

    # Save error file with new name in error folder
    error_csv_path = os.path.join(error_folder, "error.csv")
    with open(error_csv_path, "a") as f:
        f.write("Failed HTTP Errors\n")
    error_df.to_csv(error_csv_path, mode="a", index=False, header=True)

    out_path = os.path.join(base_dir, output_file)

    # Append to the existing CSV file or create a new one if it doesn't exist
    if os.path.exists(out_path):
        existing_df = pd.read_csv(out_path)
        combined_df = pd.concat([existing_df, output_df], ignore_index=True)

        # Delete the 'Last Update' column temporarily to remove duplicates
        combined_df_no_update = combined_df.drop(columns=["Last Update"])
        combined_df_no_update = combined_df_no_update.drop_duplicates()

        # Add the 'Last Update' column back
        combined_df = combined_df_no_update.join(combined_df["Last Update"])

        combined_df.to_csv(out_path, mode="w", index=False)
    else:
        output_df.to_csv(out_path, index=False)

    print(f"Processing completed. Output saved to {out_path}")
