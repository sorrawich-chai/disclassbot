import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, time as dtime
import asyncio
import discord.utils
from discord.ui import View, Button
import pytz

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handlers = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intent = discord.Intents.default()
intent.message_content = True
intent.members = True

bot = commands.Bot(command_prefix='/', intents=intent)

# ตารางเรียน
TIMETABLE = {
    "monday": [
        {"room": "3210", "subject_code": "Eng for sci"},
        {"room": "3309", "subject_code": "Thai"},
        {"room": "7504", "subject_code": "math"},
        {"room": "7504", "subject_code": "add math"},
        {"room": "โรงอาหาร", "subject_code": "lunch"},
        {"room": "2409", "subject_code": "physics"},
        {"room": "7301", "subject_code": "แนะแนว"},
        {"room": "----", "subject_code": "ชุมนุม"},
        {"room": "7601", "subject_code": "stat math"},
        {"room": "7601", "subject_code": "stat math"},
    ],
    "tuesday": [
        {"room": "COM 4", "subject_code": "Sketchup"},
        {"room": "COM 4", "subject_code": "Sketchup"},
        {"room": "2102", "subject_code": "physics"},
        {"room": "7504", "subject_code": "math"},
        {"room": "โรงอาหาร", "subject_code": "lunch"},
        {"room": "2302", "subject_code": "BIO"},
        {"room": "2302", "subject_code": "BIO"},
        {"room": "3509", "subject_code": "GEO"},
        {"room": "2401", "subject_code": "research"},
        {"room": "2401", "subject_code": "research"},
    ],
    "wednesday": [
        {"room": "2102", "subject_code": "Chem"},
        {"room": "2102", "subject_code": "Chem"},
        {"room": "3509", "subject_code": "History"},
        {"room": "3209", "subject_code": "ENG"},
        {"room": "โรงอาหาร", "subject_code": "lunch"},
        {"room": "3508", "subject_code": "GEO"},
        {"room": "4304", "subject_code": "Art"},
        {"room": "7502", "subject_code": "add math"},
        {"room": "----", "subject_code": "3rd lang"},
        {"room": "----", "subject_code": "3rd lang"},
    ],
    "thursday": [
        {"room": "COM 2", "subject_code": "com prog"},
        {"room": "COM 2", "subject_code": "com prog"},
        {"room": "3209", "subject_code": "ENG"},
        {"room": "3209", "subject_code": "ENG Native"},
        {"room": "โรงอาหาร", "subject_code": "lunch"},
        {"room": "7502", "subject_code": "สุขศึกษา"},
        {"room": "2", "subject_code": "physics"},
        {"room": "3509", "subject_code": "physics"},
        {"room": "2401", "subject_code": "writing"},
        {"room": "2401", "subject_code": "writing"},
    ],
    "friday": [
        {"room": "2102", "subject_code": "com prog"},
        {"room": "2102", "subject_code": "com prog"},
        {"room": "7504", "subject_code": "ENG"},
        {"room": "7504", "subject_code": "ENG Native"},
        {"room": "โรงอาหาร", "subject_code": "lunch"},
        {"room": "HR(depend)", "subject_code": "สุขศึกษา"},
        {"room": "HR(depend)", "subject_code": "physics"},
        {"room": "3309", "subject_code": "physics"},
    ]
}

CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
ROLE_CHANNEL_ID = int(os.getenv('ROLE_CHANNEL_ID'))  # ใส่ channel id ที่ให้กดรับยศ

@bot.command()
async def test_channel(ctx):
    channel = bot.get_channel(CHANNEL_ID)
    await ctx.send(f"channel = {channel}")

# เพิ่มตัวแปร global สำหรับความยาวคาบ
CLASS_DURATION = 50  # นาที

@bot.command(name="event40mins")
async def event_40mins(ctx):
    global CLASS_DURATION
    CLASS_DURATION = 40
    await ctx.send("ตั้งคาบเรียนเป็น 40 นาทีเรียบร้อยแล้ว!")

@bot.command(name="event50mins")
async def event_50mins(ctx):
    global CLASS_DURATION
    CLASS_DURATION = 50
    await ctx.send("ตั้งคาบเรียนเป็น 50 นาทีเรียบร้อยแล้ว!")

def get_next_class_time():
    now = datetime.now()
    start_time = dtime(8, 10)
    for i in range(len(TIMETABLE.get(now.strftime("%A").lower(), []))):
        class_time = (datetime.combine(now.date(), start_time) + timedelta(minutes=CLASS_DURATION * i)).time()
        if now.time() < class_time:
            return i, class_time
    return None, None

@bot.event
async def on_ready():
    print(f'hihihi Im {bot.user.name}')
    if not notify_class.is_running():
        notify_class.start()

