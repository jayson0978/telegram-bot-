import logging
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

import json
import pandas as pd
import datetime

from config import TOKEN, ADMIN_PASSWORD

logging.basicConfig(level=logging.INFO)


storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

# States
class Form(StatesGroup):
    room_num = State() 
    day = State()
    from_t = State()
    to_t = State() 
    stat = State()



week_days = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")


#-------------------------------file handling----------------#
with open("data/language.json") as file:
	lan_data = json.load(file)


with open("data/user_lan.json") as file:
	r_lan_data = json.load(file)

with open("data/info.json") as file:
	info = json.load(file)

with open("data/available_room.json") as file:
	able_rooms = json.load(file)


student_data = pd.read_csv("data/students.csv")



#------------------------------------------------------Functions---------------------------------------#
def buttons_in_start(names, request_num=False):
	keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
	for name in names:
		keyboard.add(types.KeyboardButton(text=name, request_contact=request_num))
	return keyboard


def week_button(names):
	keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
	for i , a in names:
		keyboard.add(types.KeyboardButton(text=i), types.KeyboardButton(text=a))
	return keyboard

#-----------------------------------changing the variables in text to a new input--------------------#
def text_update(text, **variables):
	for var, new_val in variables.items():
		text = text.replace(var, new_val)
	return text


def get_keyboard(button_names):
	buttons = []
	keyboard = types.InlineKeyboardMarkup(row_width=2)
	for lan, call_data in button_names.items():
		buttons.append(types.InlineKeyboardButton(text=lan, callback_data=f"{call_data}_language"))
	keyboard.add(*buttons)
	return keyboard


def rooms_text(initial_text, able_rooms):
	text_lines = ""
	count = 0
	room_cond = {}
	for num in able_rooms:
		room_cond[num] = able_rooms[num]["num_students"]
	for room_num, student_num in room_cond.items():
		count += 1
		text_line = f"<b>{count}. </b>{room_num}({student_num}/10)\n"
		text_lines += text_line

	return initial_text + text_lines


#---------------------------------inline keyboards---------------------------#

def room_btns(able_rooms):
	keyboard = types.InlineKeyboardMarkup(row_width=4)
	buttons = []
	count = 0
	for room_num in able_rooms:
		count += 1
		buttons.append(types.InlineKeyboardButton(text=str(count), callback_data=room_num))
	keyboard.add(*buttons)
	return keyboard



def orgineze_room_btn(able_rooms, room_num):
	keyboard = types.InlineKeyboardMarkup(row_width=2)
	buttons = []
	time = able_rooms[room_num]["week"]
	for day in able_rooms[room_num]["week"].items():
		from_t = time[day[0]]["from"]
		to_t = time[day[0]]["to"]
		button_text = f"{day[0]} {from_t}:00-{to_t}:00"
		callback_data1 = f"{room_num}_{day[0]}"
		buttons.append(types.InlineKeyboardButton(text=button_text, callback_data=callback_data1))
	keyboard.add(*buttons)
	return keyboard


def get_buttons(data: dict, row_width: int):
	keyboard = types.InlineKeyboardMarkup(row_width=row_width)
	buttons = []
	for text, call_query in data.items():
		buttons.append(types.InlineKeyboardButton(text=text, callback_data=call_query))
	keyboard.add(*buttons)
	return keyboard




#-----------------------------start commans------------------------#
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
	if not str(message.from_user.id) in r_lan_data:       #if the user isn't in the db, set it's language to english 
		r_lan_data[str(message.from_user.id)] = "eng"

	user_lan = r_lan_data[str(message.from_user.id)]

	msg = text_update(text=lan_data[user_lan]["greating_msg"], name123=message.from_user.first_name)

	example_msg = lan_data[user_lan]["example_data"]
	await message.answer(msg)
	await message.answer(example_msg)


