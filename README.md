# 📚 Discord Timetable

This project is a **Discord bot** designed to assist students with their class schedules. It automatically sends timetable reminders, exam/homework notifications, and even processes uploaded timetable images by cropping them into individual class slots.

## 🚀 Features

* 📅 **Timetable Notifications**: Sends reminders for upcoming classes.
* 📷 **Image Cropping**: Crops timetable images into individual class slots for easier processing.
* 📌 **Exam and Homework Tracking**: Allows adding, listing, and counting down to exams and homework deadlines.
* 🔔 **Automatic Role Management**: Assigns roles for subjects and rooms to users.
* 📖 **Interactive Commands**: Includes commands for viewing the current/next class, modifying timetables, and setting class durations.

## 🛠️ Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/discord-timetable-bot.git
   cd discord-timetable-bot
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory and add:

   ```env
   DISCORD_TOKEN=your_bot_token
   CHANNEL_ID=your_channel_id
   ROLE_CHANNEL_ID=your_role_channel_id
   ```

## 📂 File Structure

* `main.py`: The main Discord bot logic.
* `create_crop.py`: Handles image cropping for timetable processing.
* `requirements.txt`: List of required Python packages.
* `exams.json`, `homeworks.json`, `makeup.json`: Stores exam, homework, and makeup class data.

## 📜 Commands Overview

| Command                        | Description                             |
| ------------------------------ | --------------------------------------- |
| `/class now`                   | View the current class                  |
| `/nextclass`                   | View the next class of the day          |
| `/event40mins`, `/event50mins` | Set class duration to 40 or 50 minutes  |
| `/exam <subject> <dd/mm>`      | Add an exam                             |
| `/listexam`                    | List all exams                          |
| `/hw <subject> <dd/mm>`        | Add a homework                          |
| `/listhw`                      | List all homework assignments           |
| `/รับยศ`                       | Get subject and room roles via a button |
| `/setuprole` (admin)           | Create a role setup message             |
| `/createroles` (admin)         | Create roles for all subjects and rooms |
| `/table change ...`            | Modify the timetable entries            |
| `/table_look <day>`            | View the timetable for a specific day   |
| `/ชด <day> <period>`           | Set a makeup class for the day          |

## 🖼️ Timetable Image Processing

When a timetable image is sent to the bot using `/table_image`, it will automatically crop the image into class slots based on predefined coordinates and process them for use.

## ✅ Requirements

* Python 3.8+
* Discord Bot Token
* Discord server with appropriate permissions

## 📖 License

This project is licensed under the MIT License.

---
