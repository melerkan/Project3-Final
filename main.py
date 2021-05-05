import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import threading
import time

# ParseHub keys & tokens for API
API_KEY = "tL73GLCnox8H"
PROJECT_TOKEN = "taSKg8GBK8K-"
RUN_TOKEN = "tTUeowrx2GMq"

# Class to get various pieces of data
class Data:
	def __init__(self, api_key, project_token):
		self.api_key = api_key
		self.project_token = project_token
		self.params = {
		"api_key": self.api_key
		}
		self.data = self.get_data()

	def get_data(self):
		# Requests data from ParseHub servers & assigns data to variable data
		response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data', params=self.params)
		data = json.loads(response.text)
		return data

	# Gets total cases worldwide
	def get_total_cases(self):
		data = self.data['total']

		for info in data:
			if info['name'] == "Coronavirus Cases:":
				return info['value']

	# Gets total deaths worldwide
	def get_total_deaths(self):
		data = self.data['total']

		for info in data:
			if info['name'] == "Deaths:":
				return info['value']

		return "0"

	# Gets total recovered worldwide
	def get_recovered(self):
		data = self.data['total']

		for info in data:
			if info['name'] == "Recovered:":
				return info['value']

		return "0"

	# Gets all country data
	def get_country_data(self, country):
		data = self.data["country"]

		for info in data:
			if info['name'].lower() == country.lower():
				return info

		return "0"

	# Gets list of all countries
	def get_country_list(self):
		countries = []
		for country in self.data['country']:
			countries.append(country['name'].lower())

		return countries

	# Updates data to current numbers
	def update_data(self):
		response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params)

		def poll():
			time.sleep(0.1)
			old_data = self.data
			while True:
				new_data = self.get_data()
				if new_data != old_data:
					self.data = new_data
					print("Data updated.")
					break
				time.sleep(5)

		td = threading.Thread(target=poll)
		td.start()

# Sets up text to speech
def speak(text):
	engine = pyttsx3.init()
	engine.say(text)
	engine.runAndWait()

# Gets audio from microphone, assigns speech to text as string to variable 'said'
def get_audio():
	r = sr.Recognizer()
	with sr.Microphone() as source:
		audio = r.listen(source)
		said = ""

		try:
			said = r.recognize_google(audio)
		except Exception as e:
			print("Exception: Could not understand you", str(e))

	return said.lower()

def main():
	print("Welcome to the COVID-19 Voice Assistant!\n")
	print("Statistics you can ask about (use your microphone):\n")
	print("- Total cases\n- Total deaths\n- Total recovered\n- Country specific stats\n- COVID-19 Tests by Country\n- Country populations")
	data = Data(API_KEY, PROJECT_TOKEN)

	# Stops accepting audio with this word
	quit = "stop"

	country_list = data.get_country_list()

	# Speech patterns
	total_patterns = {
			re.compile("[\w\s]+ total [\w\s]+ cases"): data.get_total_cases,
			re.compile("[\w\s]+ total cases"): data.get_total_cases,
			re.compile("[\w\s]+ total [\w\s]+ deaths"): data.get_total_deaths,
			re.compile("[\w\s]+ total deaths"): data.get_total_deaths,
			re.compile("[\w\s]+ total [\w\s]+ recovered"): data.get_recovered,
			re.compile("[\w\s]+ total recovered"): data.get_recovered
	}

	country_patterns = {
			re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['country_cases'],
			re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['country_deaths'],
			re.compile("[\w\s]+ recovered [\w\s]+"): lambda country: data.get_country_data(country)['country_recovered'],
			re.compile("[\w\s]+ tests [\w\s]+"): lambda country: data.get_country_data(country)['country_tests'],
			re.compile("[\w\s]+ population [\w\s]+"): lambda country: data.get_country_data(country)['population']
	}

	update_pattern = "update"

	# Loop to accept audio until quit word
	while True:
		print("Start speaking...")
		text = get_audio()
		print(text)
		result = None

		# Loop to understand audio related to specific countries
		for pattern, func in country_patterns.items():
			if pattern.match(text):
				words = set(text.split(" "))
				for country in country_list:
					if country in words:
						result = func(country)
						break

		# Loop to understand audio related to the worldwide statistics
		for pattern, func in total_patterns.items():
			if pattern.match(text):
				result = func()
				break

		# If statement to understand audio when update is asked for
		if text == update_pattern:
			result = "Data is being updated. This may take a few minutes."
			data.update_data()

		# Program speaks and prints the requested statistic 
		if result:
			print(result)
			speak(result)
			print()

		# Quits loop
		if text.find(quit) != -1:
			print("Exit")
			break

# Runs main
main()