#---------------------------Changing the bot language-----------------------#
@dp.message_handler(commands=['language'])
async def change_lan(message: types.Message):
	user_lan = r_lan_data[str(message.from_user.id)]
	text = lan_data[user_lan]["lan_change"]
	await message.answer(text=text, reply_markup=get_keyboard(button_names=info["languages"]))







#------------------------------Callback_quary_handler---------------------------#
#removes the room info from available_room.json
@dp.callback_query_handler(text_contains="remove_")
async def accept_booking(call: types.CallbackQuery):
	user_lan = r_lan_data[str(call.from_user.id)]
	room_num = call.data.split("_")[1]
	able_rooms.pop(room_num)
	with open("data/available_room.json", "w") as file:
		json.dump(able_rooms, file)
	await call.message.edit_text(lan_data[user_lan]["remove_msg"])



#if the admin accept to give the room to the students
@dp.callback_query_handler(text_contains="approved")
async def accept_booking(call: types.CallbackQuery):
	room_num = call.data.split("_")[0]
	student_chat_id = able_rooms[room_num]["students"]
	for i in student_chat_id:
		user_lan = r_lan_data[str(i)]
		msg = text_update(text=lan_data[user_lan]["notification"], room123=room_num)
		await bot.send_message(i, text=msg)

	able_rooms[room_num]["accepted"] = True
	with open("data/available_room.json", "w") as file:
		json.dump(able_rooms, file)
	await call.message.edit_text(text ="✅" + lan_data[r_lan_data[str(call.from_user.id)]]["nts_btn"])


#if the admin rejects the bookings 1 clear student list 2 send notification to the users about not approving
@dp.callback_query_handler(text_contains="nononono")
async def reject_booking(call: types.CallbackQuery):
	room_num = call.data.split("_")[0]
	student_chat_id = able_rooms[room_num]["students"]
	for i in student_chat_id:
		user_lan = r_lan_data[str(i)]
		msg = text_update(lan_data[user_lan]["no_accept_notif"], room123=room_num)

		able_rooms[room_num]["students"] = []                      #clearing the room data couse the user decide to reject the bookings
		able_rooms[room_num]["responsible_student"]["name"] = ""
		able_rooms[room_num]["accepted"] = False
		with open("data/available_room.json", "w") as file:
			json.dump(able_rooms, file)
		await bot.send_message(i, text=msg)
	await call.message.edit_text(text="❎"+lan_data[r_lan_data[str(call.from_user.id)]]["no_accept_notif_admin"])


#if the user accepts to take the responsibility of the room
@dp.callback_query_handler(text_contains="accept")
async def accept_pressed(call: types.CallbackQuery):
	user_lan = r_lan_data[str(call.from_user.id)]
	room_num = call.data.split("_")[0]
	user_name = call.from_user.first_name
	msg = text_update(text=lan_data[user_lan]["accept_msg"], name123=user_name)
	able_rooms[room_num]["responsible_student"]["name"] = user_name
	able_rooms[room_num]["students"].append(call.message.chat.id) 

	with open("data/available_room.json", "w") as file:
		json.dump(able_rooms, file)
	await call.message.edit_text(text=msg)
	

#if the user rejects to take the responsibility of the room
@dp.callback_query_handler(text_contains="reject")
async def accept_pressed(call: types.CallbackQuery):
	user_lan = r_lan_data[str(call.from_user.id)]
	room_num = call.data.split("_")[0]
	msg = lan_data[user_lan]["reject_text"]
	able_rooms[room_num]["students"].append(call.message.chat.id)
	with open("data/available_room.json", "w") as file:
		json.dump(able_rooms, file)
	await call.message.edit_text(msg)


