#!/usr/bin/env python
# coding: utf-8

# In[186]:


import requests
import pandas as pd
import selenium.common.exceptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.keys import Keys
import datetime as dt
import time
# from fake_useragent import UserAgent
import random

#User agent list
ua_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/E7FBAF",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36 Keeper/1616028983",
]

# Settings
options = webdriver.FirefoxOptions()
options.headless = True
# ua = UserAgent()
# userAgent = ua.random
options.add_argument(f"user-agent={ua_list[random.randint(0, 6)]}")
options.add_argument("--width=1920")
options.add_argument("--height=1080")
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
start_url = "https://coolparcel.com/shipping/international/shipping-calculator"
wait = WebDriverWait(driver, 1)
time1 = dt.datetime.now()
current_time = time1.strftime("%Y-%m-%dT%H_%M_%S")


# In[187]:

def random_sleep():
    """
    Random sleep function to avoid being blocked by coolparcel
    :return:
    """
    # Make random sleep timer with floats
    sleep_time = random.uniform(1.2, 2.5)
    time.sleep(sleep_time)


def element_by_id(id1:str):
    element = driver.find_element(by=By.ID, value=id1)
    return element


# In[188]:


def element_by_selector(selector:str):
    element = driver.find_element(by= By.CSS_SELECTOR, value=selector)
    return element


# In[189]:


def country_info_input(country:str, postalcode:str, from1 = False):
    # Setup input field variables
    country_input = element_by_id("package-input-origin") if from1 else element_by_id("package-input-destination")
    postal_input = element_by_id("package-origin_postcode") if from1 else element_by_id("package-delivery_postcode")

    # Write country
    random_sleep()
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(country_input)).click()
    # country_input.click()
    random_sleep()
    country_input.send_keys(Keys.BACKSPACE)
    random_sleep()
    country_input.send_keys(country)
    random_sleep()

    # Write postalcode
    postal_input.click()
    random_sleep()
    for _ in range(2):
        postal_input.send_keys(Keys.ARROW_RIGHT)
        time.sleep(0.5)
    for _ in range(7):
        postal_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)
    postal_input.send_keys(postalcode)


# In[190]:


def setup_search(countries:list, postalcodes:list, from1:list, package_specs:dict):
    """
    :param countries: List of origin and destination countries
    :param postalcodes: List of postalcodes from origin and destination
    :param from1: List that specifies if first or second country is origin
    :param package_specs: Example input {"weight":"20", "length":"20", "width":"30", "height":"5"} -- Weight in lb(pounds), length measurements in In(inches)
    :return
    """
    # Loop through and setup countries input fields
    for index, country in enumerate(countries):
        country_info_input(country, postalcodes[index], from1[index])
        time.sleep(1)

    # Setup measurement variables
    weight = element_by_selector("#clone-package-container > div > div > div:nth-child(1) > div > div.form-group.col-6.col-lg-6 > div > input")
    length = element_by_selector("#clone-package-container > div > div > div:nth-child(2) > div > div:nth-child(1) > div > input")
    width = element_by_selector("#clone-package-container > div > div > div:nth-child(2) > div > div:nth-child(2) > div > input")
    height = element_by_selector("#clone-package-container > div > div > div:nth-child(2) > div > div:nth-child(3) > div > input")

    # Open custom measurements
    size_button = element_by_id("package-custom-size")
    # driver.execute_script("arguments[0].scrollIntoView();", size_button)
    time.sleep(1)
    size_button.click()
    time.sleep(1)

    # Setup measurements input fields
    weight.send_keys(package_specs["weight"])
    time.sleep(1)
    length.send_keys(package_specs["length"])
    time.sleep(1)
    width.send_keys(package_specs["width"])
    time.sleep(1)
    height.send_keys(package_specs["height"])
    time.sleep(1)

    # Click search
    find_price = element_by_selector("#package > form > div.details-packages > div.find-price > button")
    find_price.click()


# In[191]:


def scrape_data():
    info_container = driver.find_elements(by=By.CLASS_NAME, value="result-container")
    result = [x.text for x in info_container]
    return result


# In[192]:


def jsonfy_data(data, from1, to1):  # Going through data taking some info --> turning into dataframe --> lastly to record json for mongodb
    all_data = []
    for shipment in data:
        temp_data = shipment.split("\n")
        temp_dict = {"time":current_time, "from":from1, "to":to1}
        for index, line in enumerate(temp_data):
            if " → " in line:
                temp_dict["delivery_method"] = line
            elif index == 1:
                temp_dict["company"] = line
            elif "$" in line:
                temp_dict["cost"] = line
        all_data.append(temp_dict)

    df = pd.DataFrame(all_data)
    return df


