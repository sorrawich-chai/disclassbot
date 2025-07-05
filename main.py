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
from timetable import timetable_fidner
from create_crop import create_cropped_image
from timetable2 import timetable_finde

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handlers = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intent = discord.Intents.default()
intent.message_content = True
intent.members = True

bot = commands.Bot(command_prefix='/', intents=intent)
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
ROLE_CHANNEL_ID = int(os.getenv('ROLE_CHANNEL_ID'))  # ใส่ channel id ที่ให้กดรับยศ
TIMETABLE = timetable_finde()

@bot.command(name="table_image")
async def table_image(ctx):
    if not ctx.message.attachments:
        await ctx.send("please insert class table")
        return
    attachment = ctx.message.attachments[0]
    if not attachment.filename.lower().endswith(('.jpg')):
        await ctx.send("ไฟล์ที่แนบไม่ใช่รูปภาพที่รองรับ")
        return
    await attachment.save("class_image.jpg")
    await ctx.send(f"processing...")

    try:
        create_cropped_image("class_image.jpg")
        global TIMETABLE
        TIMETABLE = timetable_fidner()
        await ctx.send(f"Image processed successfully")
        # Send timetable day by day
        for day, classes in TIMETABLE.items():
            msg = f"**{day.capitalize()}**\n"
            for idx, c in enumerate(classes, 1):
                msg += f"{idx}. วิชา: {c.get('subject_code', c.get('subject', ''))} | ห้อง: {c.get('room', '')}\n | ครู: {c.get('teacher', '----')}\n"
            await ctx.send(msg)
    except Exception as e:
        await ctx.send("")

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

    timetable_today = TIMETABLE[weekday].copy()
    # --- แทรกคาบชดเฉยเป็นคาบ 9 ---
    makeup = load_makeup()
    if weekday in makeup:
        from_day = makeup[weekday]["from_day"]
        period = makeup[weekday]["period"]
        if from_day in TIMETABLE and 0 <= period < len(TIMETABLE[from_day]):
            makeup_class = TIMETABLE[from_day][period]
            if len(timetable_today) >= 9:
                timetable_today[8] = makeup_class  # แทนคาบ 9
            else:
                while len(timetable_today) < 8:
                    timetable_today.append({"room": "----", "subject_code": "----"})
                timetable_today.append(makeup_class)

    start_time = dtime(8, 10)
    channel = discord.utils.get(bot.get_all_channels(), id=CHANNEL_ID)
    guild = channel.guild if channel else None

    # --- เวลาคาบแต่ละคาบ (พัก 10 นาทีหลังคาบ 7) ---
    class_times = []
    t = datetime.combine(now.date(), start_time)
    for i in range(len(timetable_today)):
        class_times.append(t.time())
        if i == 6:  # หลังคาบ 7 พัก 10 นาที
            t += timedelta(minutes=CLASS_DURATION + 10)
        else:
            t += timedelta(minutes=CLASS_DURATION)

    for i in range(len(timetable_today) - 1):
        # แจ้งเตือนก่อนจบคาบ 2 นาที
        notify_time = (datetime.combine(now.date(), class_times[i]) + timedelta(minutes=CLASS_DURATION - 2)).time()
        next_class = timetable_today[i + 1]
        if now.time().hour == notify_time.hour and now.time().minute == notify_time.minute:
            subject_role = discord.utils.get(guild.roles, name=next_class['subject_code'])
            if subject_role is None:
                subject_role = await guild.create_role(name=next_class['subject_code'])
            room_role = discord.utils.get(guild.roles, name=next_class['room'])
            if room_role is None:
                room_role = await guild.create_role(name=next_class['room'])
            await channel.send(
                f"{subject_role.mention} {room_role.mention}\n"
                f"⏰ จะหมดคาบที่ {i+1} แล้ว\n"
                f"คาบถัดไป: {next_class['subject_code']} (ห้อง {next_class['room']})"
            )
            break

    # แจ้งเตือนจบคาบสุดท้าย
    last_class_end = (datetime.combine(now.date(), class_times[-1]) + timedelta(minutes=CLASS_DURATION)).time()
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

ROLE_MESSAGE_ID = None  # เก็บ message id ที่ใช้รับยศ
ROLE_EMOJI = "✅"       # อีโมจิที่ใช้รับยศ
ROLE_NAME = "MSEPtub7"  # ชื่อ role

@bot.event
async def on_member_join(member):
    guild = member.guild
    role_name = ROLE_NAME
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
        @discord.ui.button(label=f"รับยศ {ROLE_NAME}", style=discord.ButtonStyle.primary, custom_id=f"get_{ROLE_NAME}")
        async def button_callback(self, interaction: discord.Interaction, button: Button):
            role_name = "MSEPtub7"
            guild = interaction.guild
            role = discord.utils.get(guild.roles, name=role_name)
            if role is None:
                role = await guild.create_role(name=role_name)
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"ได้รับยศ {role.mention} เรียบร้อยแล้ว!", ephemeral=True)
    await ctx.send(f"กดปุ่มด้านล่างเพื่อรับยศ {ROLE_NAME}", view=RoleButtonView())


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

    # แจก role ทุกวิชาและห้องของทุกวัน
    subject_set = set()
    room_set = set()
    for day in TIMETABLE.values():  # <-- ต้องใช้ .values() เพื่อรวมทุกวัน
        for c in day:
            subject_set.add(c['subject_code'])
            room_set.add(c['room'])

    roles_to_give = []
    for name in subject_set | room_set:
        if name == "----" or name == "โรงอาหาร":
            continue
        role = discord.utils.get(guild.roles, name=name)
        if role is None:
            role = await guild.create_role(name=name)
        roles_to_give.append(role)

    await member.add_roles(*roles_to_give)
    try:
        await member.send("คุณได้รับยศทุกวิชาและห้องเรียบร้อยแล้ว!")
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