@tasks.loop(minutes=1)
async def notify_class():
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    weekday = now.strftime("%A").lower()
    if weekday not in TIMETABLE:
        return

    timetable_today = TIMETABLE[weekday]
    start_time = dtime(8, 10)
    channel = discord.utils.get(bot.get_all_channels(), id=CHANNEL_ID)
    guild = channel.guild if channel else None
    role = discord.utils.get(guild.roles, name="MSEPtub7") if guild else None
    role_mention = role.mention if role else "@MSEPtub7"

    # แจ้งเตือนเมื่อถึงเวลาจบคาบ
    for i in range(len(timetable_today)):
        class_end = (datetime.combine(now.date(), start_time) + timedelta(minutes=CLASS_DURATION * (i + 1))).time()
        if now.time().hour == class_end.hour and now.time().minute == class_end.minute:
            class_info = timetable_today[i]
            await channel.send(
                f"{role_mention}\n"
                f"⏰ หมดคาบที่ {i+1} แล้ว!\n"
                f"ห้อง: {class_info['room']}  "
                f"วิชา: {class_info['subject_code']}\n"
            )
            break

    # แจ้งเตือนพิเศษเมื่อหมดคาบสุดท้าย
    last_class_end = (datetime.combine(now.date(), start_time) + timedelta(minutes=CLASS_DURATION * len(timetable_today))).time()
    if now.time().hour == last_class_end.hour and now.time().minute == last_class_end.minute:
        await channel.send("หมดคาบเรียนแล้ววันนี้ ขอให้เดินทางโดยสวัสดิภาพ 🚌")

@bot.command(name="class")
async def class_now(ctx, arg=None):
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    if arg != "now":
        await ctx.send("ใช้คำสั่ง `/class now` เพื่อดูคาบปัจจุบัน")
        return

    weekday = now.strftime("%A").lower()
    if weekday not in TIMETABLE:
        await ctx.send("วันนี้ไม่มีเรียน")
        return

    start_time = dtime(8, 10)
    timetable_today = TIMETABLE[weekday]
    found = False
    for i in range(len(timetable_today)):
        class_start = (datetime.combine(now.date(), start_time) + timedelta(minutes=CLASS_DURATION * i)).time()
        class_end = (datetime.combine(now.date(), start_time) + timedelta(minutes=CLASS_DURATION * (i + 1))).time()
        if class_start <= now.time() < class_end:
            class_info = timetable_today[i]
            await ctx.send(
                f"ตอนนี้เป็นคาบที่ {i+1}\n"
                f"วิชา: {class_info['subject_code']}\n"
                f"ห้อง: {class_info['room']}"
            )
            found = True
            break
    if not found:
        # เช็คว่าก่อนคาบแรกหรือหลังคาบสุดท้าย
        first_class_start = (datetime.combine(now.date(), start_time)).time()
        last_class_end = (datetime.combine(now.date(), start_time) + timedelta(minutes=CLASS_DURATION * len(timetable_today))).time()
        if now.time() < first_class_start:
            await ctx.send("ขณะนี้ยังไม่ถึงเวลาเรียน")
        elif now.time() >= last_class_end:
            await ctx.send("หมดคาบเรียนแล้ววันนี้ ขอให้เดินทางโดยสวัสดิภาพ 🚌")
        else:
            await ctx.send("ขณะนี้ไม่อยู่ในช่วงเวลาเรียน")

@bot.event
async def on_member_join(member):
    guild = member.guild
    role_name = "MSEPtub7"
    # ค้นหา role ถ้ายังไม่มีให้สร้างใหม่
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        role = await guild.create_role(name=role_name)
    await member.add_roles(role)
    try:
        await member.send(f"ยินดีต้อนรับสู่เซิร์ฟเวอร์! คุณได้รับยศ {role_name} แล้ว")
    except Exception:
        pass  # กรณีปิด DM

@bot.command(name="รับยศ")
async def give_role_button(ctx):
    if ctx.channel.id != ROLE_CHANNEL_ID:
        await ctx.send("กรุณากดรับยศในห้องที่กำหนดเท่านั้น")
        return
    class RoleButtonView(View):
        @discord.ui.button(label="รับยศ MSEPtub7", style=discord.ButtonStyle.primary, custom_id="get_mseptub7")
        async def button_callback(self, interaction: discord.Interaction, button: Button):
            role_name = "MSEPtub7"
            guild = interaction.guild
            role = discord.utils.get(guild.roles, name=role_name)
            if role is None:
                role = await guild.create_role(name=role_name)
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"ได้รับยศ {role.mention} เรียบร้อยแล้ว!", ephemeral=True)
    await ctx.send("กดปุ่มด้านล่างเพื่อรับยศ MSEPtub7", view=RoleButtonView())

bot.run(token, log_handler=handlers, log_level=logging.DEBUG)