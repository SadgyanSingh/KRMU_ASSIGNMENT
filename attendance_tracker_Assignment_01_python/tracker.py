"""
attendance_system_full.py
Merged Attendance Tracker with:
 - interactive recording (date-aware)
 - query by date + export to student_attendance_record.txt
 - CSV & text archive
 - roster management (file-backed)
 - Generate full date-wise PDF with colored Present/Absent rows
Author: Sadgyan Singh (updated)
Date: 2025-11-13 (merged & enhanced)
"""

from datetime import datetime, date
from pathlib import Path
import csv
import re
from collections import defaultdict, OrderedDict

# PDF library (install via: pip install reportlab)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

ATT_DIR = Path("attendance_tracker")
ATT_DIR.mkdir(parents=True, exist_ok=True)

ARCHIVE = ATT_DIR / "attendance_archive.txt"
EXPORT_FILE = ATT_DIR / "student_attendance_record.txt"
CSV_LOG = ATT_DIR / "attendance_log.csv"
OUT_PDF = ATT_DIR / "full_date_list.pdf"
ROSTER_FILE = ATT_DIR / "roster.txt"   # one student name per line (optional)

# -------------------------
# Utility functions
# -------------------------
def parse_time(timestr: str):
    """Normalize time input. Accepts 'HH:MM', 'HH:MM AM/PM', 'HH:MMAM'."""
    timestr = timestr.strip()
    fmt_candidates = ["%I:%M %p", "%H:%M", "%I:%M%p"]
    for fmt in fmt_candidates:
        try:
            dt = datetime.strptime(timestr, fmt)
            return dt.strftime("%I:%M %p")  # normalized
        except ValueError:
            continue
    raise ValueError("Invalid time format. Use e.g., '09:15 AM' or '09:15' (24-hour).")

def input_positive_int(prompt: str):
    while True:
        try:
            n = int(input(prompt))
            if n <= 0:
                print("Please enter a positive integer.")
                continue
            return n
        except ValueError:
            print("Please enter a valid integer (e.g., 5).")

def ask_yes_no(prompt: str):
    return input(prompt).strip().lower() in ("y", "yes")

