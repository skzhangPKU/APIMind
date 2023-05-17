import re
import sys
import urllib.request
import os
from bs4 import BeautifulSoup


class PlayStore():
	def __init__(self, package_name):
		self._cover_image = None
		self._description = None
		self._screenshots = None
		try:
			if (self._validate_play_store_package_name(package_name)):
				self.__package_name = package_name
				print("Initialised play store object with package name: %s" %package_name)
			else:
				print("Invalid package name: %s" %package_name)
				sys.exit(1)
		except Exception as e:
			print(e)
			sys.exit(1)

	def _validate_play_store_package_name(self, p):
		regex =  "([a-zA-Z_]{1}[a-zA-Z0-9_]*(\.[a-zA-Z_]{1}[a-zA-Z0-9_]*)*)$"
		return re.match(regex, p)

	def _generate_play_store_url(self):
		return ("https://app.mi.com/details?id=" + str(self.__package_name) + "&ref=search")

	def _fetch_url_content(self):
		url = self._generate_play_store_url()
		l = urllib.request.urlopen(url)
		if l.getcode() == 200:
			print("Fetched play store link successfully! (%s)" %url)
			return l.read()
		else:
			print("Error in fetching url! (%s)" %url)
			sys.exit(1)

	def _generate_soup(self):
		try:
			content = self._fetch_url_content()
			soup = BeautifulSoup(content, "html.parser")
		except Exception as e:
			print(e)
			sys.exit(1)
		else:
			return soup

	def _parse_soup(self, write_to_disk):
		soup = self._generate_soup()
		description = self._fetch_description(soup)
		title = self._fetch_title(soup)
		category = self._fetch_category(soup)
		year = self._fetch_year(soup)
		requirement = self._fetch_requirement(soup)
		self._description = description
		self._title = title
		self._category = category
		self._year = year
		self._requirement = requirement
		if write_to_disk:
			self._setup_folder()
			self._save_description()

	def _fetch_cover_image(self, soup):
		cover_container = soup.find_all('div', {"class": "cover-container"})
		for c in cover_container:
			cover_image = c.find_all('img', {"class": "cover-image"})			
		if len(cover_image)>0:
			return "https:" + cover_image[0]["src"]
		else:
			print("Cover Image not found!")
			return None

	def _fetch_description(self, soup):
		description_container = soup.find_all('div', {"class": "bARER", "data-g-id": "description"})
		if len(description_container)>0:
			return (description_container[0].text)
		else:
			print("Description not found!")
			return None

	def _fetch_description_xiaomi(self, soup):
		description_container = soup.find_all('div', {"class": "app-text"})
		if len(description_container)>0:
			return (description_container[0].text)
		else:
			print("Description not found!")
			return None
			
	def _fetch_title(self, soup):
		title_container = soup.find_all("div", {"class": "id-app-title"})
		if len(title_container)>0:
			return (title_container[0].text)
		else:
			print("Title not found!")
			return None
			
	def _fetch_category(self, soup):
		category_container = soup.find_all("span", {"itemprop": "genre"})
		if len(category_container)>0:
			return (category_container[0].text)
		else:
			print("category not found!")
			return None
			
	def _fetch_year(self, soup):
		year_container = soup.find_all("div", {"itemprop": "datePublished"})
		if len(year_container)>0:
			return (year_container[0].text[-4:])
		else:
			print("category not found!")
			return None	
	
	def _fetch_requirement(self, soup):
		requirement_container = soup.find_all("div", {"itemprop": "operatingSystems"})
		if len(requirement_container)>0:
			return (requirement_container[0].text)
		else:
			print("category not found!")
			return None
		
	def _fetch_screenshots(self, soup):
		img_containers = soup.find_all("img", {"class": "full-screenshot"})
		screenshots = []
		for i in img_containers:
			url = i.get("src", None)
			if url: url = "https:" + url; screenshots.append(url)							
		return screenshots

	def _setup_folder(self):
		if not os.path.exists(self.__package_name):
			os.makedirs(self.__package_name)
		else:
			for root, dirs, files in os.walk(self.__package_name, topdown=False):
			    for name in files:
			        os.remove(os.path.join(root, name))
			    for name in dirs:
			        os.rmdir(os.path.join(root, name))
			

	def _download_and_save(self, url, fname):
		urllib.urlretrieve(url, self.__package_name+"/"+fname+".png")

	def _save_cover_image(self):
		self._download_and_save(self._cover_image, "cover_image")

	def _save_screenshots(self):
		i = 0
		for s in self._screenshots:			
			self._download_and_save(s, "s"+str(i))
			i += 1

	def _save_description(self):
		f = open(self.__package_name+"/"+"desc", 'wb')
		f.write(self._description.encode("utf8"))
		f.close()

		