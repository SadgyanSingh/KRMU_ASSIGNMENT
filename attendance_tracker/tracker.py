# STEP 1: Folder and File Structure Creation

# Name: Sadgyan Singh
# Date: 2025-11-09
# Assignment: Attendance Tracker Project

from datetime import datetime

print("Welcome to the Attendance Tracker System!")
print("This system records the attendance of the students.\n")

# STEP 2 & 3: Input + Validation (combined)
attendance = {}  # dictionary to store attendance

# --- total entries to record ---
while True:
    try:
        count = int(input("How many students' attendance record do you want to record? "))
        if count <= 0:
            print("Please enter a positive number.")
            continue
        break
    except ValueError:
        print("Please enter a valid integer (e.g., 5).")

# --- collect entries with validation ---
for i in range(count):
    # name validation
    while True:
        name = input(f"Student name {i+1}: ").strip()
        if name == "":
            print("Name cannot be empty. Please try again.")
            continue
        if name in attendance:
            print(f"Student '{name}' already exists. Please enter a different name.")
            continue
        break

    # time validation 
    while True:
        check_in = input(f"Enter the time for {name} (e.g., 09:15 AM): ").strip()
        if check_in == "":
            print("Time cannot be empty. Please try again.")
            continue
        # OPTIONAL strict check:
        try:
            datetime.strptime(check_in, "%I:%M %p")  # ex: 09:15 AM
        except ValueError:
            print("Invalid time format. Use e.g., 09:15 AM.")
            continue
        break

    attendance[name] = check_in

# STEP 4: Attendance Summary Display
colw = 22
print("\n" + "Student Name".ljust(colw) + "Check-in Time")
print("-" * (colw + 16))

for nm, t in attendance.items():
    print(nm.ljust(colw) + t)

print("-" * (colw + 16))
present_count = len(attendance)
print(f"Total Students Present: {present_count}")

# BONUS: Absent Students Count (safe)
while True:
    try:
        total = int(input("\nTotal class strength: "))
        if total < present_count:
            print(f"Total class strength cannot be less than present ({present_count}). Try again.")
            continue
        break
    except ValueError:
        print("Please enter a valid integer.")

absent = total - present_count
print(f"Total Present: {present_count}")
print(f"Total Absent: {absent}")

print("\nThank you for using the Attendance Tracker System!")
print("Goodbye!")

# BONUS Task 6: Save Attendance Report to File
save_choice = input("\nDo you want to save the attendance report to a file? (yes/no): ").strip().lower()
if save_choice in ("y", "yes"):
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M:%S")
    fname = "attendance_tracker/attendance_log.txt"

    lines = []
    lines.append("Attendance Report")
    lines.append(f"Generated at: {stamp}")
    lines.append("")
    lines.append("Student Name".ljust(colw) + "Check-in Time")
    lines.append("-" * (colw + 16))
    for nm, t in attendance.items():
        lines.append(nm.ljust(colw) + t)
    lines.append("-" * (colw + 16))
    lines.append(f"Total Students Present: {present_count}")
    lines.append(f"Total Students (Class Strength): {total}")
    lines.append(f"Total Absent: {absent}")
    lines.append("")

    try:
        with open(fname, "a", encoding="utf-8") as f:  # 'a' to append multiple runs
            f.write("\n".join(lines) + "\n")
        print(f"\n✅ Attendance report saved to '{fname}' (current folder).")
    except Exception as e:
        print(f"⚠️ File save failed: {e}")
else:
    print("Report not saved.")