# -------------------------
# Archive / CSV helpers
# -------------------------
def write_archive_section(for_date: date, stamp: str, attendance: dict, total_strength: int, absent: int):
    """Append a human-readable section to ARCHIVE file (keeps all runs)."""
    colw = 28
    header = f"=== Attendance for: {for_date.isoformat()} ==="
    lines = []
    lines.append(header)
    lines.append(f"Generated at: {stamp}")
    lines.append("")
    lines.append("Student Name".ljust(colw) + "Check-in Time")
    lines.append("-" * (colw + 16))
    for nm in sorted(attendance.keys(), key=lambda s: s.lower()):
        lines.append(nm.ljust(colw) + attendance[nm])
    lines.append("-" * (colw + 16))
    lines.append(f"Total Students Present: {len(attendance)}")
    lines.append(f"Total Students (Class Strength): {total_strength}")
    lines.append(f"Total Absent: {absent}")
    lines.append("")  # blank line between sections

    with open(ARCHIVE, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def append_csv_rows(for_date: date, stamp: str, attendance: dict):
    file_exists = CSV_LOG.exists()
    with open(CSV_LOG, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["generated_at", "date", "student_name", "check_in_time"])
        for nm in sorted(attendance.keys(), key=lambda s: s.lower()):
            writer.writerow([stamp, for_date.isoformat(), nm, attendance[nm]])

# -------------------------
# Roster management
# -------------------------
def load_roster():
    """Load roster from ROSTER_FILE if exists, else return empty list."""
    if not ROSTER_FILE.exists():
        return []
    names = []
    for ln in ROSTER_FILE.read_text(encoding="utf-8").splitlines():
        n = ln.strip()
        if n:
            names.append(n.title())
    return sorted(list(dict.fromkeys(names)), key=lambda s: s.lower())

def save_roster(names):
    ROSTER_FILE.write_text("\n".join(names), encoding="utf-8")
    print(f"Roster saved to '{ROSTER_FILE}' ({len(names)} students).")

def interactive_roster_editor():
    print("\n--- Roster Manager ---")
    roster = load_roster()
    print(f"Current roster count: {len(roster)}")
    if roster:
        print(", ".join(roster[:10]) + ("..." if len(roster) > 10 else ""))
    while True:
        print("\nOptions: 1) Add student  2) Remove student  3) View all  4) Replace roster (bulk)  5) Save & Exit  6) Cancel")
        ch = input("Choose [1-6]: ").strip()
        if ch == "1":
            nm = input("Enter student name to ADD: ").strip().title()
            if nm == "":
                print("Empty name ignored.")
            elif nm in roster:
                print("Already exists.")
            else:
                roster.append(nm)
                roster.sort(key=lambda s: s.lower())
                print(f"Added: {nm}")
        elif ch == "2":
            nm = input("Enter student name to REMOVE: ").strip().title()
            if nm in roster:
                roster.remove(nm)
                print(f"Removed: {nm}")
            else:
                print("Name not found in roster.")
        elif ch == "3":
            if not roster:
                print("Roster empty.")
            else:
                print("Roster:")
                for idx, nm in enumerate(roster, start=1):
                    print(f"{idx}. {nm}")
        elif ch == "4":
            print("Enter names one per line. Empty line to stop.")
            new = []
            while True:
                ln = input().strip()
                if ln == "":
                    break
                new.append(ln.title())
            roster = sorted(list(dict.fromkeys(new)), key=lambda s: s.lower())
            print("Roster replaced.")
        elif ch == "5":
            save_roster(roster)
            break
        elif ch == "6":
            print("Roster edit canceled.")
            break
        else:
            print("Invalid option.")

# -------------------------
# Recording and querying flows
# -------------------------
def record_attendance_flow():
    print("\n--- Record Attendance ---")
    date_inp = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
    if date_inp == "":
        for_date = date.today()
    else:
        try:
            for_date = datetime.strptime(date_inp, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format. Using today's date.")
            for_date = date.today()

    attendance = {}
    count = input_positive_int("How many students' attendance records do you want to record? ")

    for i in range(count):
        while True:
            raw_name = input(f"Student name {i+1}: ").strip()
            if raw_name == "":
                print("Name cannot be empty. Please try again.")
                continue
            name = raw_name.title()
            if name.lower() in (n.lower() for n in attendance.keys()):
                print(f"Student '{name}' already exists. Please enter a different name.")
                continue
            break

        while True:
            check_in_raw = input(f"Enter the time for {name} (e.g., 09:15 AM or 09:15): ").strip()
            if check_in_raw == "":
                print("Time cannot be empty. Please try again.")
                continue
            try:
                check_in = parse_time(check_in_raw)
            except ValueError as e:
                print(e)
                continue
            break

        attendance[name] = check_in

    print("\nSummary for", for_date.isoformat())
    colw = 28
    print("\n" + "Student Name".ljust(colw) + "Check-in Time")
    print("-" * (colw + 16))
    for nm in sorted(attendance.keys(), key=lambda s: s.lower()):
        print(nm.ljust(colw) + attendance[nm])
    print("-" * (colw + 16))
    present_count = len(attendance)
    print(f"Total Students Present: {present_count}")

    # class strength
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

    # write to archive always
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        write_archive_section(for_date, stamp, attendance, total, absent)
        print(f"\n✅ Attendance appended to archive: '{ARCHIVE}'.")
    except Exception as e:
        print(f"⚠️ Could not write to archive: {e}")

    # append to CSV optionally
    if ask_yes_no("Also append rows to CSV archive? (yes/no): "):
        try:
            append_csv_rows(for_date, stamp, attendance)
            print(f"✅ CSV appended: '{CSV_LOG}'")
        except Exception as e:
            print(f"⚠️ CSV write failed: {e}")

def find_sections_by_date(target_date: date):
    """Read ARCHIVE and return a list of matching sections (text) for the target_date."""
    if not ARCHIVE.exists():
        return []
    content = ARCHIVE.read_text(encoding="utf-8")
    pattern = rf"=== Attendance for: {re.escape(target_date.isoformat())} ===\n(.*?)(?=\n=== Attendance for: |\Z)"
    matches = re.findall(pattern, content, flags=re.DOTALL)
    sections = [f"=== Attendance for: {target_date.isoformat()} ===\n" + m.strip() + "\n" for m in matches]
    return sections

def query_by_date_flow():
    print("\n--- Query Attendance by Date ---")
    date_inp = input("Enter date to query (YYYY-MM-DD) or 'today': ").strip()
    if date_inp.lower() == "today":
        target_date = date.today()
    else:
        try:
            target_date = datetime.strptime(date_inp, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            return

    sections = find_sections_by_date(target_date)
    if not sections:
        print(f"No records found for {target_date.isoformat()}.")
        return

    for idx, sec in enumerate(sections, start=1):
        print(f"\n--- Found record #{idx} for {target_date.isoformat()} ---")
        print(sec)

    if ask_yes_no("\nDo you want to export the above date's log into 'student_attendance_record.txt'? (this will OVERWRITE that file): "):
        combined = "\n".join(sections)
        try:
            with open(EXPORT_FILE, "w", encoding="utf-8") as f:
                f.write(combined)
            print(f"\n✅ Export successful: '{EXPORT_FILE}' written.")
        except Exception as e:
            print(f"⚠️ Export failed: {e}")
    else:
        print("Export skipped.")

# -------------------------
# PDF generation (colored)
# -------------------------
def read_from_csv(csv_path: Path):
    per_date = defaultdict(dict)
    if not csv_path.exists():
        return per_date
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            dt = (r.get("date") or "").strip()
            name = (r.get("student_name") or "").strip().title()
            time = (r.get("check_in_time") or "").strip()
            if not dt or not name:
                continue
            per_date[dt][name] = time
    return per_date

def read_from_archive(archive_path: Path):
    per_date = defaultdict(dict)
    if not archive_path.exists():
        return per_date
    txt = archive_path.read_text(encoding="utf-8")
    sections = re.split(r"=== Attendance for: (\d{4}-\d{2}-\d{2}) ===", txt)
    it = iter(sections)
    first = next(it, None)
    for date_chunk in it:
        date_str = date_chunk.strip()
        sec_text = next(it, "")
        for line in sec_text.splitlines():
            if line.strip() == "":
                continue
            if set(line.strip()) in (set("-"),):
                continue
            if line.strip().startswith("Generated at") or line.strip().startswith("Student Name") or line.strip().startswith("Total"):
                continue
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 2:
                name = parts[0].strip().title()
                time = parts[-1].strip()
                if re.search(r"\d{2}:\d{2}", time) or re.search(r"AM|PM", time, re.IGNORECASE) or time == "":
                    if name:
                        per_date[date_str][name] = time
    return per_date

def build_master(per_date_map):
    all_dates = sorted(per_date_map.keys())
    roster = set()
    for d in per_date_map:
        roster.update(per_date_map[d].keys())
    # if roster file exists, include its names as well
    file_roster = load_roster()
    roster.update(file_roster)
    roster_sorted = sorted(roster, key=lambda s: s.lower())
    return all_dates, roster_sorted, per_date_map

def make_colored_pdf(out_path: Path, ordered_dates, roster, per_date_map):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, rightMargin=24,leftMargin=24, topMargin=24,bottomMargin=24)
    story = []

    title = Paragraph("Full Date-wise Attendance List", styles["Title"])
    story.append(title)
    meta = Paragraph(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"])
    story.append(meta)
    story.append(Spacer(1, 12))

    if not ordered_dates or not roster:
        story.append(Paragraph("No attendance data found in CSV or archive.", styles["Normal"]))
        doc.build(story)
        print("PDF generated (but no data found).")
        return

    for idx, dt in enumerate(ordered_dates, start=1):
        header = Paragraph(f"{idx}. Date: {dt}", styles["Heading2"])
        story.append(header)
        story.append(Spacer(1, 6))

        table_data = [["Student Name", "Status", "Check-in Time"]]
        date_entries = per_date_map.get(dt, {})

        for name in roster:
            if name in date_entries:
                time = date_entries.get(name, "")
                status = "Present"
                chk = time if time else "-"
            else:
                status = "Absent"
                chk = "-"
            table_data.append([name, status, chk])

        # create table
        tbl = Table(table_data, colWidths=[220, 80, 100], repeatRows=1)
        tbl_style = TableStyle([
            ("GRID", (0,0), (-1,-1), 0.45, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#D3D3D3")),  # header
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN", (1,1), (1,-1), "CENTER"),
            ("ALIGN", (2,1), (2,-1), "CENTER"),
        ])

        # apply colored backgrounds row by row (Present = greenish, Absent = reddish)
        for row_idx in range(1, len(table_data)):
            status_cell = table_data[row_idx][1]
            if status_cell.lower() == "present":
                tbl_style.add("BACKGROUND", (0,row_idx), (-1,row_idx), colors.HexColor("#e6f4ea"))  # light green
            else:
                tbl_style.add("BACKGROUND", (0,row_idx), (-1,row_idx), colors.HexColor("#fdecea"))  # light red

        tbl.setStyle(tbl_style)
        story.append(tbl)
        story.append(Spacer(1, 12))

        if idx % 3 == 0:
            story.append(PageBreak())

    doc.build(story)
    print(f"✅ Colored PDF created: {out_path}")

def generate_full_pdf_flow():
    print("\n--- Generate Full Date-wise PDF (colored) ---")
    per_date = read_from_csv(CSV_LOG)
    if not per_date:
        per_date = read_from_archive(ARCHIVE)
    if not per_date:
        print("No attendance data found in CSV or archive. Nothing to generate.")
        return
    ordered_dates, roster, data = build_master(per_date)
    make_colored_pdf(OUT_PDF, ordered_dates, roster, data)

# -------------------------
# Main menu
# -------------------------
def main_menu():
    print("Welcome to the Attendance Tracker System (Merged - Full Features)!")
    while True:
        print("\nSelect an option:")
        print("1) Record attendance (new)")
        print("2) Query attendance by date (and export to student_attendance_record.txt)")
        print("3) Manage roster (load/edit/save)")
        print("4) Generate Full Date-wise PDF (colored) [full_date_list.pdf]")
        print("5) Exit")
        choice = input("Enter 1 / 2 / 3 / 4 / 5: ").strip()
        if choice == "1":
            record_attendance_flow()
        elif choice == "2":
            query_by_date_flow()
        elif choice == "3":
            interactive_roster_editor()
        elif choice == "4":
            generate_full_pdf_flow()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please choose 1-5.")

if __name__ == "__main__":
    main_menu()