#Changing the bot language
@dp.callback_query_handler(text_contains="language")
async def changing_lan(call: types.CallbackQuery):
	user_lan = r_lan_data[str(call.from_user.id)]
	call.data = call.data.split("_")[0]
	call_data = []
	for i in info["languages"]:
		call_data.append(info["languages"][i])
	if call.data in call_data:
		r_lan_data[str(call.from_user.id)] = call.data
		with open("data/user_lan.json", "w") as file:
			json.dump(r_lan_data, file)
		btn_name = []
		booking_btn = lan_data[user_lan]["booking"]
		cont_btn_name = lan_data[user_lan]["contact_btn"]
		btn_name.append(booking_btn)
		btn_name.append(cont_btn_name)
		await call.message.edit_text(f'{lan_data[call.data]["lan_change_response"]} 👇 /start')


#---------------------------------available time-------------------------#
@dp.callback_query_handler(text_contains="_")
async def time(call: types.CallbackQuery):
	user_lan = r_lan_data[str(call.from_user.id)]
	room_num = call.data.split("_")[0]
	able_rooms[room_num]["num_students"] += 1
	with open("data/available_room.json", "w") as file:
		json.dump(able_rooms, file)
	msg = lan_data[user_lan]["respon_per"]

	data = {
	lan_data[user_lan]["respon_per_btn1"]: f"{room_num}_accept",
	lan_data[user_lan]["respon_per_btn2"]: f"{room_num}_reject"
	}
	await call.message.edit_text(msg, reply_markup=get_buttons(data, 2))


@dp.callback_query_handler()
async def callbacks_lan(call: types.CallbackQuery):
	await call.answer(cache_time=60)
	user_lan = r_lan_data[str(call.from_user.id)]
	a = ""
	try:
		a = int(call.data)
	except:
		pass
	if type(a) == int:
		msg = text_update(text=lan_data[user_lan]["room_btn_pressed"], name123=call.from_user.first_name, room123=call.data)
		await call.message.edit_text(msg, reply_markup=orgineze_room_btn(able_rooms, call.data))





#-------------------------------text handlers---------------------------------#
#--------------------------------Admin side-----------------------------------#
#if the user inserts the admin password checking and giving access to change the data 
@dp.message_handler(lambda message: message.text == ADMIN_PASSWORD)
async def is_admin(message: types.Message):
	user_lan = r_lan_data[str(message.from_user.id)]
	names = [lan_data[user_lan][i] for i in ["bookings_btn", "able_btn"]]
	await message.reply(text=lan_data[user_lan]["password_conf"]+"✅", reply_markup=types.ReplyKeyboardRemove())
	await message.answer(text=lan_data[user_lan]["next_step"], reply_markup=buttons_in_start(names))


#show the availability of the rooms 
availability_btn = [lan_data[lan]["able_btn"] for lan in lan_data]
@dp.message_handler(lambda message: message.text in availability_btn)
async def change_availability(message: types.Message):
	user_lan = r_lan_data[str(message.from_user.id)]
	await message.reply(text=lan_data[user_lan]["booking"], reply_markup=buttons_in_start([lan_data[user_lan]["add_room"]]))
	now = datetime.datetime.now()
	later = now.replace(day=now.day+7)
	for room_num in able_rooms:
		time_str = ""
		time = able_rooms[room_num]["week"]
		for day in able_rooms[room_num]["week"].items():
			from_t = time[day[0]]["from"]
			to_t = time[day[0]]["to"]
			button_text = f"{day[0]} {from_t}:00-{to_t}:00"
			time_str += f"{button_text}\n"
		msg = text_update(text=lan_data[user_lan]["able_room"], room123=room_num)+ "\n" + time_str

		remove_btn = {lan_data[user_lan]["remove"]: f"remove_{room_num}"}
		await message.answer(text=msg, reply_markup=get_buttons(remove_btn, 1))



