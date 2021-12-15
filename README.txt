Room booking bot made bu aiogram library

How to use it?
1 install these libraries 
	pip install -U aiogram
	pip install python-dotenv
	pip install pandas
2. Open .env file and insert your bots TOKEN and ADMIN_PASSWORD(if the user have admin password they can use the bot as admin and can modife files)
3. run main.py file
4. Firstly, the bot asks the user to enter student id and pasword number 
Enter (U12345 AA1234567)
5. if you want to use the bot as admin send the ADMIN_PASSWORD after /starting it
6. Now bot works in 2 languages. To update languages open language.json file do these if you don't skip
	6.1 From the end of the file type your language code e.g. "uz", "rus"
	6.2 Translate the text in other languages above with the same "key"
	6.3 Text contains some variables(student123 or room123) to change them into room number or user name. Don't translate them.
	6.4 The last, open info.json file and Enter your new language name and its language code respectively 
