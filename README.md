# web-scraping-zillow

scraping data from “Zillow”, www.zillow.com, a US real-estate marketplace, similar to Israel’s Yad2.
The client wants a full crawl of Zillow, for specific cities. For simplification, we focus on apartments only with the following criteria:
●	in the zip code 61761 in the state “Michigan”, USA
●	only single-family homes (houses)
●	 with a monthly rental price of between 1000-2000$.

this project uses python to scrape all apartments that fit the criteria above from the zillow website, using Nimble WEB API to navigate to the web pages and parse them in python using the beautiful soup library, so that we end up with a CSV file with all data fields the client is interested in.

Important: it is essential for the client that all houses that fit the criteria will be in the data. So the scraping should be exhaustive.