#show the bookings to the admin
bookings_list = [lan_data[lan]["bookings_btn"] for lan in lan_data]
@dp.message_handler(lambda message: message.text in bookings_list)
async def bookings(message: types.Message):
	user_lan = r_lan_data[str(message.from_user.id)]
	for room_num in able_rooms:
		if not able_rooms[room_num]["accepted"]:
			student_stat = f"({len(able_rooms[room_num]['students'])}/10)"
			starting_txt = text_update(lan_data[user_lan]["bookings_txt"], room123=room_num, student123=student_stat)
			if able_rooms[room_num]["responsible_student"]["name"]:
				txt = f"\n{able_rooms[room_num]['responsible_student']['name']} (in charge)"
				msg = starting_txt + txt
				if len(able_rooms[room_num]['students']) >= 10:
					keyboard = {
					lan_data[user_lan]["respon_per_btn1"]: f"{room_num}_approved",
					lan_data[user_lan]["respon_per_btn2"]: f"{room_num}_nononono"
					}
				else:
					keyboard = {
					lan_data[user_lan]["respon_per_btn2"]: f"{room_num}_nononono"
					}
				await message.answer(text=msg, reply_markup=get_buttons(keyboard, 2))

			else:
				if len(able_rooms[room_num]['students']) == 0:
					msg = starting_txt
					await message.answer(text=msg)
				else:
					msg = starting_txt
					keyboard = {
					lan_data[user_lan]["respon_per_btn2"]: f"{room_num}_nononono"
					}
					await message.answer(text=msg, reply_markup=get_buttons(keyboard, 2))




#adding rooms to the available_room.json
add_room_txt= [lan_data[lan]["add_room"] for lan in lan_data]
@dp.message_handler(lambda message: message.text in add_room_txt)
async def add_room(message: types.Message):
	user_lan = r_lan_data[str(message.from_user.id)]
	await Form.room_num.set()
	msg = lan_data[user_lan]["add_room_msg"]
	await message.answer(text=msg, reply_markup=types.ReplyKeyboardRemove())




#adding room info #room number
@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.room_num)
async def process_age_invalid(message: types.Message):
	user_lan = r_lan_data[str(message.from_user.id)]
	"""
	If room number is invalid
	"""
	return await message.reply(lan_data[user_lan]["invalid_room_num"])


#taking the room number
@dp.message_handler(lambda message: message.text.isdigit(), state=Form.room_num)
async def process_age(message: types.Message, state: FSMContext):
	user_lan = r_lan_data[str(message.from_user.id)]
	async with state.proxy() as data:
		data["room_num"] = message.text

	await Form.next()
	msg = text_update(lan_data[user_lan]["insert_time"], room123=data["room_num"])
	today = datetime.datetime.today().weekday() + 1   #weekday as a number from 0 to 6
	days = "0123456"
	before = days[today:]
	after = days[:today]
	days = before+after
	button_names = [week_days[int(i)] for i in days]
	f = lambda A, n=2: [A[i:i+n] for i in range(0, len(A), n)]    #dividing week days by 2 parts
	button_names = f(button_names)
	button_names[0][0] = "Today"
	button_names[3].append("Cancel")
	await message.answer(msg, reply_markup=week_button(button_names))


#taking the name of the week day
@dp.message_handler(lambda message: message.text in week_days or message.text == "Today" or message.text == "Cancel", state=Form.day)
async def filling_room_info(message: types.Message, state: FSMContext):
	user_lan = r_lan_data[str(message.from_user.id)]
	async with state.proxy() as data:
		if message.text == "Cancel":
			await state.finish()
			names = [lan_data[user_lan][i] for i in ["bookings_btn", "able_btn"]]
			await message.answer(text=lan_data[user_lan]["cenceled"], reply_markup=buttons_in_start(names))
			return
		elif message.text == "Today":
			today = datetime.datetime.today().weekday() + 1 
			data["day"] = week_days[today]
		else:
			data["day"] = message.text
	await Form.next()
	await message.answer(lan_data[user_lan]["from_time"], reply_markup=types.ReplyKeyboardRemove())


#taking "from time"
@dp.message_handler(lambda message: message.text.isdigit(), state=Form.from_t)
async def process_from_t(message: types.Message, state: FSMContext):
	user_lan = r_lan_data[str(message.from_user.id)]
	async with state.proxy() as data:
		data["from_t"] = int(message.text)
	await Form.next()
	msg = lan_data[user_lan]["to_time"]
	await message.answer(msg)

