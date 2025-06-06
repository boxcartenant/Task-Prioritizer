import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime, timedelta
import uuid
from functools import partial
import calendar
from tkinter.font import Font
import math

window_geometry = "1250x760"
default_main_sashpos = 700
impact_high_dollars = 100000



class Task:
    def __init__(self, short_desc, long_desc, safety, impact, hype, due_date, 
                 area="", entity="", maintenance_plan="", procedure_doc="", 
                 requestor="", project="", is_win=False, id=None, prerequisites=None,
                 contingents=None, delegate=None, status=None, completion_date=None,
                 snooze_until=None, impact_is_percentage=False,
                 recurrence_type="none", recurrence_settings=None, first_active_date=None,
                 delegate_reminder_days=0):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.short_desc = short_desc
        self.long_desc = long_desc
        self.safety = safety
        self.impact = impact
        self.hype = hype
        self.due_date = due_date
        self.area = area
        self.entity = entity
        self.maintenance_plan = maintenance_plan
        self.procedure_doc = procedure_doc
        self.requestor = requestor
        self.project = project
        self.is_win = is_win
        if prerequisites is None:
            self.prerequisites = []
        else:
            self.prerequisites = prerequisites
        if contingents is None:
            self.contingents = []
        else:
            self.contingents = contingents
        self.delegate = delegate
        if status is None:
            self.status = "active"
        else:
            self.status = status
        self.completion_date = completion_date
        self.snooze_until = snooze_until
        self.impact_is_percentage = impact_is_percentage
        self.recurrence_type = recurrence_type
        if recurrence_settings is None:
            self.recurrence_settings = {}
        else:
            self.recurrence_settings = recurrence_settings
        self.first_active_date = first_active_date
        self.delegate_reminder_days = delegate_reminder_days

    def calculate_priority(self, tasks):
        if self.status != "active":
            return -1
        for prereq_id in self.prerequisites:
            prereq = next((t for t in tasks if t.id == prereq_id), None)
            if prereq and prereq.status != "completed":
                return -1
        urgency = math.ceil((self.due_date - datetime.now()).total_seconds()/(24*60*60))
        impact_value = self.impact
        if not self.impact_is_percentage:
            impact_value = impact_value * 100/impact_high_dollars
        priority = (0.3 * self.safety / 100 +
                    0.2 * self.hype / 100 +
                    0.1 * impact_value/ 100 +
                    0.4 * ((urgency/(0-60))+1)) *100
        if self.is_win:
            priority += 100
        for cont_id in self.contingents:
            cont = next((t for t in tasks if t.id == cont_id), None)
            if cont and cont.status == "active":
                cont_priority = cont.calculate_priority(tasks)
                if cont_priority > priority:
                    priority = cont_priority
        return priority

    def _get_reminder_timing(self):
        """
        Helper method to calculate delegate reminder timing.
        Returns a tuple: (is_due_today: bool, days_to_next: int).
        is_due_today is True if a reminder is due today.
        days_to_next is the number of days until the next reminder (0 if due today).
        """
        if not self.delegate or self.delegate_reminder_days == 0:
            return False, None
        current_time = datetime.now()
        days_since_start = (current_time - (self.first_active_date or self.due_date)).days
        if days_since_start < 0:  # Handle future start dates
            return False, -days_since_start
        is_due_today = days_since_start % self.delegate_reminder_days == 0
        days_to_next = self.delegate_reminder_days - (days_since_start % self.delegate_reminder_days)
        return is_due_today, days_to_next

    def get_time_to_delegate_reminder(self):
        if self.delegate and self.delegate_reminder_days != 0 and self.status == "active" and not self.is_snoozed():
            is_due_today, days_to_next = self._get_reminder_timing()
            if days_to_next is not None:
                return f"{days_to_next} days"
        return "N/A"

    def needs_reminder(self, tasks):
        if self.delegate and self.status == "active" and not self.is_snoozed():
            priority = self.calculate_priority(tasks)
            if priority < 0:
                return False
            is_due_today, _ = self._get_reminder_timing()
            return is_due_today
        return False

    def is_snoozed(self):
        return self.snooze_until and self.snooze_until > datetime.now()

    def get_state(self, tasks):
        if self.status == "completed":
            return "Complete"
        if self.status == "abandoned":
            return "Abandoned"
        if self.is_snoozed():
            return "Snoozed"
        if self.calculate_priority(tasks) < 0 and self.status == "active":
            return "Contingent"
        return "Actionable"

    def get_snooze_duration(self):
        if self.is_snoozed():
            delta = self.snooze_until - datetime.now()
            return f"{delta.days + 1} days"
        return "N/A"

    def get_next_revival_time(self, reference_time=None):
        if self.recurrence_type == "none":
            return None
        if reference_time is None:
            reference_time = self.first_active_date if self.first_active_date else self.due_date
        if not reference_time:
            return None

        if self.recurrence_type == "weekly":
            days_of_week = self.recurrence_settings.get("days", [])
            if not days_of_week:
                return None
            day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
            target_days = [day_map[day] for day in days_of_week]
            current_weekday = reference_time.weekday()
            days_ahead = []
            for target in target_days:
                delta = (target - current_weekday) % 7
                if delta == 0:
                    delta = 7
                days_ahead.append(delta)
                
            min_days = min(days_ahead)
            print("days ahead map:",days_ahead)
            print("next recurrence mapped to...", reference_time + timedelta(days=min_days))
            return reference_time + timedelta(days=min_days)

        elif self.recurrence_type == "monthly":
            target_day = self.recurrence_settings.get("day", 1)
            next_month = reference_time.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            last_day_of_month = calendar.monthrange(next_month.year, next_month.month)[1]
            actual_day = min(target_day, last_day_of_month)
            return next_month.replace(day=actual_day)

        elif self.recurrence_type == "annually":
            target_month = self.recurrence_settings.get("month", 1)
            target_day = self.recurrence_settings.get("day", 1)
            next_year = reference_time.replace(year=reference_time.year + 1)
            last_day_of_month = calendar.monthrange(next_year.year, target_month)[1]
            actual_day = min(target_day, last_day_of_month)
            return next_year.replace(month=target_month, day=actual_day)

        elif self.recurrence_type == "every_n":
            n = self.recurrence_settings.get("n", 1)
            unit = self.recurrence_settings.get("unit", "days")
            target = self.recurrence_settings.get("target")
            if unit == "days":
                return reference_time + timedelta(days=n)
            elif unit == "weeks":
                day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
                target_day = day_map[target]
                next_date = reference_time + timedelta(weeks=n)
                days_ahead = (target_day - next_date.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return next_date + timedelta(days=days_ahead)
            elif unit == "months":
                next_date = reference_time + timedelta(days=32 * n)
                next_date = next_date.replace(day=1)
                last_day_of_month = calendar.monthrange(next_date.year, next_date.month)[1]
                actual_day = min(target, last_day_of_month)
                return next_date.replace(day=actual_day)
            elif unit == "years":
                next_date = reference_time.replace(year=reference_time.year + n)
                last_day_of_month = calendar.monthrange(next_date.year, target)[1]
                actual_day = min(self.recurrence_settings.get("day", 1), last_day_of_month)
                return next_date.replace(month=target, day=actual_day)
        return None

class Person:
    def __init__(self, name, job_title, department, area="", is_contractor=False, id=None):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.name = name
        self.job_title = job_title
        self.department = department
        self.area = area
        self.is_contractor = is_contractor

class TaskManager:
    def __init__(self):
        global window_geometry, default_main_sashpos
        self.tasks = []
        self.people = []
        self.current_filter = "actionable"
        self.sort_column = "Priority"
        self.sort_direction = "desc"
        self.current_task_id = None
        self.load_data()
        self.root = tk.Tk()
        self.root.title("Task Prioritizer")
        self.root.geometry(window_geometry)
        self.search_query = tk.StringVar()
        self.setup_gui()
        self.root.after(100, lambda: self.main_frame.sashpos(0, default_main_sashpos))

    def load_data(self):
        try:
            with open("task_data.json", "r") as f:
                data = json.load(f)
                self.people = [Person(**p) for p in data.get("people", [])]
                person_map = {p.id: p for p in self.people}
                for task_data in data.get("tasks", []):
                    if isinstance(task_data["due_date"], str):
                        task_data["due_date"] = datetime.fromisoformat(task_data["due_date"])
                    if task_data.get("completion_date") and isinstance(task_data["completion_date"], str):
                        task_data["completion_date"] = datetime.fromisoformat(task_data["completion_date"])
                    if task_data.get("snooze_until") and isinstance(task_data["snooze_until"], str):
                        task_data["snooze_until"] = datetime.fromisoformat(task_data["snooze_until"])
                    if task_data.get("first_active_date") and isinstance(task_data["first_active_date"], str):
                        task_data["first_active_date"] = datetime.fromisoformat(task_data["first_active_date"])
                    task_data.pop("last_revival_time", None)
                    task_data["safety"] = task_data.get("safety", 50)
                    task_data["hype"] = task_data.get("hype", 50)
                    task_data["impact"] = task_data.get("impact", 0)
                    task_data["impact_is_percentage"] = task_data.get("impact_is_percentage", True)
                    task_data["delegate_reminder_days"] = task_data.get("delegate_reminder_days", 0)
                    delegate_id = task_data.get("delegate")
                    if delegate_id:
                        task_data["delegate"] = person_map.get(delegate_id)
                    else:
                        task_data["delegate"] = None
                    self.tasks.append(Task(**task_data))
        except FileNotFoundError:
            pass

    def save_data(self):
        tasks_data = []
        for t in self.tasks:
            task_dict = vars(t).copy()
            if task_dict["delegate"]:
                task_dict["delegate"] = task_dict["delegate"].id
            tasks_data.append(task_dict)
        data = {
            "tasks": tasks_data,
            "people": [vars(p) for p in self.people]
        }
        with open("task_data.json", "w") as f:
            json.dump(data, f, default=str)

    def setup_gui(self):
        global default_main_sashpos
        self.main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.list_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.list_frame, weight=1)

        search_frame = ttk.Frame(self.list_frame)
        search_frame.pack(fill=tk.X, side=tk.TOP)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_query)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_query.trace("w", lambda name, index, mode, sv=self.search_query: self.update_task_list())

        filter_frame = ttk.Frame(self.list_frame)
        filter_frame.pack(fill=tk.X, side=tk.TOP)
        ttk.Button(filter_frame, text="Actionable Only", command=partial(self.set_filter, "actionable")).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="Snoozed/Delegated", command=partial(self.set_filter, "snoozed")).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="Contingent", command=partial(self.set_filter, "contingent")).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="Completed/Abandoned", command=partial(self.set_filter, "completed_abandoned")).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="All Tasks", command=partial(self.set_filter, "all")).pack(side=tk.LEFT)

        self.tree_frame = ttk.Frame(self.list_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        self.all_columns = ("Short Desc", "Priority", "Due Date", "Completed/Abandoned Date", "State", "Snooze/Reminder", "W.I.N.", "Delegated", "Recurring")
        self.tree = ttk.Treeview(self.tree_frame, columns=self.all_columns, show="headings")
        self.tree.heading("Short Desc", text="Description")
        self.tree.heading("Priority", text="Priority")
        self.tree.heading("Due Date", text="Due Date")
        self.tree.heading("Completed/Abandoned Date", text="Completed/Abandoned Date")
        self.tree.heading("State", text="State")
        self.tree.heading("Snooze/Reminder", text="Snooze/Reminder")
        self.tree.heading("W.I.N.", text="W.I.N.")
        self.tree.heading("Delegated", text="Delegated")
        self.tree.heading("Recurring", text="Recurring")
        self.tree.column("Short Desc", width=250)
        self.tree.column("Priority", width=80)
        self.tree.column("Due Date", width=50)
        self.tree.column("Completed/Abandoned Date", width=150)
        self.tree.column("State", width=100)
        self.tree.column("Snooze/Reminder", width=100)
        self.tree.column("W.I.N.", width=50)
        self.tree.column("Delegated", width=70)
        self.tree.column("Recurring", width=30)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.setup_scrollbar()

        for col in self.all_columns:
            self.tree.heading(col, command=lambda c=col: self.sort_by_column(c))

        button_frame = ttk.Frame(self.list_frame)
        button_frame.pack(fill=tk.X, side=tk.TOP)
        ttk.Button(button_frame, text="Add Task", command=self.add_task).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Manage People", command=self.manage_people).pack(side=tk.LEFT)

        detail_container = ttk.Frame(self.main_frame)
        self.main_frame.add(detail_container, weight=2)
        canvas = tk.Canvas(detail_container, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(detail_container, orient="vertical", command=canvas.yview)
        self.detail_frame = ttk.Frame(canvas)
        self.detail_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.detail_frame, anchor="nw", width=canvas.winfo_width())
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.create_window((0, 0), window=self.detail_frame, anchor="nw"), width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.detail_widgets = {}
        self.update_task_list()

    def setup_scrollbar(self):
        if hasattr(self, 'y_scrollbar'):
            self.y_scrollbar.pack_forget()
        self.y_scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.y_scrollbar.set)
        self.y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def sort_by_column(self, column):
        if self.sort_column == column:
            self.sort_direction = "desc" if self.sort_direction == "asc" else "desc"
        else:
            self.sort_column = column
            self.sort_direction = "desc"
        self.update_task_list()

    def set_filter(self, filter_type):
        self.current_filter = filter_type
        self.update_task_list()

    def update_task_list(self):
        current_time = datetime.now()
        #if the task is delegated, and it's time for a reminder, create a reminder task.
        #   Otherwise, update the due date for the existing reminder task
        for task in [t for t in self.tasks if t.delegate and t.status == "active"]:
            if task.needs_reminder(self.tasks):
                reminder_task = next((t for t in self.tasks if t.contingents and t.contingents[0] == task.id and "[remind delegate]" in t.short_desc), None)
                if not reminder_task:
                    due_date = (current_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    reminder_task = Task(
                        short_desc=f"[remind delegate] {task.short_desc}",
                        long_desc="Delegated to "+task.delegate.name+": "+task.long_desc,
                        safety=task.safety,
                        impact=task.impact,
                        hype=task.hype,
                        due_date=due_date,
                        area=task.area,
                        entity=task.entity,
                        maintenance_plan=task.maintenance_plan,
                        procedure_doc=task.procedure_doc,
                        requestor=task.requestor,
                        project=task.project,
                        is_win=task.is_win,
                        prerequisites=None,
                        contingents=[task.id],
                        delegate=None,
                        status="active",
                        impact_is_percentage=task.impact_is_percentage,
                        recurrence_type="none",
                        first_active_date=current_time
                    )
                    self.tasks.append(reminder_task)
                    print("creating reminder task...",reminder_task.short_desc)
                else:
                    next_midnight = (current_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    if reminder_task.due_date != next_midnight:
                        reminder_task.due_date = next_midnight
                self.save_data()

        for item in self.tree.get_children():
            self.tree.delete(item)

        ## Set up the headers based on the current filter mode
        search_text = self.search_query.get().lower().strip()
        if self.current_filter == "actionable":
            tasks = [t for t in self.tasks if t.status == "active" and t.calculate_priority(self.tasks) >= 0 and not t.is_snoozed() and not t.delegate]
            active_columns = ("Short Desc", "Priority", "Due Date", "Recurring")
        elif self.current_filter == "all":
            tasks = self.tasks
            active_columns = ("Short Desc", "Priority", "Due Date", "State")
        elif self.current_filter == "snoozed":
            tasks = [t for t in self.tasks if t.is_snoozed() or (t.status == "active" and t.delegate)]
            active_columns = ("Short Desc", "Priority", "Due Date", "Snooze/Reminder", "Delegated", "Recurring")
        elif self.current_filter == "contingent":
            tasks = [t for t in self.tasks if t.calculate_priority(self.tasks) < 0 and t.status == "active"]
            active_columns = ("Short Desc", "Due Date", "State")
        elif self.current_filter == "completed_abandoned":
            tasks = [t for t in self.tasks if t.status in ["completed", "abandoned"]]
            active_columns = ("Short Desc", "Due Date", "Completed/Abandoned Date", "State", "W.I.N.")

        if search_text:
            tasks = [t for t in tasks if any(search_text in str(getattr(t, field)).lower() 
                                           for field in ["short_desc", "long_desc", "safety", "impact", "hype", 
                                                         "area", "entity", "maintenance_plan", "procedure_doc", 
                                                         "requestor", "project", "is_win", 
                                                         "due_date"] 
                                           if getattr(t, field) is not None)]

        # Configure only the active columns
        for col in self.all_columns:
            if col in active_columns:
                self.tree.heading(col, text=col)
                if col == "Short Desc":
                    width = 400
                elif col == "Recurring":
                    width = 70
                elif col == "Snooze/Reminder":
                    width = 100
                elif col == "Completed/Abandoned Date":
                    width = 150
                elif col in ["Priority", "State", "Due Date"]:
                    width = 80
                elif col in ["Delegated", "W.I.N."]:
                    width = 50
                else:
                    width = 200
                self.tree.column(col, width=width, stretch=False)
            else:
                self.tree.column(col, width=0, stretch=False)  # Hide unused columns

        if self.sort_column == "Short Desc":
            tasks.sort(key=lambda t: t.short_desc.lower() if t.short_desc else "", reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "Priority":
            tasks.sort(key=lambda t: t.calculate_priority(self.tasks) if t.status == "active" else -1, reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "Due Date":
            tasks.sort(key=lambda t: t.due_date, reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "Completed/Abandoned Date":
            tasks.sort(key=lambda t: t.completion_date if t.completion_date else datetime.min, reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "State":
            tasks.sort(key=lambda t: t.get_state(self.tasks), reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "Snooze/Reminder":
            tasks.sort(key=lambda t: int(t.get_snooze_duration().split()[0]) if t.is_snoozed() else -1, reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "W.I.N.":
            tasks.sort(key=lambda t: t.is_win, reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "Delegated":
            tasks.sort(key=lambda t: bool(t.delegate), reverse=(self.sort_direction == "desc"))
        

        #("Short Desc", "Priority", "Due Date", "Completed/Abandoned Date", "State", "Snooze/Reminder", "W.I.N.", "Delegated", "Recurring")
        for task in tasks:
            priority = f"{task.calculate_priority(self.tasks):.2f}" if task.calculate_priority(self.tasks) >= 0 else "N/A"
            due_date = task.due_date.strftime("%Y-%m-%d")
            if self.current_filter == "all":
                #print(task.get_state(self.tasks))
                values = (task.short_desc, priority, due_date,"", task.get_state(self.tasks), "", "", "")
            elif self.current_filter == "snoozed":
                delegated = "✓" if task.delegate else ""
                snooze_time = task.get_time_to_delegate_reminder() if task.delegate else task.get_snooze_duration()
                values = (task.short_desc, priority, due_date, "", "", snooze_time, "", delegated)
            elif self.current_filter == "completed_abandoned":
                completed_date = task.completion_date.strftime("%Y-%m-%d") if task.completion_date else "N/A"
                win_status = "✓" if task.is_win else ""
                values = (task.short_desc, "", due_date, completed_date, task.get_state(self.tasks), "", win_status, "")
            elif self.current_filter == "contingent":
                #print(task.get_state(self.tasks))
                values = (task.short_desc, "", due_date,"", task.get_state(self.tasks), "", "", "")
            else:
                this_recurrence = "" if task.recurrence_type.lower() == "none" else "🕑"
                values = (task.short_desc, priority, due_date, "", "", "", "", "", this_recurrence)
            item = self.tree.insert("", "end", values=values)
            self.tree.item(item, tags=(task.id, "reminder" if "[remind delegate]" in task.short_desc else ""))
        if self.current_filter == "actionable":
            self.tree.tag_configure("reminder", font=("Segoe UI", 9, "bold"))
        else:
            self.tree.tag_configure("reminder", font=("Segoe UI", 9))
            
        # Re-select the current task if it's in the filtered list
        if self.current_task_id:
            task_ids = [task.id for task in tasks]  # IDs of tasks in the current filter
            if self.current_task_id in task_ids:
                for item in self.tree.get_children():
                    if self.tree.item(item, "tags")[0] == self.current_task_id:
                        self.tree.selection_set(item)
                        self.tree.focus(item)
                        self.tree.see(item)  # Ensure the item is visible
                        break

        
        # Reconfigure scrollbar and force geometry update
        self.setup_scrollbar()
        self.tree.update_idletasks()
        self.tree_frame.update()

        # Ensure scrollbar visibility based on content
        #if len(tasks) > 10:  # Arbitrary threshold; adjust based on Treeview height
        #    self.y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        #else:
        #    self.y_scrollbar.pack_forget()  # Hide if not needed

        self.tree.bind("<ButtonRelease-1>", self.show_task_details)

    def add_task(self):
        self.show_task_details(None, new_task=True)

    def show_task_details(self, event=None, task_id=None, new_task=False):
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        if new_task:
            self.current_task_id = None
            task = Task("", "", 50, 0, 50, datetime.now() + timedelta(days=7), impact_is_percentage=True)
        else:
            if not task_id:
                selected = self.tree.selection()
                if not selected:
                    self.current_task_id = None
                    return
                task_id = self.tree.item(selected[0], "tags")[0]
            task = next((t for t in self.tasks if t.id == task_id), None)
            if not task:
                self.current_task_id = None
                return
            self.current_task_id = task_id

        if new_task:
            ttk.Label(self.detail_frame, text="Create New Task").pack(fill=tk.X)
        else:
            ttk.Label(self.detail_frame, text="Task Details").pack(fill=tk.X)
        fields = [
            ("Short Description", "short_desc", tk.StringVar(value=task.short_desc)),
            ("Area", "area", tk.StringVar(value=task.area)),
            ("Entity", "entity", tk.StringVar(value=task.entity)),
            ("Maintenance Plan", "maintenance_plan", tk.StringVar(value=task.maintenance_plan)),
            ("Procedure Doc", "procedure_doc", tk.StringVar(value=task.procedure_doc)),
            ("Requestor", "requestor", tk.StringVar(value=task.requestor)),
            ("Project", "project", tk.StringVar(value=task.project)),
            ("Safety (1-100%)", "safety", tk.IntVar(value=task.safety)),
            ("Hype (1-100%)", "hype", tk.IntVar(value=task.hype)),
            ("Impact ($ or %)", "impact", tk.StringVar(value=task.impact)),
            ("Impact is % if checked", "impact_is_percentage", tk.BooleanVar(value=task.impact_is_percentage)),
            ("Task is W.I.N.", "is_win", tk.BooleanVar(value=task.is_win)),
        ]

        for label, attr, var in fields:
            frame = ttk.Frame(self.detail_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Label(frame, text=label, width=25).pack(side=tk.LEFT)
            if isinstance(var, tk.BooleanVar):
                ttk.Checkbutton(frame, variable=var).pack(side=tk.LEFT)
            else:
                ttk.Entry(frame, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.detail_widgets[attr] = var

        ttk.Label(self.detail_frame, text="Long Description").pack(fill=tk.X, padx=5, pady=2)
        desc_pane = ttk.PanedWindow(self.detail_frame, orient=tk.VERTICAL)
        desc_pane.pack(fill=tk.BOTH, expand=True)
        desc_frame = ttk.Frame(desc_pane)
        desc_pane.add(desc_frame, weight=0)
        long_desc_text = tk.Text(desc_frame, height=5, width=40, wrap="word", font=("Arial", 10))
        long_desc_text.insert("1.0", task.long_desc)
        long_desc_scroll = ttk.Scrollbar(desc_frame, orient="vertical", command=long_desc_text.yview)
        long_desc_text.configure(yscrollcommand=long_desc_scroll.set)
        long_desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        long_desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_widgets["long_desc"] = long_desc_text

        due_date_var = tk.StringVar(value=task.due_date.strftime("%Y-%m-%d"))
        frame = ttk.Frame(self.detail_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(frame, text="Due Date (YYYY-MM-DD)", width=25).pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=due_date_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.detail_widgets["due_date"] = due_date_var

        delegate_var = tk.StringVar()
        frame = ttk.Frame(self.detail_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(frame, text="Delegate", width=25).pack(side=tk.LEFT)
        delegate_combo = ttk.Combobox(frame, textvariable=delegate_var, 
                                    values=[""] + [p.name for p in self.people])
        delegate_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if task.delegate:
            delegate_var.set(task.delegate.name)
        self.detail_widgets["delegate"] = delegate_var

        delegate_reminder_frame = ttk.Frame(self.detail_frame)
        delegate_reminder_frame.pack(fill=tk.X, padx=5, pady=2)
        delegate_reminder_label = ttk.Label(delegate_reminder_frame, text="Delegate Reminder (days, 0=never)", width=35)
        delegate_reminder_var = tk.IntVar(value=task.delegate_reminder_days)
        delegate_reminder_entry = ttk.Entry(delegate_reminder_frame, textvariable=delegate_reminder_var)
        self.detail_widgets["delegate_reminder_days"] = delegate_reminder_var

        def update_delegate_reminder_visibility(*args):
            if delegate_var.get():
                delegate_reminder_label.pack(side=tk.LEFT)
                delegate_reminder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                delegate_reminder_label.pack_forget()
                delegate_reminder_entry.pack_forget()

        delegate_var.trace("w", update_delegate_reminder_visibility)
        update_delegate_reminder_visibility()

        recurrence_frame = ttk.LabelFrame(self.detail_frame, text="Recurrence Settings")
        recurrence_frame.pack(fill=tk.X, padx=5, pady=5)

        recurrence_type_var = tk.StringVar(value=task.recurrence_type)
        frame = ttk.Frame(recurrence_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(frame, text="Recurrence Type", width=30).pack(side=tk.LEFT)
        recurrence_type_combo = ttk.Combobox(frame, textvariable=recurrence_type_var, 
                                            values=["none", "weekly", "monthly", "annually", "every_n"])
        recurrence_type_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.detail_widgets["recurrence_type"] = recurrence_type_var

        first_active_date_var = tk.StringVar(value=task.first_active_date.strftime("%Y-%m-%d") if task.first_active_date else datetime.now().strftime("%Y-%m-%d"))
        frame = ttk.Frame(recurrence_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(frame, text="First Active Date (YYYY-MM-DD)", width=30).pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=first_active_date_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.detail_widgets["first_active_date"] = first_active_date_var

        settings_frame = ttk.Frame(recurrence_frame)
        settings_frame.pack(fill=tk.X, padx=5, pady=2)

        self.detail_widgets["recurrence_settings"] = {}
        def update_recurrence_settings(*args):
            for widget in settings_frame.winfo_children():
                widget.destroy()
            self.detail_widgets["recurrence_settings"].clear()
            r_type = recurrence_type_var.get()
            
            if r_type == "weekly":
                ttk.Label(settings_frame, text="Days of Week").pack(fill=tk.X)
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                current_days = task.recurrence_settings.get("days", [])
                day_frame = ttk.Frame(settings_frame)
                day_frame.pack(fill=tk.X)
                for day in days:
                    var = tk.BooleanVar(value=day in current_days)
                    ttk.Checkbutton(day_frame, text=day, variable=var).pack(side=tk.LEFT)
                    self.detail_widgets["recurrence_settings"][f"weekly_{day}"] = var

            elif r_type == "monthly":
                frame = ttk.Frame(settings_frame)
                frame.pack(fill=tk.X)
                ttk.Label(frame, text="Day of Month", width=30).pack(side=tk.LEFT)
                day_var = tk.IntVar(value=task.recurrence_settings.get("day", 1))
                ttk.Entry(frame, textvariable=day_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.detail_widgets["recurrence_settings"]["monthly_day"] = day_var

            elif r_type == "annually":
                frame = ttk.Frame(settings_frame)
                frame.pack(fill=tk.X)
                ttk.Label(frame, text="Month", width=30).pack(side=tk.LEFT)
                month_var = tk.IntVar(value=task.recurrence_settings.get("month", 1))
                ttk.Entry(frame, textvariable=month_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.detail_widgets["recurrence_settings"]["annually_month"] = month_var
                frame = ttk.Frame(settings_frame)
                frame.pack(fill=tk.X)
                ttk.Label(frame, text="Day", width=30).pack(side=tk.LEFT)
                day_var = tk.IntVar(value=task.recurrence_settings.get("day", 1))
                ttk.Entry(frame, textvariable=day_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.detail_widgets["recurrence_settings"]["annually_day"] = day_var

            elif r_type == "every_n":
                frame = ttk.Frame(settings_frame)
                frame.pack(fill=tk.X)
                ttk.Label(frame, text="Every N", width=30).pack(side=tk.LEFT)
                n_var = tk.IntVar(value=task.recurrence_settings.get("n", 1))
                ttk.Entry(frame, textvariable=n_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.detail_widgets["recurrence_settings"]["every_n_n"] = n_var
                frame = ttk.Frame(settings_frame)
                frame.pack(fill=tk.X)
                ttk.Label(frame, text="Unit", width=30).pack(side=tk.LEFT)
                unit_var = tk.StringVar(value=task.recurrence_settings.get("unit", "days"))
                ttk.Combobox(frame, textvariable=unit_var, values=["days", "weeks", "months", "years"]).pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.detail_widgets["recurrence_settings"]["every_n_unit"] = unit_var
                target_frame = ttk.Frame(settings_frame)
                target_frame.pack(fill=tk.X)
                def update_target_field(*args):
                    for widget in target_frame.winfo_children():
                        widget.destroy()
                    unit = unit_var.get()
                    if unit == "days":
                        return
                    elif unit == "weeks":
                        frame = ttk.Frame(target_frame)
                        frame.pack(fill=tk.X)
                        ttk.Label(frame, text="Day of Week", width=20).pack(side=tk.LEFT)
                        target_var = tk.StringVar(value=task.recurrence_settings.get("target", "Monday"))
                        ttk.Combobox(frame, textvariable=target_var, values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]).pack(side=tk.LEFT, fill=tk.X, expand=True)
                        self.detail_widgets["recurrence_settings"]["every_n_target"] = target_var
                    elif unit == "months":
                        frame = ttk.Frame(target_frame)
                        frame.pack(fill=tk.X)
                        ttk.Label(frame, text="Day of Month", width=20).pack(side=tk.LEFT)
                        target_var = tk.IntVar(value=task.recurrence_settings.get("target", 1))
                        ttk.Entry(frame, textvariable=target_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
                        self.detail_widgets["recurrence_settings"]["every_n_target"] = target_var
                    elif unit == "years":
                        frame = ttk.Frame(target_frame)
                        frame.pack(fill=tk.X)
                        ttk.Label(frame, text="Month", width=20).pack(side=tk.LEFT)
                        target_var = tk.IntVar(value=task.recurrence_settings.get("target", 1))
                        ttk.Entry(frame, textvariable=target_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
                        self.detail_widgets["recurrence_settings"]["every_n_target"] = target_var
                        frame = ttk.Frame(target_frame)
                        frame.pack(fill=tk.X)
                        ttk.Label(frame, text="Day", width=20).pack(side=tk.LEFT)
                        day_var = tk.IntVar(value=task.recurrence_settings.get("day", 1))
                        ttk.Entry(frame, textvariable=day_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
                        self.detail_widgets["recurrence_settings"]["every_n_day"] = day_var
                unit_var.trace("w", update_target_field)
                update_target_field()

        recurrence_type_var.trace("w", update_recurrence_settings)
        update_recurrence_settings()

        ttk.Button(self.detail_frame, text="Select Related Tasks", 
                  command=partial(self.select_related_tasks, task)).pack(pady=5)

        button_frame = ttk.Frame(self.detail_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Save", 
                  command=partial(self.save_task, task, new_task)).pack(side=tk.LEFT, padx=5)
        if not new_task:
            if task.is_snoozed():
                ttk.Button(button_frame, text="Un-snooze", 
                          command=partial(self.unsnooze_task, task, new_task)).pack(side=tk.LEFT)
            else:
                snooze_frame = ttk.Frame(button_frame)
                snooze_frame.pack(side=tk.LEFT)
                ttk.Button(snooze_frame, text="Snooze", 
                          command=partial(self.snooze_task, task, new_task)).pack(side=tk.LEFT)
                snooze_days_var = tk.StringVar(value="1")
                ttk.Entry(snooze_frame, textvariable=snooze_days_var, width=5).pack(side=tk.LEFT)
                ttk.Label(snooze_frame, text="days").pack(side=tk.LEFT)
                self.detail_widgets["snooze_days"] = snooze_days_var
            ttk.Button(button_frame, text="Complete", 
                      command=partial(self.complete_task, task, new_task)).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Abandon", 
                      command=partial(self.abandon_task, task, new_task)).pack(side=tk.LEFT, padx=5)
            if task.status != "active":
                ttk.Button(button_frame, text="Revive", 
                          command=partial(self.revive_task, task, new_task)).pack(side=tk.LEFT, padx=5)

#######Contingent Task Popup

    def select_related_tasks(self, task):
        window = tk.Toplevel(self.root)
        window.title("Checked tasks are [prereq for/contingent on] this task.")

        # Configurable popup size (change these to make the popup bigger)
        window_width = 450  # Increase this to make the popup wider
        window_height = 400  # Increase this to make the popup taller
        window.geometry(f"{window_width}x{window_height}")

        # Font metrics
        canvas_font = Font(family="TkDefaultFont", size=9)
        text_line_height = canvas_font.metrics("linespace")
        text_line_gap = 5
        row_height = text_line_height + text_line_gap * 2
        x_offset = 5
        right_x_offset = 20  # For scrollbar
        col_widths = [200, 100, 60, 60]  # Short Desc, Due Date, Prereq, Cont
        col_positions = [x_offset]
        for w in col_widths[:-1]:
            col_positions.append(col_positions[-1] + w)

        # Search bar
        search_var = tk.StringVar()
        ttk.Label(window, text="Search").pack()
        search_entry = ttk.Entry(window, textvariable=search_var)
        search_entry.pack(fill=tk.X)

        # Canvas and scrollbar
        canvas_frame = ttk.Frame(window)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Selections storage
        selections = {"prerequisites": {}, "contingents": {}}
        for t in self.tasks:
            if t.status not in ["completed", "abandoned"] and t.id != task.id:
                selections["prerequisites"][t.id] = tk.BooleanVar(value=t.id in task.prerequisites)
                selections["contingents"][t.id] = tk.BooleanVar(value=t.id in task.contingents)

        # Track selected task
        selected_task_id = None

        # Tooltip storage
        tooltip_data = {}  # Dictionary to store tooltip info per text item

        def truncate_text(text, max_width, font):
            if font.measure(text) <= max_width:
                return text
            truncated = ""
            for word in text.split(" "):
                test_line = truncated + " " + word if truncated else word
                test_line_with_ellipsis = test_line + "..."
                if font.measure(test_line_with_ellipsis) <= max_width:
                    truncated = test_line
                else:
                    # If adding the word exceeds width, stop and add ellipsis
                    return truncated + "..." if truncated else ""
            return truncated + "..." if truncated else ""

        def update_related_task_list(*args):
            nonlocal selected_task_id
            canvas.delete("all")
            tooltip_data.clear()  # Clear previous tooltip data
            search = search_var.get().lower()
            visible_tasks = []
            for t in self.tasks:
                if t.status not in ["completed", "abandoned"] and t.id != task.id:
                    if search and not any(search in str(v).lower() for v in [
                        t.short_desc, t.long_desc, str(t.safety), str(t.impact), str(t.hype),
                        t.area, t.entity, t.maintenance_plan, t.procedure_doc, t.requestor, t.project,
                        str(t.is_win), t.due_date.strftime("%Y-%m-%d")
                    ]):
                        continue
                    visible_tasks.append(t)

            # Calculate canvas size
            canvas_height = max(200, len(visible_tasks) * row_height + 40)  # 40 for header
            canvas.config(scrollregion=(0, 0, sum(col_widths) + x_offset, canvas_height))

            # Draw headers
            headers = ["Description", "Due Date", "Prereq", "Cont"]
            y_offset = 10
            for i, header in enumerate(headers):
                canvas.create_text(col_positions[i], y_offset, text=header, anchor=tk.NW, font=canvas_font)

            # Draw task rows
            y_offset = 40
            for t in visible_tasks:
                # Clickable rectangle
                rect = canvas.create_rectangle(
                    x_offset, y_offset, sum(col_widths) + x_offset, y_offset + row_height,
                    fill="white" if t.id != selected_task_id else "lightblue",
                    tags=("row", f"task_{t.id}")
                )
                

                # Task data with tooltips
                short_desc = truncate_text(t.short_desc, col_widths[0]-3, canvas_font)
                due_date = t.due_date.strftime("%Y-%m-%d")
                desc_text = canvas.create_text(col_positions[0]+3, y_offset + text_line_gap, text=short_desc, anchor=tk.NW, font=canvas_font, tags=("text", f"desc_{t.id}", f"task_{t.id}"))
                date_text = canvas.create_text(col_positions[1], y_offset + text_line_gap, text=due_date, anchor=tk.NW, font=canvas_font, tags=("text", f"date_{t.id}"))
                canvas.tag_bind(f"desc_{t.id}", "<Button-1>", lambda e, tid=t.id: select_row(tid))

                # Initialize tooltip data
                tooltip_data[f"task_{t.id}"] = {
                    "text": t.short_desc,
                    "wait_id": None,
                    "tw": None,
                    "wait_time": 500,
                    "wrap_length": 200,
                    "x_offset": col_positions[0],
                    "y_offset": y_offset + text_line_gap
                }
                

                # Bind tooltip events
                canvas.tag_bind(f"desc_{t.id}", "<Enter>", lambda e, tid=f"task_{t.id}": enter_tooltip(e, tid))
                canvas.tag_bind(f"desc_{t.id}", "<Leave>", lambda e, tid=f"task_{t.id}": leave_tooltip(e, tid))

                # Checkboxes
                prereq_check = ttk.Checkbutton(canvas, variable=selections["prerequisites"][t.id])
                cont_check = ttk.Checkbutton(canvas, variable=selections["contingents"][t.id])
                canvas.create_window(col_positions[2] + col_widths[2]//2, y_offset + row_height//2, window=prereq_check)
                canvas.create_window(col_positions[3] + col_widths[3]//2, y_offset + row_height//2, window=cont_check)

                y_offset += row_height
        
        def enter_tooltip(event, tag_id):
            schedule_tooltip(tag_id)

        def leave_tooltip(event, tag_id):
            unschedule_tooltip(tag_id)
            hide_tooltip(tag_id)

        def schedule_tooltip(tag_id):
            unschedule_tooltip(tag_id)
            tooltip_data[tag_id]["wait_id"] = canvas.after(tooltip_data[tag_id]["wait_time"], lambda: show_tooltip(tag_id))

        def unschedule_tooltip(tag_id):
            wait_id = tooltip_data[tag_id]["wait_id"]
            if wait_id:
                canvas.after_cancel(wait_id)
                tooltip_data[tag_id]["wait_id"] = None

        def show_tooltip(tag_id):
            data = tooltip_data[tag_id]
            x = canvas.winfo_rootx() + data["x_offset"] + 10
            y = canvas.winfo_rooty() + data["y_offset"] - 10
            data["tw"] = tk.Toplevel(canvas)
            data["tw"].wm_overrideredirect(True)
            data["tw"].wm_geometry(f"+{x}+{y}")
            label = tk.Label(data["tw"], text=data["text"], justify='left',
                            background="#ffffff", relief='solid', borderwidth=1,
                            wraplength=data["wrap_length"])
            label.pack(ipadx=1)

        def hide_tooltip(tag_id):
            tw = tooltip_data[tag_id]["tw"]
            tooltip_data[tag_id]["tw"] = None
            if tw:
                tw.destroy()

        def select_row(task_id):
            nonlocal selected_task_id
            if selected_task_id:
                canvas.itemconfig(f"task_{selected_task_id}", fill="white")
            selected_task_id = task_id
            canvas.itemconfig(f"task_{task_id}", fill="lightblue")

        def save_selections():
            new_prerequisites = [tid for tid, var in selections["prerequisites"].items() if var.get()]
            new_contingents = [tid for tid, var in selections["contingents"].items() if var.get()]
            task.prerequisites = new_prerequisites
            task.contingents = new_contingents
            for t in self.tasks:
                if t.id != task.id and t.status not in ["completed", "abandoned"]:
                    if t.id in new_contingents and task.id not in t.prerequisites:
                        t.prerequisites.append(task.id)
                    elif t.id not in new_contingents and task.id in t.prerequisites:
                        t.prerequisites.remove(task.id)
                    if t.id in new_prerequisites and task.id not in t.contingents:
                        t.contingents.append(task.id)
                    elif t.id not in new_prerequisites and task.id in t.contingents:
                        t.contingents.remove(task.id)
            self.save_data()
            self.update_task_list()
            window.destroy()

        # Bind events
        search_var.trace("w", update_related_task_list)
        canvas.bind("<Configure>", update_related_task_list)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta/120), "units"))

        # Confirm button
        ttk.Button(window, text="Confirm", command=save_selections).pack()

        # Initial update
        update_related_task_list()
#######End Contingent Task Popup

    def save_task(self, task, new_task):
        try:
            task.short_desc = self.detail_widgets["short_desc"].get()
            task.long_desc = self.detail_widgets["long_desc"].get("1.0", tk.END).strip()
            task.safety = self.detail_widgets["safety"].get()
            impact_value = self.detail_widgets["impact"].get().strip()
            if self.detail_widgets["impact_is_percentage"].get():
                task.impact = max(0, min(100, int(impact_value.replace("%", "")) if impact_value.endswith("%") else int(impact_value)))
                task.impact_is_percentage = True
            else:
                task.impact = max(0, float(impact_value.replace("$", "").replace(",", "")) if impact_value else 0)
                task.impact_is_percentage = False
            task.hype = self.detail_widgets["hype"].get()
            task.due_date = datetime.strptime(self.detail_widgets["due_date"].get(), "%Y-%m-%d")
            task.area = self.detail_widgets["area"].get()
            task.entity = self.detail_widgets["entity"].get()
            task.maintenance_plan = self.detail_widgets["maintenance_plan"].get()
            task.procedure_doc = self.detail_widgets["procedure_doc"].get()
            task.requestor = self.detail_widgets["requestor"].get()
            task.project = self.detail_widgets["project"].get()
            task.is_win = self.detail_widgets["is_win"].get()
            task.delegate_reminder_days = self.detail_widgets["delegate_reminder_days"].get()
            delegate_name = self.detail_widgets["delegate"].get()
            task.delegate = next((p for p in self.people if p.name == delegate_name), None) if delegate_name else None

            task.recurrence_type = self.detail_widgets["recurrence_type"].get()
            task.first_active_date = datetime.strptime(self.detail_widgets["first_active_date"].get(), "%Y-%m-%d")
            task.recurrence_settings = {}
            if task.recurrence_type == "weekly":
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                selected_days = [day for day in days if self.detail_widgets["recurrence_settings"].get(f"weekly_{day}", tk.BooleanVar(value=False)).get()]
                task.recurrence_settings["days"] = selected_days
            elif task.recurrence_type == "monthly":
                task.recurrence_settings["day"] = self.detail_widgets["recurrence_settings"]["monthly_day"].get()
            elif task.recurrence_type == "annually":
                task.recurrence_settings["month"] = self.detail_widgets["recurrence_settings"]["annually_month"].get()
                task.recurrence_settings["day"] = self.detail_widgets["recurrence_settings"]["annually_day"].get()
            elif task.recurrence_type == "every_n":
                task.recurrence_settings["n"] = self.detail_widgets["recurrence_settings"]["every_n_n"].get()
                task.recurrence_settings["unit"] = self.detail_widgets["recurrence_settings"]["every_n_unit"].get()
                if task.recurrence_settings["unit"] != "days":
                    task.recurrence_settings["target"] = self.detail_widgets["recurrence_settings"]["every_n_target"].get()
                    if task.recurrence_settings["unit"] == "years":
                        task.recurrence_settings["day"] = self.detail_widgets["recurrence_settings"]["every_n_day"].get()

            if new_task:
                self.tasks.append(task)
                self.current_task_id = task.id
            self.save_data()
            self.update_task_list()
            if new_task:
                self.show_task_details(task_id=task.id, new_task=False)
        except (ValueError, Exception) as e:
            messagebox.showerror("Error", f"Failed to save task: {str(e)}")

    def snooze_task(self, task, new_task):
        self.save_task(task, new_task)
        try:
            days = int(self.detail_widgets["snooze_days"].get())
            target_date = (datetime.now() + timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
            task.snooze_until = target_date
        except (ValueError, KeyError):
            task.snooze_until = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.save_data()
        self.show_task_details(task_id=task.id, new_task=False) #show again because buttons change
        self.update_task_list()

    def unsnooze_task(self, task, new_task):
        self.save_task(task, new_task)
        task.snooze_until = None
        self.save_data()
        self.show_task_details(task_id=task.id, new_task=False) #show again because buttons change
        self.update_task_list()
        
    def create_next_recurrance(self, task):
        if task.recurrence_type != "none":
            next_revival = task.get_next_revival_time()
            if next_revival:
                time_diff = task.due_date - task.first_active_date if task.first_active_date else timedelta(days=0)
                new_task = Task(
                    short_desc=task.short_desc,
                    long_desc=task.long_desc,
                    safety=task.safety,
                    impact=task.impact,
                    hype=task.hype,
                    due_date=next_revival + time_diff,
                    area=task.area,
                    entity=task.entity,
                    maintenance_plan=task.maintenance_plan,
                    procedure_doc=task.procedure_doc,
                    requestor=task.requestor,
                    project=task.project,
                    is_win=task.is_win,
                    prerequisites=task.prerequisites.copy(),
                    contingents=task.contingents.copy(),
                    delegate=task.delegate,
                    status="active",
                    impact_is_percentage=task.impact_is_percentage,
                    recurrence_type=task.recurrence_type,
                    recurrence_settings=task.recurrence_settings.copy(),
                    first_active_date=next_revival,
                    snooze_until=next_revival,
                    delegate_reminder_days=task.delegate_reminder_days
                )
                self.tasks.append(new_task)

    def complete_task(self, task, new_task):
        self.save_task(task, new_task)
        task.status = "completed"
        task.completion_date = datetime.now()
        self.save_task(task, new_task)
        if task.recurrence_type != "none":
            self.create_next_recurrance(task)
        self.save_data()
        self.show_task_details(task_id=task.id, new_task=False) #show again because buttons change
        self.update_task_list()

    def abandon_task(self, task, new_task):
        self.save_task(task, new_task)
        task.status = "abandoned"
        task.completion_date = datetime.now()
        if task.recurrence_type != "none":
            answer = messagebox.askyesno("Abandon instance of recurring task?", "You are abandoning a task which is set up as recurring. \n\n- Press 'Yes' to continue recurring in the future. \n- Press 'No' to terminate all future recurrances.")
            if answer:
                self.create_next_recurrance(task)
        self.save_data()
        self.show_task_details(task_id=task.id, new_task=False) #show again because buttons change
        self.update_task_list()

    def revive_task(self, task, new_task):
        self.save_task(task, new_task)
        task.status = "active"
        task.completion_date = None
        task.snooze_until = None
        self.save_data()
        self.show_task_details(task_id=task.id, new_task=False) #show again because buttons change
        self.update_task_list()

    def manage_people(self):
        people_window = tk.Toplevel(self.root)
        people_window.title("Manage People")
        tree = ttk.Treeview(people_window, columns=("Name", "Job Title", "Department"), show="headings", selectmode="extended")
        tree.heading("Name", text="Name")
        tree.heading("Job Title", text="Job Title")
        tree.heading("Department", text="Department")
        tree.pack(fill=tk.BOTH, expand=True)
        for person in self.people:
            tree.insert("", "end", values=(person.name, person.job_title, person.department), tags=(person.id,))
        form_frame = ttk.Frame(people_window)
        form_frame.pack(fill=tk.X)
        fields = [
            ("Name", tk.StringVar()),
            ("Job Title", tk.StringVar()),
            ("Department", tk.StringVar()),
            ("Area", tk.StringVar()),
            ("Contractor", tk.BooleanVar())
        ]
        for label, var in fields:
            frame = ttk.Frame(form_frame)
            frame.pack(fill=tk.X)
            ttk.Label(frame, text=label).pack(side=tk.LEFT)
            if isinstance(var, tk.BooleanVar):
                ttk.Checkbutton(frame, variable=var).pack(side=tk.LEFT)
            else:
                ttk.Entry(frame, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=tk.X)
        ttk.Button(button_frame, text="Add Person", command=partial(self.add_person, fields, people_window)).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Delete Selected", command=partial(self.delete_people, tree, people_window)).pack(side=tk.LEFT)

    def add_person(self, fields, window):
        try:
            person = Person(
                name=fields[0][1].get(),
                job_title=fields[1][1].get(),
                department=fields[2][1].get(),
                area=fields[3][1].get(),
                is_contractor=fields[4][1].get()
            )
            self.people.append(person)
            self.save_data()
            messagebox.showinfo("Success", "Person added successfully")
            window.destroy()
            self.manage_people()  # Refresh the people manager
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add person: {str(e)}")

    def delete_people(self, tree, window):
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select at least one person to delete.")
            return

        person_ids = [tree.item(item, "tags")[0] for item in selected_items]
        dependent_tasks = []
        for person_id in person_ids:
            tasks = [t for t in self.tasks if t.delegate and t.delegate.id == person_id]
            dependent_tasks.extend(tasks)

        if dependent_tasks:
            task_list = "\n".join([f"- {t.short_desc}" for t in dependent_tasks])
            response = messagebox.askyesno(
                "Tasks Assigned",
                f"The following tasks are assigned to the selected person(s):\n{task_list}\n\n"
                "Clear these assignments and proceed with deletion?",
            )
            if not response:
                return
            for task in dependent_tasks:
                task.delegate = None
                task.delegate_reminder_days = 0

        for person_id in person_ids:
            self.people = [p for p in self.people if p.id != person_id]

        self.save_data()
        messagebox.showinfo("Success", f"{len(person_ids)} person(s) deleted successfully.")
        window.destroy()
        self.manage_people()  # Refresh the people manager

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    task_manager = TaskManager()
    task_manager.run()
