# Instagram-har-downloader
Download Instagram data of a profile from har dump

_**DISCLAIMER:** THIS SCRIPT USES WEB SCRAPING. COMMERCIAL USE OF THIS SCRIPT IS STRICTLY PROHIBITED AND IS ILLEGAL. PLEASE FEEL FREE TO USE IT FOR LEARNING!_

## Install dependencies
`pip install -r requirements.txt`

## Get HAR file
- Open user profile in Firefox - [example](https://www.instagram.com/whentestingmetquality/).
- Open developer tools and network tab.
- Disable cache and reload page.
- Scroll down till all posts are downloaded.
- Click the gear icon on top left in dev tools and click "Save All As HAR".

## Usage
Extract the har dump using steps from above section, then run:<br/>
`python instagram_har.py <input.har>`
<br/>
<br/>
**Tested on Firefox v76.0.1 and v89.0.2**