#taking "to time"
@dp.message_handler(lambda message: message.text.isdigit(), state=Form.to_t)
async def process_from_t(message: types.Message, state: FSMContext):
	user_lan = r_lan_data[str(message.from_user.id)]
	async with state.proxy() as data:
		data["to_t"] = int(message.text)
	await Form.next()
	msg = lan_data[user_lan]["finish"]
	btn_names = [lan_data[user_lan]["save"], lan_data[user_lan]["cencel"]]
	await message.answer(msg, reply_markup=buttons_in_start(btn_names))


#saving or cancelling the proccess
@dp.message_handler(state=Form.stat)
async def process_from_t(message: types.Message, state: FSMContext):
	user_lan = r_lan_data[str(message.from_user.id)]
	async with state.proxy() as data:
		data["stat"] = message.text
	if data["stat"] == lan_data[user_lan]["cencel"]:                 #cencel the proccess
		await state.finish()
		names = [lan_data[user_lan][i] for i in ["bookings_btn", "able_btn"]]
		await message.answer(text=lan_data[user_lan]["cenceled"], reply_markup=buttons_in_start(names))
		return
	elif data["stat"] == lan_data[user_lan]["save"]:                 #saving the room info
		if data["room_num"] in able_rooms:
			able_rooms[data["room_num"]]["week"][data["day"]] = {
			"from": data["from_t"],
			"to": data["to_t"],
			"date":{
			"now":"",
			"week later": ""
			}
			}
		else:
			able_rooms[data["room_num"]]={
			"num_students": 0,
			"students": [],
			"responsible_student":{
				"name": ""
				},
			"accepted": False,
			"week":{
			data["day"]:{
			"from": data["from_t"],
			"to": data["to_t"],
			"date":{
			"now":"",
			"week later": ""
			}
			}
			}
			}
		with open("data/available_room.json", "w") as file:
			json.dump(able_rooms, file)
		await state.finish()
		msg = lan_data[user_lan]["saved"]
		names = [lan_data[user_lan][i] for i in ["bookings_btn", "able_btn"]]
		await message.answer(msg, reply_markup=buttons_in_start(names))


#----------------------------------------Contact-----------------------------------#
contact_btn_name= [lan_data[lan]["contact_btn"] for lan in lan_data]
@dp.message_handler(lambda message: message.text in contact_btn_name)
async def without_puree(message: types.Message):
	msg = info["admin_cont"]
	await message.answer(msg)


booking_btn_name = [lan_data[lan]["booking"] for lan in lan_data]
@dp.message_handler(lambda message: message.text in booking_btn_name)
async def without_puree(message: types.Message):
	user_lan = r_lan_data[str(message.from_user.id)]
	msg = rooms_text(initial_text=lan_data[user_lan]["rooms"], able_rooms=able_rooms)
	await message.answer(msg, parse_mode=types.ParseMode.HTML, reply_markup=room_btns(able_rooms))


#-------------------------Cheking the student info----------------------------#
@dp.message_handler(content_types="text")
async def check_student_data(message: types.Message):
	user_lan = r_lan_data[str(message.from_user.id)]
	text = message.text.lower()
	student_id = text[:6]
	passport_num = text[len(text)-9:]
	msg = "✅\n"+lan_data[user_lan]["proved"]

	btn_name = []
	booking_btn = lan_data[user_lan]["booking"]
	cont_btn_name = lan_data[user_lan]["contact_btn"]
	btn_name.append(booking_btn)
	btn_name.append(cont_btn_name)

	if student_id in list(student_data["id"]):             #checking the student id
		s_name = student_data.loc[student_data["id"] == student_id]
		s_name = s_name["passport number"].item().lower()
		if s_name == passport_num:                         #checking student passport number
			await message.answer(text=msg, reply_markup=buttons_in_start(names=btn_name))







if __name__ == '__main__':
    executor.start_polling(dp)
    