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
import json

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
    if not notify_exam_and_hw.is_running():
        notify_exam_and_hw.start()

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

    last_class_end = (datetime.combine(now.date(), start_time) + timedelta(minutes=CLASS_DURATION * len(timetable_today))).time()
    if now.time().hour == last_class_end.hour and now.time().minute == last_class_end.minute:
        await channel.send("หมดคาบเรียนแล้ววันนี้ ขอให้เดินทางโดยสวัสดิภาพ 🚌")

@tasks.loop(minutes=1)
async def notify_exam_and_hw():
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    if now.hour == 19 and now.minute == 0:
        channel = discord.utils.get(bot.get_all_channels(), id=CHANNEL_ID)
        if not channel:
            return

        # แจ้งเตือนสอบ
        exams = load_exams()
        if exams:
            msg = "⏰ แจ้งเตือนสอบ\n"
            for e in exams:
                exam_date = datetime.strptime(e['date'], "%Y-%m-%d").replace(tzinfo=tz)
                days_left = (exam_date.date() - now.date()).days
                if days_left >= 0:
                    msg += f"- {e['subject']} : เหลืออีก {days_left} วัน (สอบวันที่ {exam_date.strftime('%d/%m/%Y')})\n"
            await channel.send(msg)

        # แจ้งเตือนการบ้าน
        homeworks = load_homeworks()
        if homeworks:
            msg = "📚 แจ้งเตือนการบ้าน\n"
            for h in homeworks:
                due_date = datetime.strptime(h['date'], "%Y-%m-%d").replace(tzinfo=tz)
                days_left = (due_date.date() - now.date()).days
                if days_left >= 0:
                    msg += f"- {h['subject']} : เหลืออีก {days_left} วัน (ส่งวันที่ {due_date.strftime('%d/%m/%Y')})\n"
            await channel.send(msg)

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

@bot.command(name="nextclass")
async def next_class(ctx):
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    weekday = now.strftime("%A").lower()
    if weekday not in TIMETABLE:
        await ctx.send("วันนี้ไม่มีเรียน")
        return

    start_time = dtime(8, 10)
    timetable_today = TIMETABLE[weekday]
    for i in range(len(timetable_today)):
        class_start = (datetime.combine(now.date(), start_time) + timedelta(minutes=CLASS_DURATION * i)).time()
        class_end = (datetime.combine(now.date(), start_time) + timedelta(minutes=CLASS_DURATION * (i + 1))).time()
        if now.time() < class_start:
            class_info = timetable_today[i]
            await ctx.send(
                f"คาบถัดไปคือคาบที่ {i+1}\n"
                f"วิชา: {class_info['subject_code']}\n"
                f"ห้อง: {class_info['room']}\n"
                f"เริ่มเวลา: {class_start.strftime('%H:%M')}"
            )
            return
    await ctx.send("วันนี้ไม่มีคาบถัดไปแล้ว หรือหมดคาบเรียนแล้ววันนี้")

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

ROLE_MESSAGE_ID = None  # เก็บ message id ที่ใช้รับยศ
ROLE_EMOJI = "✅"       # อีโมจิที่ใช้รับยศ
ROLE_NAME = "MSEPtub7"  # ชื่อ role

@bot.command(name="setuprole")
@commands.has_permissions(administrator=True)
async def setup_role_message(ctx):
    """ส่งข้อความสำหรับรับยศ (admin ใช้ครั้งเดียว)"""
    msg = await ctx.send(f"กด {ROLE_EMOJI} เพื่อรับยศ {ROLE_NAME}")
    await msg.add_reaction(ROLE_EMOJI)
    global ROLE_MESSAGE_ID
    ROLE_MESSAGE_ID = msg.id

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != ROLE_MESSAGE_ID:
        return
    if str(payload.emoji) != ROLE_EMOJI:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member is None or member.bot:
        return

    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if role is None:
        role = await guild.create_role(name=ROLE_NAME)
    await member.add_roles(role)
    try:
        await member.send(f"คุณได้รับยศ {role.name} เรียบร้อยแล้ว!")
    except Exception:
        pass

EXAM_FILE = "exams.json"