room = "tub7"  # เปลี่ยนเป็นห้องที่ต้องการ
@bot.command(name=f"help{room}")
async def helptub7(ctx):
    embed = discord.Embed(
        title=f"📚 คำสั่งช่วยเหลือบอท class_{room}",
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
    embed.add_field(
        name="/createroles (admin)",
        value="สร้าง role สำหรับทุกวิชาและห้องใน TIMETABLE (admin เท่านั้น)",
        inline=False
    )
    embed.add_field(
        name="/ชด <วัน> <คาบ>",
        value="แทรกคาบชดเฉยเป็นคาบ 9 ของวันนี้ เช่น `/ชด monday 3`",
        inline=False
    )
    embed.add_field(
        name="/table change (teacher|room|subject_code) (day) (period) (new_value)",
        value="แก้ไขตารางเรียน เช่น `/table change teacher monday 2 ครู...`",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name="createroles")
@commands.has_permissions(administrator=True)
async def create_all_roles(ctx):
    """สร้าง role สำหรับทุกวิชาและห้องใน TIMETABLE (admin เท่านั้น)"""
    guild = ctx.guild
    subject_set = set()
    room_set = set()
    for day in TIMETABLE.values():
        for c in day:
            subject_set.add(c['subject_code'])
            room_set.add(c['room'])
    created = []
    for name in subject_set | room_set:
        if name == "----" or name == "โรงอาหาร":
            continue
        if not discord.utils.get(guild.roles, name=name):
            await guild.create_role(name=name)
            created.append(name)
    if created:
        await ctx.send(f"สร้าง role: {', '.join(created)} เรียบร้อยแล้ว")
    else:
        await ctx.send("มี role ครบทุกวิชาและห้องแล้ว")

MAKEUP_FILE = "makeup.json"

def load_makeup():
    try:
        with open(MAKEUP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_makeup(data):
    with open(MAKEUP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@bot.command(name="ชด")
async def makeup_class(ctx, day: str, period: int):
    """
    ใช้ /ชด <วัน> <คาบ> เช่น /ชด monday 3
    จะนำคาบที่ <period> ของ <day> มาแทรกเป็นคาบ 9 ของวันนี้
    """
    day = day.lower()
    if day not in TIMETABLE:
        await ctx.send("ไม่พบวันดังกล่าว")
        return
    if not (1 <= period <= len(TIMETABLE[day])):
        await ctx.send("คาบที่ระบุไม่ถูกต้อง")
        return
    makeup = load_makeup()
    today = datetime.now(pytz.timezone('Asia/Bangkok')).strftime("%A").lower()
    makeup[today] = {"from_day": day, "period": period-1}  # zero-based index
    save_makeup(makeup)
    subject = TIMETABLE[day][period-1]['subject_code']
    room = TIMETABLE[day][period-1]['room']
    await ctx.send(f"ตั้งคาบชดเฉย: {subject} ({room}) จะมาแทรกเป็นคาบ 9 ของวันนี้ ({today})")



@bot.command(name="table")
async def table_command(ctx, action: str, field: str = None, day: str = None, period: int = None, *, new_value: str = None):
    """
    ใช้ /table change (teacher|room|subject_code) (day) (period) (new_value)
    เช่น /table change teacher monday 2 ครู...
    """
    global TIMETABLE
    if action != "change":
        await ctx.send("ใช้ /table change (teacher|room|subject_code) (day) (period) (new_value)")
        return
    if field not in ("teacher", "room", "subject_code"):
        await ctx.send("field ต้องเป็น teacher, room หรือ subject_code เท่านั้น")
        return
    if day is None or period is None or new_value is None:
        await ctx.send("กรุณาระบุ /table change (teacher|room|subject_code) (day) (period) (new_value)")
        return
    day = day.lower()
    if day not in TIMETABLE:
        await ctx.send("ไม่พบวันดังกล่าว")
        return
    try:
        period = int(period)
        if not (1 <= period <= len(TIMETABLE[day])):
            await ctx.send("คาบที่ระบุไม่ถูกต้อง")
            return
    except Exception:
        await ctx.send("period ต้องเป็นตัวเลข")
        return
    # แก้ไขข้อมูล
    TIMETABLE[day][period-1][field] = new_value
    await ctx.send(f"แก้ไข {field} ของ {day} คาบที่ {period} เป็น \"{new_value}\" เรียบร้อยแล้ว")

@bot.command(name="table_look")
async def table_look(ctx, day: str):
    """
    ใช้ /table_look <day> เช่น /table_look monday
    """
    day = day.lower()
    if day not in TIMETABLE:
        await ctx.send("ไม่พบวันดังกล่าว")
        return
    msg = f"**{day.capitalize()}**\n"
    for idx, c in enumerate(TIMETABLE[day], 1):
        msg += f"{idx}. วิชา: {c.get('subject_code', c.get('subject', ''))} | ห้อง: {c.get('room', '')}\n | ครู: {c.get('teacher', '----')}\n"
    await ctx.send(msg)

bot.run(token, log_handler=handlers, log_level=logging.DEBUG)