# In[193]:


def push_to_mongodb(data):  # TODO mongodb write
    pass


# In[194]:


def check_init_input(from1, to1, package_measures):
    """
    :param from1: Origin country
    :param to1: Destination country
    :param package_measures: Package measurements
    :return:
    """
    country_list = []
    us_states_list = []
    with open("Data_ETL/Webscrapers/resources/countries_list.txt") as r, open("Data_ETL/Webscrapers/resources//us_states.txt") as r2:
        for country in r.readlines():
            country_list.append(country[:-1])

        for state in r2.readlines():
            us_states_list.append(state[:-1])

    # print(us_states_list)
    # Checking if countries exists
    if (from1.capitalize() in country_list and to1.capitalize() in country_list) or (from1 in us_states_list and to1 in us_states_list):
        # Checking that package_measures have all the info
        measurements = ["weight", "length", "width", "height"]
        for measurement in measurements:
            if measurement in package_measures.keys():
                pass
            else:
                print("Measurements wrong")
                return False

        for k, v in package_measures.items():
            try:
                float(v)
            except ValueError as e:
                print(e)
                print("Given item measurement format is wrong")

        return True
    else:
        return False


# In[195]:


def get_zipcode(country):
    # get zipcode for country or us state

    # if Finland
    if country.lower() == "finland":
        return "00100"
    else:
        pass
        # print("Not Finland")

    # if US state
    df = pd.read_json("Data_ETL/Webscrapers/resources/uszips.json")
    test_df = df[df["state_name"] == country]
    if str(test_df.shape) == "(0, 18)":
        pass
        # print("Not US state")
    else:
        zip_code = df[df["state_name"] == country]["zip"].iloc[3]
        if len(str(zip_code)) == 3:
            return "00" + str(zip_code)
        elif len(str(zip_code)) == 4:
            return "0" + str(zip_code)
        elif len(str(zip_code)) == 5:
            return str(zip_code)

    # if Other country
    """client = pymongo.MongoClient()
    db = client["Shipments"]
    col = db["addresses"]
    data = col.find_one({})
    df2 = pd.DataFrame(data["data"])"""
    df2 = pd.read_json("Data_ETL/Webscrapers/resources/other_countries_zipcodes.json")
    result_df = df2[df2["country"] == country]
    if str(result_df.shape) == "(0, 2)":
        print("Not other country")
    else:
        return str(result_df.iloc[0, 1])

    return False


# In[196]:


def main(from1, to1, package_measures, from_zipcode, to_zipcode):
    """
    :param from1: Origin country
    :param to1: Destination country
    :param package_measures: Package measurements
    :param from_zipcode: Origin zipcode
    :param to_zipcode: Destination zipcode
    :return:
    """
    time.sleep(1)
    driver.get(start_url)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(driver.find_element(By.ID, "package-input-origin")))
    if from_zipcode is None:
        from_zipcode = get_zipcode(from1)
    if to_zipcode is None:
        to_zipcode = get_zipcode(to1)
    if from_zipcode is False or to_zipcode is False:
        return False
    setup_search([from1, to1], [from_zipcode, to_zipcode], [True, False], package_measures)
    WebDriverWait(driver, 60).until(method=EC.visibility_of_element_located((By.CLASS_NAME, "result")))
    raw_data = scrape_data()
    df = jsonfy_data(raw_data, from1, to1)
    push_to_mongodb(df)
    # driver.quit()
    return df


# In[197]:
def stop_driver():
    driver.quit()


def init(from1: str, to1: str, package_measures: dict,from_zipcode: str=None, to_zipcode: str=None):
    """
    :param to_zipcode: Optional
    :param from_zipcode: Optional
    :param from1: str Have to be capitalized and written correctly (country/state)
    :param to1: str Have to be capitalized and written correctly (country/state)
    :param package_measures: Example input {"weight":"20", "length":"20", "width":"30", "height":"5"} -- Weight in lb(pounds), length measurements in In(inches)
    :return:
    """
    check_init_input(from1, to1, package_measures)
    data = main(from1, to1, package_measures, from_zipcode, to_zipcode)
    if data is False:
        print("Country or state is not in database or is invalid")
    return data.to_dict(orient="records")
"""    try:
        check_init_input(from1, to1, package_measures)
        data = main(from1, to1, package_measures)
        return data
    except:
        print("Unexpected error")"""


# In[198]:


# info = init("Belgium", "Texas", {"weight":"20", "length":"20", "width":"30", "height":"5"}, "2440", "75226")
# print(info)


# In[198]:




