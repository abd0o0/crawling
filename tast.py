import re
import requests
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlsplit
import pandas as pd
from tld import get_fld
import logging
import os
import time
from selenium import webdriver


keywords = {"contact", "about us", "impressum", "kontakt", "ueber uns"}

def extract_emails(url):
    depth = 0
    url = url.replace("http://", "")
    unscraped_url = [url]
    scraped_url = set()    
    list_emails = set()
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0'
    }
    email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    link_pattern = re.compile(r'\d+\.\d+\.html')
    while len(unscraped_url):
        url = unscraped_url.pop()
        scraped_url.add(url)

        parts = urlsplit(url)  
        base_url = "{0.scheme}://{0.netloc}".format(parts)

        if '/' in parts.path:
            part = url.rfind("/")
            path = url[0:part + 1]
        else:
            path = url

        print("Searching for Emails in  %s" % url)  

        try:
            response = requests.get(url, headers=headers)
        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL):
            
            logging.error("Error accessing url: " + url)
            print(f"{url} is accessible")
            continue
        
        
        if response.status_code != 200:

            logging.warning("HTTP status code is not 200 for url: " + url)
            print(f"{url} is not accessible")
            continue
        time.sleep(2)

        new_emails = set(re.findall(email_regex, response.text))
        new_emails = [email for email in new_emails if email.endswith('.com') or email.endswith('.net') or email.endswith('.de')]
        if new_emails:
            list_emails.update(new_emails)
            if len(list_emails) > 0:
                return list_emails

        if (depth > 8):
            return list_emails
        depth +=1
        soup = BeautifulSoup(response.text, 'html.parser')

        
        #if not links:
        #    driver = webdriver.Chrome()
        #    driver.get(url)
        #    soup = BeautifulSoup(driver.page_source, 'html.parser')
        #    driver.quit()
        email_spans = soup.find_all('span')
        for span in email_spans:
            email = re.findall(email_regex, span.text)
            if email:
                new_emails.append(email[0])
        list_emails.update(new_emails)
        if len(list_emails) > 0:
            return list_emails
        if (depth > 8):
            return list_emails
        depth +=1
        links = soup.find_all('a' , href=True)


        for link in links:

            weblink = link.get("href")
            link_text = link.text.lower()
            if weblink is None:
                continue

            if weblink.startswith('mailto:'):
                email = weblink.replace('mailto:','')
                email = email.replace('(at)','@')
                new_emails.append(email)
                continue


            if weblink.startswith('/'):
                weblink = base_url + weblink
            elif not weblink.startswith('https'):
                weblink = path + weblink
                
            match = re.search(link_pattern,weblink)
            if match:
                email = match.group().replace('.html','')
                email = email.replace('.','@')
                new_emails.append(email)
                continue


            if base_url in weblink:
                if ("about" in link_text) or ("about" in weblink):
                    logging.info(f"{weblink} contains the keyword 'about'")
                    print(f"linktext",weblink)
                if any(keyword in weblink.lower() for keyword in keywords):
                    if not weblink in unscraped_url and not weblink in scraped_url:
                        unscraped_url.append(weblink)
            list_emails.update(new_emails)


def save_emails(emails, filename):
    
    if os.path.isfile(filename):
        existing_emails = pd.read_csv(filename)
    else:
        existing_emails = pd.DataFrame(columns=["List of Emails"])


    
    df = pd.concat([existing_emails, pd.DataFrame(emails, columns=["List of Emails"])], ignore_index=True)
    
    df.drop_duplicates(subset ="List of Emails", keep = False, inplace = True) 
    
    df.to_csv(filename, index=False)

    
def main():
    
    logging.basicConfig(filename='scraping.log', level=logging.INFO)
    df = pd.read_excel("urls.xlsx")
    for index, row in df.iterrows() :
        if pd.notnull(row['URL']):
            url = row['URL']
            if "https://" not in url:
                url = "https://"+ url
            emails = extract_emails(url)
            for i, email in enumerate(emails):
                df.at[index, f'Email_{i+1}'] = email
    df.to_excel("urls.xlsx", index=False)

if __name__ == "__main__":
    main()

