#################################
##### Name:      Moeki Kurita
##### Uniqname:  mkurita
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets  # file that contains your API key

# Cache required info for each URL --------------------------------------------
CACHE_FILENAME = "cache.json"

# Load API key ----------------------------------------------------------------
API_KEY = secrets.API_KEY


# Original helper functions ---------------------------------------------------
def get_soup(url: str):
    """Execute BeautifulSoup requet

    Parameters
    ----------
    url : str
        url to be parsed

    Returns
    -------
    bs4 object
    """
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')


def open_cache(filename: str):
    ''' Opens the cache file if it exists and loads the JSON
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    filename: str
        filename for the cache

    Returns
    -------
    dict
        The opened cache
    '''
    try:
        with open(filename, 'r') as fobj:
            cache_dict = json.load(fobj)
    except FileNotFoundError:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict: dict, filename: str):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    filename: str
        filename for the cache

    Returns
    -------
    None
    '''
    with open(filename, 'w') as fobj:
        json.dump(cache_dict, fobj, indent=4)


def print_places(place_dict: dict):
    """Print places included in the given dictionary
       (e.g. - Name (Category): Address, City)

    Parameters
    ----------
    place_dict : dict
        dictionary of neaby places created by get_nearby_places()
    """
    for place in place_dict["searchResults"]:
        temp_dict = {
            "name": place["name"],
            "category": place["fields"]["group_sic_code_name"],
            "address": place["fields"]["address"],
            "city": place["fields"]["city"]
        }
        # check and overwrite empty attributes
        for k, v in temp_dict.items():
            if v == "":
                temp_dict[k] = f"No {k}"
        print(
            f"- {temp_dict['name']} ({temp_dict['category']}):",
            f"{temp_dict['address']}, {temp_dict['city']}"
        )


# Existing class/func ---------------------------------------------------------
class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        """Initialize NationalSite instance

        Parameters
        ----------
        category : str
            cateogry of the site
        name : str
            name of the site
        address : str
            address of the site
        zipcode : str
            zipcode of the site
        phone : str
            phone number of the site
        """
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        """Print summarized info of the site as a string

        Returns
        -------
        str
            summarized info of the site
        """
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    state_dict = {}
    baseurl = "https://www.nps.gov"
    index_path = "/index.htm"
    cache_dict = open_cache(CACHE_FILENAME)
    if baseurl + index_path in cache_dict.keys():
        # print("Using cache")
        state_dict = cache_dict[baseurl + index_path]
    else:
        # print("Fetching")
        soup = get_soup(url=baseurl + index_path)
        state_list = soup.find("ul",
                               class_="dropdown-menu SearchBar-keywordSearch")
        state_list = state_list.find_all("a")
        for state in state_list:
            state_path = state["href"]
            state_dict[state.text.lower()] = baseurl + state_path
        cache_dict[baseurl + index_path] = state_dict
        save_cache(cache_dict=cache_dict, filename=CACHE_FILENAME)
    return state_dict


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    cache_dict = open_cache(CACHE_FILENAME)
    if site_url in cache_dict.keys():
        print("Using cache")
        site = NationalSite(category=cache_dict[site_url]["category"],
                            name=cache_dict[site_url]["name"],
                            address=cache_dict[site_url]["address"],
                            zipcode=cache_dict[site_url]["zipcode"],
                            phone=cache_dict[site_url]["phone"])
    else:
        print("Fetching")
        soup = get_soup(url=site_url)
        # search header area
        headers = soup.find("div", "Hero-titleContainer")
        # collect attributes
        name = headers.find("a", class_="Hero-title")
        try:
            name = name.text.strip()
        except AttributeError:
            name = "No name"
        category = headers.find("span", class_="Hero-designation")
        try:
            category = category.text.strip()
        except AttributeError:
            category = "No category"
        # search footer area
        footers = soup.find("div", class_="ParkFooter-contact")
        # collect attributes
        local = footers.find("span", itemprop="addressLocality")
        region = footers.find("span", itemprop="addressRegion")
        try:
            address = f"{local.text.strip()}, {region.text.strip()}"
        except AttributeError:
            address = "No address"
        zipcode = footers.find("span", itemprop="postalCode")
        try:
            zipcode = zipcode.text.strip()
        except AttributeError:
            zipcode = "No zipcode"
        phone = footers.find("span", itemprop="telephone")
        try:
            phone = phone.text.strip()
        except AttributeError:
            phone = "No phone"
        # create instance
        site = NationalSite(category=category,
                            name=name,
                            address=address,
                            zipcode=zipcode,
                            phone=phone)
        # update cache
        cache_dict[site_url] = {"category": category,
                                "name": name,
                                "address": address,
                                "zipcode": zipcode,
                                "phone": phone}
        save_cache(cache_dict=cache_dict, filename=CACHE_FILENAME)
    return site


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    cache_dict = open_cache(CACHE_FILENAME)
    if state_url in cache_dict.keys():
        print("Using cache")
        site_urls = cache_dict[state_url]
    else:
        print("Fetching")
        # get list of headings of each site
        soup = get_soup(state_url)
        site_h3_list = soup.find("ul", id="list_parks").find_all("h3")
        # to concatenate URL
        baseurl = "https://www.nps.gov"
        index_path = "index.htm"
        # create list of URLs
        site_urls = []
        for site in site_h3_list:
            site_path = site.find("a")["href"]
            site_url = baseurl + site_path + index_path
            site_urls.append(site_url)
        # update cache
        cache_dict[state_url] = site_urls
        save_cache(cache_dict=cache_dict, filename=CACHE_FILENAME)
    # create NationalSite objects for each URL
    sites = []
    for url in site_urls:
        site = get_site_instance(url)
        sites.append(site)
    return sites


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    cache_dict = open_cache(CACHE_FILENAME)
    zipcode = site_object.zipcode
    if zipcode in cache_dict.keys():
        print("Using cache")
        place_dict = cache_dict[zipcode]
    else:
        print("Fetching")
        baseurl = "http://www.mapquestapi.com/search/v2/radius"
        params = {
            "key": API_KEY,
            "origin": zipcode,
            "radius": "10",
            "maxMatches": "10",
            "ambiguities": "ignore",
            "outFormat": "json"
        }
        response = requests.get(url=baseurl, params=params)
        place_dict = response.json()
        cache_dict[zipcode] = place_dict
        save_cache(cache_dict=cache_dict, filename=CACHE_FILENAME)
    return place_dict


if __name__ == "__main__":
    prompt = "Enter a state name (e.g. Michigan, michigan), or 'exit': "
    prompt2 = "Choose the number for detail search or 'exit' or 'back': "
    state_dict = build_state_url_dict()
    while True:
        state = input(prompt).lower()
        # check exit
        if state == "exit":
            break
        try:
            sites = get_sites_for_state(state_dict[state])
            # pretty print
            header = f"List of national sites in {state.title()}"
            print("-" * len(header), header, "-" * len(header), sep='\n')
            counter = 1
            for site in sites:
                print(f"[{counter}] {site.info()}")
                counter += 1
            # display nearby places
            while True:
                detail = input(prompt2)
                # check exit
                if detail == "exit" or detail == "back":
                    break
                # check invalid input (out of range)
                elif int(detail) > counter - 1 or int(detail) < 1:
                    print("[Error] Invalid input.")
                    continue
                # check if the selected site has zipcode
                elif sites[int(detail) - 1].zipcode == "No zipcode":
                    print("[Error] This site does not have location info")
                    continue
                # pretty-print nearby places
                else:
                    place_dict = get_nearby_places(sites[int(detail) - 1])
                    header = f"Places near {sites[int(detail)-1].name.title()}"
                    print("-" * len(header),
                          header,
                          "-" * len(header),
                          sep='\n')
                    print_places(place_dict)
                    continue
            # check exit
            if detail == "exit":
                break
        # if invalid state name is given
        except KeyError:
            print("Enter proper state name.")
            continue
