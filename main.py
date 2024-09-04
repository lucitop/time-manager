import sys
import os
import pygame
import time
import random
import threading
import json
from datetime import datetime, timedelta

pygame.mixer.init()

PREDEFINED_SOUNDS = {
    '1': os.path.join('sounds', 'beep.wav'),
    '2': os.path.join('sounds', '8bit.mp3'),
    '3': os.path.join('sounds', 'cozy.mp3'),
    '4': os.path.join('sounds', 'scifi.wav')
}

DEFAULT_TIMER_SOUND = PREDEFINED_SOUNDS['1']
DEFAULT_ALARM_SOUND = PREDEFINED_SOUNDS['1']

stop_alarm_flag = False

def play_sound_loop(sound_file):
    global stop_alarm_flag
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.play(-1)
    while not stop_alarm_flag:
        time.sleep(0.1)
    pygame.mixer.music.stop()

def stop_alarm_sound():
    global stop_alarm_flag
    input("Press Enter to stop the sound...")
    stop_alarm_flag = True

class TimerManager:
    def __init__(self, timer_sound=DEFAULT_TIMER_SOUND, alarm_sound=DEFAULT_ALARM_SOUND, template_file="templates.json"):
        self.timers = []
        self.alarms = []
        self.templates = []
        self.timer_sound = timer_sound
        self.alarm_sound = alarm_sound
        self.template_file = template_file
        self.lock = threading.Lock()
        self.stopwatch_running = False
        self.stopwatch_start_time = None
        self.load_templates()

    def monitor_timers_and_alarms(self):
        global stop_alarm_flag
        while True:
            now = datetime.now()
            with self.lock:
                for i, (name, timer) in enumerate(self.timers, start=1):
                    time_left = timer - now
                    if time_left.total_seconds() <= 0:
                        stop_alarm_flag = False
                        self.timers.pop(i - 1)
                        threading.Thread(target=play_sound_loop, args=(self.timer_sound,), daemon=True).start()
                        self.notify_user(name)
                        stop_alarm_sound()

                for i, alarm in enumerate(self.alarms, start=1):
                    time_left = alarm - now
                    if time_left.total_seconds() <= 0:
                        stop_alarm_flag = False
                        self.alarms.pop(i - 1)
                        threading.Thread(target=play_sound_loop, args=(self.alarm_sound,), daemon=True).start()
                        self.notify_user(f"Alarm {i}")
                        stop_alarm_sound()
            time.sleep(1)

    
    def notify_user(self, alert_type):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n\n\n\n\n\n{' ' * 10}{alert_type.upper()} TIME IS UP!")
        print(f"{' ' * 10}Press Enter to return to the main menu...")
        input()
        os.system('cls' if os.name == 'nt' else 'clear')

    def save_templates(self):
        with open(self.template_file, 'w') as f:
            json.dump(self.templates, f)
        print("Templates saved.")
    
    def load_templates(self):
        try:
            with open(self.template_file, 'r') as f:
                self.templates = json.load(f)
            print("Templates loaded.")
        except FileNotFoundError:
            print("No templates file found, starting fresh.")
        except json.JSONDecodeError:
            print("Error loading templates, starting fresh.")
            self.templates = []

    def add_timer(self, base_minutes, random_interval=None, name="Timer"):
        if random_interval is not None:
            random_addition = random.uniform(0, random_interval)
        else:
            random_addition = 0
        total_minutes = base_minutes + random_addition
        total_seconds = int(total_minutes * 60)
        minutes, seconds = divmod(total_seconds, 60)
        end_time = datetime.now() + timedelta(minutes=total_minutes)
        with self.lock:
            self.timers.append((name, end_time))
        print(f"{name} set for {minutes} minutes and {seconds} seconds ({base_minutes} base + {random_addition:.2f} random).")

    def add_alarm(self, alarm_time_str):
        try:
            alarm_time = datetime.strptime(alarm_time_str, "%H:%M")
            now = datetime.now()
            today_alarm = now.replace(hour=alarm_time.hour, minute=alarm_time.minute, second=0, microsecond=0)
            if today_alarm < now:
                today_alarm += timedelta(days=1)
            with self.lock:
                self.alarms.append(today_alarm)
            print(f"Alarm set for {today_alarm.strftime('%H:%M')}.")
        except ValueError:
            print("Invalid time format. Please use HH:MM format.")

    def add_template(self, name, base_minutes, random_interval):
        if len(self.templates) >= 5:
            print("You cannot save more than 5 templates.")
            return
        self.templates.append((name, base_minutes, random_interval))
        self.save_templates()
        print(f"Template '{name}' saved: Base minutes: {base_minutes}, Random interval: {random_interval}")

    def view_templates(self):
        if not self.templates:
            print("No templates available.")
        else:
            for i, (name, base, interval) in enumerate(self.templates, start=1):
                print(f"{i}. {name}: Base: {base} minutes, Random interval: {interval} minutes")

    def run_template(self, index):
        if 0 <= index < len(self.templates):
            name, base_minutes, random_interval = self.templates[index]
            print(f"Running template '{name}'")
            self.add_timer(base_minutes, random_interval, name)
        else:
            print("Invalid template index.")

    def run_all_templates(self):
        if not self.templates:
            print("No templates available to run.")
            return
        print("Running all templates...")
        for name, base_minutes, random_interval in self.templates:
            print(f"Running template '{name}' with base minutes {base_minutes} and random interval {random_interval}")
            self.add_timer(base_minutes, random_interval, name)

    def remove_timer(self):
        if not self.timers:
            print("No timers to remove.")
            return
        print("Active timers:")
        for i, timer in enumerate(self.timers, start=1):
            time_left = timer - datetime.now()
            print(f"{i}. Timer {i}: {str(time_left)} left")
        try:
            index = int(input("Enter the timer number to remove: ")) - 1
            if 0 <= index < len(self.timers):
                del self.timers[index]
                print(f"Timer {index + 1} removed.")
            else:
                print("Invalid timer number.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    def remove_alarm(self):
        if not self.alarms:
            print("No alarms to remove.")
            return
        print("Active alarms:")
        for i, alarm in enumerate(self.alarms, start=1):
            time_left = alarm - datetime.now()
            print(f"{i}. Alarm {i}: {str(time_left)} left")
        try:
            index = int(input("Enter the alarm number to remove: ")) - 1
            if 0 <= index < len(self.alarms):
                del self.alarms[index]
                print(f"Alarm {index + 1} removed.")
            else:
                print("Invalid alarm number.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    def modify_alarm(self):
        if not self.alarms:
            print("No alarms to modify.")
            return
        print("Active alarms:")
        for i, alarm in enumerate(self.alarms, start=1):
            print(f"{i}. Alarm set for {alarm.strftime('%H:%M')}")
        try:
            index = int(input("Enter the alarm number to modify: ")) - 1
            if 0 <= index < len(self.alarms):
                new_alarm_time_str = input("Enter the new alarm time (HH:MM format): ")
                self.alarms[index] = datetime.strptime(new_alarm_time_str, "%H:%M").replace(year=datetime.now().year,
                                                                                           month=datetime.now().month,
                                                                                           day=datetime.now().day)
                print(f"Alarm {index + 1} modified to {self.alarms[index].strftime('%H:%M')}.")
            else:
                print("Invalid alarm number.")
        except ValueError:
            print("Invalid input. Please use the correct time format (HH:MM).")

    def modify_timer(self):
        if not self.timers:
            print("No timers to modify.")
            return
        print("Active timers:")
        for i, timer in enumerate(self.timers, start=1):
            time_left = timer - datetime.now()
            print(f"{i}. Timer {i}: {str(time_left)} left")
        try:
            index = int(input("Enter the timer number to modify: ")) - 1
            if 0 <= index < len(self.timers):
                base_minutes = float(input("Enter new base minutes: "))
                random_interval = input("Enter new random interval in minutes (or nothing to skip): ")
                random_interval = float(random_interval) if random_interval else None
                self.add_timer(base_minutes, random_interval)
                del self.timers[index]
                print(f"Timer {index + 1} modified.")
            else:
                print("Invalid timer number.")
        except ValueError:
            print("Invalid input. Please enter valid numbers.")

    def stop_all_timers(self):
        with self.lock:
            if self.timers:
                self.timers.clear()
                print("All timers have been stopped.")
            else:
                print("No timers to stop.")

    def add_stopwatch(self):
        if self.stopwatch_running:
            print("Stopwatch already running.")
        else:
            self.stopwatch_start_time = datetime.now()
            self.stopwatch_running = True
            print("Stopwatch started.")

    def stop_stopwatch(self):
        if not self.stopwatch_running:
            print("No stopwatch running.")
        else:
            elapsed_time = datetime.now() - self.stopwatch_start_time
            print(f"Stopwatch stopped. Time elapsed: {str(elapsed_time)}")
            self.stopwatch_running = False
            self.stopwatch_start_time = None

    def change_timer_sound(self, timer_sound):
        self.timer_sound = timer_sound
        print(f"Timer sound changed to: {timer_sound}")

    def change_alarm_sound(self, alarm_sound):
        self.alarm_sound = alarm_sound
        print(f"Alarm sound changed to: {alarm_sound}")

    def check_time_left(self):
        now = datetime.now()
        global stop_alarm_flag
        with self.lock:
            if not self.timers and not self.alarms:
                print("No active timers or alarms.")
            for i, (name, timer) in enumerate(self.timers, start=1):
                time_left = timer - now
                if time_left.total_seconds() > 0:
                    minutes, seconds = divmod(int(time_left.total_seconds()), 60)
                    print(f"{name}: {minutes} minutes and {seconds} seconds left.")
                else:
                    print(f"{name}: Time's up!")
                    stop_alarm_flag = False
                    threading.Thread(target=play_sound_loop, args=(self.timer_sound,), daemon=True).start()
                    stop_alarm_sound()

            for i, alarm in enumerate(self.alarms, start=1):
                time_left = alarm - now
                if time_left.total_seconds() > 0:
                    minutes, seconds = divmod(int(time_left.total_seconds()), 60)
                    print(f"Alarm {i}: {minutes} minutes and {seconds} seconds left.")
                else:
                    print(f"Alarm {i}: Time's up!")
                    stop_alarm_flag = False
                    threading.Thread(target=play_sound_loop, args=(self.alarm_sound,), daemon=True).start()
                    stop_alarm_sound()

def template_menu(timer_manager):
    while True:
        print("\n--- Template Menu ---")
        print("1. View Templates")
        print("2. Add Template")
        print("3. Run Template")
        print("4. Modify Template")
        print("5. Delete Template")
        print("6. Back to Main Menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            timer_manager.view_templates()
        elif choice == '2':
            try:
                name = input("Enter a name for the template: ")
                base_minutes = float(input("Enter base minutes for the template: "))
                random_interval = float(input("Enter random interval in minutes for the template: "))
                timer_manager.add_template(name, base_minutes, random_interval)
            except ValueError:
                print("Invalid input. Please enter valid numbers.")
        elif choice == '3':
            timer_manager.view_templates()
            try:
                index = int(input("Enter the template number to run: ")) - 1
                timer_manager.run_template(index)
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        elif choice == '4':
            timer_manager.view_templates()
            try:
                index = int(input("Enter the template number to modify: ")) - 1
                name = input("Enter new name for the template: ")
                base_minutes = float(input("Enter new base minutes: "))
                random_interval = float(input("Enter new random interval in minutes: "))
                timer_manager.modify_template(index, name, base_minutes, random_interval)
            except ValueError:
                print("Invalid input. Please enter valid numbers.")
        elif choice == '5':
            timer_manager.view_templates()
            try:
                index = int(input("Enter the template number to delete: ")) - 1
                timer_manager.delete_template(index)
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        elif choice == '6':
            break
        else:
            print("Invalid option. Please try again.")

def main_menu(timer_manager):
    while True:
        print("\n--- Main Menu ---")
        print("1. Set a timer")
        print("2. Set an alarm")
        print("3. Start a stopwatch")
        print("4. Template Menu")
        print("5. Run all timer templates")
        print("6. Stop all timers")
        print("7. Stop the running stopwatch")
        print("8. View active timers and alarms")
        print("9. Modify/Remove Alarms and Timers")
        print("10. Settings")
        print("11. Quit")

        choice = input("Enter your choice: ")

        if choice == '1':
            try:
                base_minutes = float(input("Enter the base minutes for the timer (e.g., 1.5 for 1 minute 30 seconds): "))
                name = input("Enter a name for the timer: ")
                random_interval = input("Enter the random interval in minutes to add (or nothing to skip): ")
                random_interval = float(random_interval) if random_interval else None
                timer_manager.add_timer(base_minutes, random_interval, name)
            except ValueError:
                print("Invalid input. Please enter valid numbers.")
        elif choice == '2':
            alarm_time_str = input("Enter the alarm time (HH:MM format): ")
            timer_manager.add_alarm(alarm_time_str)
        elif choice == '3':
            timer_manager.add_stopwatch()
        elif choice == '4':
            template_menu(timer_manager)
        elif choice == '5':
            timer_manager.run_all_templates()
        elif choice == '6':
            timer_manager.stop_all_timers()
        elif choice == '7':
            if timer_manager.stopwatch_running:
                timer_manager.stop_stopwatch()
            else:
                print("No stopwatch is running.")
        elif choice == '8':
            timer_manager.check_time_left()
            input("Press Enter to go back to the main menu...")
        elif choice == '9':
            modify_or_remove_menu(timer_manager)
        elif choice == '10':
            settings_menu(timer_manager)
        elif choice == '11':
            print("Exiting...")
            break
        else:
            print("Invalid option. Please try again.")

def modify_or_remove_menu(timer_manager):
    while True:
        print("\n--- Modify/Remove Alarms and Timers ---")
        print("1. Modify an alarm")
        print("2. Remove an alarm")
        print("3. Modify a timer")
        print("4. Remove a timer")
        print("5. Back to main menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            timer_manager.modify_alarm()
        elif choice == '2':
            timer_manager.remove_alarm()
        elif choice == '3':
            timer_manager.modify_timer()
        elif choice == '4':
            timer_manager.remove_timer()
        elif choice == '5':
            break
        else:
            print("Invalid option. Please try again.")

def settings_menu(timer_manager):
    while True:
        print("\n--- Settings Menu ---")
        print("1. Change timer sound")
        print("2. Change alarm sound")
        print("3. Back to main menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            timer_sound = choose_sound("Select a sound for timers:")
            timer_manager.change_timer_sound(timer_sound)
        elif choice == '2':
            alarm_sound = choose_sound("Select a sound for alarms:")
            timer_manager.change_alarm_sound(alarm_sound)
        elif choice == '3':
            break
        else:
            print("Invalid option. Please try again.")

def choose_sound(prompt):
    print(prompt)
    for key, sound in PREDEFINED_SOUNDS.items():
        print(f"{key}: {sound}")
    choice = input("Select a sound by entering the number: ")
    if choice not in PREDEFINED_SOUNDS:
        print("Invalid option. Please try again.")
        return DEFAULT_TIMER_SOUND
    return PREDEFINED_SOUNDS.get(choice, DEFAULT_TIMER_SOUND)

def main():
    timer_manager = TimerManager()
    threading.Thread(target=timer_manager.monitor_timers_and_alarms, daemon=True).start()
    main_menu(timer_manager)

if __name__ == "__main__":
    main()
