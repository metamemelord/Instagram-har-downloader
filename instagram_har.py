#!/opt/anaconda3/bin/python
import re, requests, json, os, sys, random, string
from bs4 import BeautifulSoup

WEB_PROFILE_INFO_PAT='api/v1/users/web_profile_info'
GRAPHQL_QUERY_PAT = 'graphql/query'
INSTA_HOME = 'https://www.instagram.com/'
failed_videos = []

p = re.compile('[0-9]*_[0-9]*.*_[n|s]\.(webp|jpg|mp4)')


def get_data_from_html(req, filtered_response):
    soup = BeautifulSoup(req['response']['content']['text'], "html.parser")
    target_script = None
    for script in soup.find_all('script', src=None):
        if 'window._sharedData =' in script.string:
            target_script = script
            break
    if target_script is None:
        return
    k = target_script.string.replace('window._sharedData =', '')
    k = k[:-1]
    k = json.loads(k)
    homepage_entries = k['entry_data']['ProfilePage'][0]['graphql']['user']
    filtered_response.append(homepage_entries)


def get_random_string(size):
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(size))


def get_node_data(obj):
    return obj['node'] if 'node' in obj else None


def download_media(obj, base_path):
    url = ''
    typ = '.jpg'
    if obj['__typename'] == 'GraphImage':
        if 'display_resources' in obj:
            url = obj['display_resources'][-1]['src']
        else:
            url = obj['display_url']
    else:
        if 'video_url' in obj:
            url = obj['video_url']
        else:
            failed_videos.append(obj['shortcode'])
            return
        typ = '.mp4'
    url = url.replace('\u0026', '&')
    filename = get_random_string(40) + typ
    found = p.search(url)
    if found:
        filename = found.group(0)
    filepath = os.path.join(base_path, filename)
    if len(filename) < 6:
        print(obj, "\n\n", url, "\n\n")
    if not os.path.exists(filepath):
        httpresp = requests.get(url)
        out_file = open(filepath, "wb")
        out_file.write(httpresp.content)
        out_file.close()
        print("Saved", filename)
    else:
        print("Already exists", filename)

def create_dirs_and_get_output_path(username):
    downloads_dir = os.path.join(os.getcwd(), 'Downloads')
    create_dir_if_does_not_exist(downloads_dir, True)

    output_dir = os.path.join(downloads_dir, username)
    create_dir_if_does_not_exist(output_dir, True)

    return output_dir

def create_dir_if_does_not_exist(path, log=False):
    if not os.path.isdir(path):
        os.mkdir(path)
        if log:
            print('Created directory:', path)
    else:
        if log:
            print('Directory exists:', path)

input_file = open(os.path.abspath(sys.argv[1]))
file_content = input_file.read()
input_file.close()

username = re.search('\(@[^ ]*\)', file_content).group(0)[2:-1]
print("Username:", username)

output_dir = create_dirs_and_get_output_path(username)

print("Output dir:", output_dir)

# Load the json content of HAR file
request_items = json.loads(file_content)['log']['entries']

# content-type header
html_header = {"name": "content-type", "value": "text/html; charset=utf-8"}
# Filter all the calls that were made to the graphql API
filtered_response = []
for req in request_items:
    if req['request']['method'] == 'OPTIONS':
        continue
    if INSTA_HOME + username in req['request']['url'] and str(
            html_header) in str(req['response']['headers']).lower(): # This doesn't work anymore!
        get_data_from_html(req, filtered_response)
    elif GRAPHQL_QUERY_PAT in req['request']['url'] or WEB_PROFILE_INFO_PAT in req['request']['url']:
        filtered_response.append(
            json.loads(req['response']['content']['text'])['data']['user'])
        

# Filter only timeline posts
timeline_posts = []
for post in filtered_response:
    if 'edge_owner_to_timeline_media' in post:
        timeline_posts.extend(
            map(get_node_data, post['edge_owner_to_timeline_media']['edges']))
    # elif 'edge_web_feed_timeline' in post:
    #     timeline_posts.extend(
    #         map(get_node_data, post['edge_web_feed_timeline']['edges']))

print("Total posts found:", len(timeline_posts))

raw_posts_data_file = open(os.path.join(output_dir, "posts_raw.json"), "w")
raw_posts_data_file.write(json.dumps(timeline_posts))
raw_posts_data_file.close()

for post in timeline_posts:
    if post['__typename'] == 'GraphSidecar':
        sidecar_id = post["id"]
        output_dir_sidecar = os.path.join(output_dir, sidecar_id)
        create_dir_if_does_not_exist(output_dir_sidecar)
        for sidecar_item in post["edge_sidecar_to_children"]["edges"]:
            download_media(sidecar_item['node'], output_dir_sidecar)
    else:
        download_media(post, output_dir)

if failed_videos:
    failed_videos_log = os.path.join(output_dir, "failed.log")
    print("There are some failed videos, please download them manually.\n%s" %
          failed_videos_log)
    with open(failed_videos_log, "w") as f:
        for failed in failed_videos:
            f.write(INSTA_HOME + '/p/' + failed + '\n')