def load_exams():
    try:
        with open(EXAM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_exams(exams):
    with open(EXAM_FILE, "w", encoding="utf-8") as f:
        json.dump(exams, f, ensure_ascii=False, indent=2)

@bot.command(name="exam")
async def add_exam(ctx, subject: str, date: str, year: int = None):
    """เพิ่มรายการสอบ เช่น /exam BIO 10/07 หรือ /exam BIO 10/07 2025"""
    try:
        parts = date.split("/")
        if len(parts) != 2:
            await ctx.send("รูปแบบวันที่ไม่ถูกต้อง ใช้ /exam <ชื่อวิชา> <วัน/เดือน> [ปี] เช่น /exam BIO 10/07 หรือ /exam BIO 10/07 2025")
            return
        day, month = map(int, parts)
        tz = pytz.timezone('Asia/Bangkok')
        now = datetime.now(tz)
        if year is None:
            year = now.year
        exam_date = datetime(year, month, day, 0, 0, tzinfo=tz)
        if exam_date < now:
            await ctx.send(f"วันสอบ {exam_date.strftime('%d/%m/%Y')} ผ่านไปแล้ว ไม่สามารถเพิ่มได้")
            return
    except Exception:
        await ctx.send("รูปแบบวันที่ไม่ถูกต้อง ใช้ /exam <ชื่อวิชา> <วัน/เดือน> [ปี] เช่น /exam BIO 10/07 หรือ /exam BIO 10/07 2025")
        return

    exams = load_exams()
    exams.append({"subject": subject, "date": exam_date.strftime("%Y-%m-%d")})
    save_exams(exams)
    await ctx.send(f"เพิ่มการสอบ {subject} วันที่ {exam_date.strftime('%d/%m/%Y')} เรียบร้อยแล้ว!")

@bot.command(name="listexam")
async def list_exam(ctx):
    """ดูรายการสอบทั้งหมด (พร้อมนับถอยหลังและสี เรียงวันสอบใกล้สุดขึ้นก่อน)"""
    exams = load_exams()
    if not exams:
        await ctx.send("ยังไม่มีรายการสอบ")
        return

    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    # เรียงจากวันสอบใกล้สุดไปไกลสุด
    exams = sorted(
        exams,
        key=lambda e: (datetime.strptime(e['date'], '%Y-%m-%d').replace(tzinfo=tz) - now).days
    )
    embed = discord.Embed(title="รายการสอบ", color=0x00ff00)
    for e in exams:
        exam_date = datetime.strptime(e['date'], '%Y-%m-%d').replace(tzinfo=tz)
        days_left = (exam_date.date() - now.date()).days
        if days_left < 0:
            continue  # ข้ามรายการที่สอบไปแล้ว
        # เลือกสี
        if days_left <= 3:
            color = 0xff0000  # แดง
        elif days_left <= 7:
            color = 0xffa500  # เหลือง
        else:
            color = 0x00ff00  # เขียว
        embed.color = color
        embed.add_field(
            name=f"{e['subject']} (สอบวันที่ {exam_date.strftime('%d/%m/%Y')})",
            value=f"เหลืออีก **{days_left}** วัน",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command(name="listhw")
async def list_hw(ctx):
    """ดูรายการการบ้านทั้งหมด (เรียงวันส่งใกล้สุดขึ้นก่อน)"""
    homeworks = load_homeworks()
    if not homeworks:
        await ctx.send("ยังไม่มีรายการการบ้าน")
        return
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    # เรียงจากวันส่งใกล้สุดไปไกลสุด
    homeworks = sorted(
        homeworks,
        key=lambda h: (datetime.strptime(h['date'], '%Y-%m-%d').replace(tzinfo=tz) - now).days
    )
    embed = discord.Embed(title="รายการการบ้าน", color=0x00ff00)
    for h in homeworks:
        due_date = datetime.strptime(h['date'], '%Y-%m-%d').replace(tzinfo=tz)
        days_left = (due_date.date() - now.date()).days
        if days_left < 0:
            continue  # ข้ามรายการที่เลยกำหนดส่งแล้ว
        # เลือกสี
        if days_left <= 3:
            color = 0xff0000  # แดง
        elif days_left <= 7:
            color = 0xffa500  # เหลือง
        else:
            color = 0x00ff00  # เขียว
        embed.color = color
        embed.add_field(
            name=f"{h['subject']} (ส่งวันที่ {due_date.strftime('%d/%m/%Y')})",
            value=f"เหลืออีก **{days_left}** วัน",
            inline=False
        )
    await ctx.send(embed=embed)

HW_FILE = "homeworks.json"

def load_homeworks():
    try:
        with open(HW_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_homeworks(homeworks):
    with open(HW_FILE, "w", encoding="utf-8") as f:
        json.dump(homeworks, f, ensure_ascii=False, indent=2)

@bot.command(name="hw")
async def add_hw(ctx, subject: str, date: str, year: int = None):
    """เพิ่มการบ้าน เช่น /hw MATH 15/07 หรือ /hw MATH 15/07 2025"""
    try:
        parts = date.split("/")
        if len(parts) != 2:
            await ctx.send("รูปแบบวันที่ไม่ถูกต้อง ใช้ /hw <ชื่อวิชา> <วัน/เดือน> [ปี] เช่น /hw MATH 15/07 หรือ /hw MATH 15/07 2025")
            return
        day, month = map(int, parts)
        tz = pytz.timezone('Asia/Bangkok')
        now = datetime.now(tz)
        if year is None:
            year = now.year
        due_date = datetime(year, month, day, 0, 0, tzinfo=tz)
        if due_date < now:
            await ctx.send(f"วันส่ง {due_date.strftime('%d/%m/%Y')} ผ่านไปแล้ว ไม่สามารถเพิ่มได้")
            return
    except Exception:
        await ctx.send("รูปแบบวันที่ไม่ถูกต้อง ใช้ /hw <ชื่อวิชา> <วัน/เดือน> [ปี] เช่น /hw MATH 15/07 หรือ /hw MATH 15/07 2025")
        return

    homeworks = load_homeworks()
    homeworks.append({"subject": subject, "date": due_date.strftime("%Y-%m-%d")})
    save_homeworks(homeworks)
    await ctx.send(f"เพิ่มการบ้าน {subject} ส่งวันที่ {due_date.strftime('%d/%m/%Y')} เรียบร้อยแล้ว!")

@bot.command(name="helptub7")
async def helptub7(ctx):
    embed = discord.Embed(
        title="📚 คำสั่งช่วยเหลือบอท class_tub_7",
        description="รวมคำสั่งหลักที่ใช้กับบอทนี้",
        color=0x3498db
    )
    embed.add_field(
        name="/class now",
        value="ดูคาบเรียนปัจจุบัน",
        inline=False
    )
    embed.add_field(
        name="/nextclass",
        value="ดูคาบถัดไปของวันนี้",
        inline=False
    )
    embed.add_field(
        name="/event40mins, /event50mins",
        value="ตั้งความยาวคาบเรียน (40 หรือ 50 นาที)",
        inline=False
    )
    embed.add_field(
        name="/exam <ชื่อวิชา> <วัน/เดือน> [ปี]",
        value="เพิ่มรายการสอบ เช่น `/exam BIO 10/07` หรือ `/exam BIO 10/07 2025`",
        inline=False
    )
    embed.add_field(
        name="/listexam",
        value="ดูรายการสอบทั้งหมด (เรียงวันสอบใกล้สุดขึ้นก่อน)",
        inline=False
    )
    embed.add_field(
        name="/hw <ชื่อวิชา> <วัน/เดือน> [ปี]",
        value="เพิ่มการบ้าน เช่น `/hw MATH 15/07` หรือ `/hw MATH 15/07 2025`",
        inline=False
    )
    embed.add_field(
        name="/listhw",
        value="ดูรายการการบ้านทั้งหมด (เรียงวันส่งใกล้สุดขึ้นก่อน)",
        inline=False
    )
    embed.add_field(
        name="/รับยศ",
        value="รับยศ MSEPtub7 ด้วยปุ่ม หรือใช้ /setuprole สำหรับแอดมินเพื่อสร้างข้อความรับยศแบบรีแอค",
        inline=False
    )
    embed.add_field(
        name="/setuprole (admin)",
        value="สร้างข้อความรับยศแบบรีแอค (admin เท่านั้น)",
        inline=False
    )
    await ctx.send(embed=embed)

bot.run(token, log_handler=handlers, log_level=logging.DEBUG)