import pandas as pd
import re
import requests
from bs4 import BeautifulSoup

# Read URLs from Excel file
df = pd.read_excel("urls.xlsx")

# Set of keywords to look for in URLs
keywords = {"contact", "about us", "impressum", "kontakt", "ueber uns"}

# Set of URLs that have been scraped
scraped_urls = set()

# Set of emails extracted
emails = set()

# Iterate over URLs
for index, row in df.iterrows():
    url = row['URL']
    if pd.isna(url):  # Check for NaN values
        continue
    print(url)
    scraped_urls.add(url)
    # Send GET request to URL
    response = requests.get(url)

    # Check if request was successful
    if response.status_code != 200:
        continue

    # Extract emails from response text
    new_emails = set(re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", response.text, re.I))
    new_emails = [email for email in emails if not (email.endswith('.png') or email.endswith('.jpg'))]
    print(new_emails)
    emails.update(new_emails)
    print(emails)
    # Parse HTML of response
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all anchor tags in HTML
    links = soup.find_all('a', href=True)

    # Iterate over links
    for link in links:
        weblink = link.get('href')
        
        if any(keyword in weblink for keyword in keywords):
            if weblink not in scraped_urls:
                scraped_urls.add(weblink)
                new_df = pd.DataFrame({'URL': [weblink]})
                df = pd.concat([df, new_df], ignore_index=True)
                print(weblink)
print("Emails to xcele" % emails)
# Add column to dataframe to store extracted emails
df['Emails'] = emails
#
## Write dataframe to Excel file
df.to_excel("urls.xlsx", index=False)
#