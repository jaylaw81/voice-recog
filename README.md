# Voice API Search

A very small voice activated web search tool.

Utilizing the [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) and `python` this small
little app will parse a sitemap.xml file and based on a configuration file allow a user to interact
with the browser via voice to search a site and return "somewhat" acurate results.

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

To configure your scraper, create a `./config.json`

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

## Caching

The Javascript will cache the API data for 1hr (3600000ms) in `localStorage`.

After cache timeout occurs, refreshing the JS page will invalidate the `localStorage` cache and call the API to retrieve new data and re-cache to `localStorage`
