# Voice API Search

# Run small App

I use `serve` to run a quick local instance.

https://www.npmjs.com/package/serve

1. Run `serve` in directory
2. App will run at something like http://localhost:3000 or whatever open port there is.

## Run Scraper

1. Install python dependencies `pip install`
2. Run `python3 scrape.py`
3. API will run at http://127.0.0.1:5000/api/faqs

## Configuration

To configure your scraper, edit the config.json

`sitemap`
contains the path to your sitemap.xml file

`faq_url_pattern`
regex of paths to follow within your sitemap.xml

`scrape_patterns`

array of elements

`selector`
Parent selector of the containing elements

`question`
The question element that may be used in Search

`answer`
The response element to return in the Search

```
{
  "sitemap": "http://localhost:3000/sitemap.xml",
  "faq_url_pattern": "(army-life|basic-training|how-to|requirements|basic-training|benefits|find-your-path|specialty-careers|job-training)",
  "scrape_patterns": [
    {
      "selector": "details[data-component=\"accordion\"]",
      "question": ".accordion__subheading h3",
      "answer": ".accordion__body p"
    },
    {
      "selector": ".exposedgridcard",
      "question": "h3.card-content__heading",
      "answer": ".rte p"
    }
  ]
}
```
