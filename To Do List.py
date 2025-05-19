import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime, timedelta
import uuid
from functools import partial
import calendar

window_geometry = "1250x760"
default_main_sashpos = 700

class Task:
    def __init__(self, short_desc, long_desc, safety, impact, hype, due_date, 
                 area="", entity="", maintenance_plan="", procedure_doc="", 
                 requestor="", project="", is_win=False, id=None, prerequisites=None,
                 contingents=None, delegate=None, status=None, completion_date=None,
                 snooze_until=None, impact_is_percentage=False,
                 recurrence_type="none", recurrence_settings=None, first_active_date=None):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.short_desc = short_desc
        self.long_desc = long_desc
        self.safety = safety  # 1-100 range
        self.impact = impact  # Dollar amount or percentage (0-100000) depending on impact_is_percentage
        self.hype = hype  # 1-100 range
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
        self.delegate = delegate  # Will be a Person object or None
        if status is None:
            self.status = "active"  # active, completed, abandoned
        else:
            self.status = status
        self.completion_date = completion_date
        self.snooze_until = snooze_until
        self.impact_is_percentage = impact_is_percentage
        # Recurrence fields
        self.recurrence_type = recurrence_type  # none, weekly, monthly, annually, every_n
        if recurrence_settings is None:
            self.recurrence_settings = {}
        else:
            self.recurrence_settings = recurrence_settings
        self.first_active_date = first_active_date

    def calculate_priority(self, tasks):
        if self.status != "active":
            return -1
        for prereq_id in self.prerequisites:
            prereq = next((t for t in tasks if t.id == prereq_id), None)
            if prereq and prereq.status != "completed":
                return -1
        urgency = max(1, (self.due_date - datetime.now()).days)
        impact_value = self.impact
        if self.impact_is_percentage:
            impact_value = impact_value * 10  # Scale 0-100% to 0-1000 (equivalent to dollar range)
        priority = (self.safety * 0.4 / 100 + self.hype * 0.2 / 100 + impact_value / 100000 * 0.3 + (30 / urgency) * 0.2)
        for cont_id in self.contingents:
            cont = next((t for t in tasks if t.id == cont_id), None)
            if cont and cont.status == "active":
                cont_priority = cont.calculate_priority(tasks)
                if cont_priority > priority:
                    priority = cont_priority
        return priority

    def needs_reminder(self):
        if self.delegate and self.status == "active" and not self.is_snoozed():
            priority = self.calculate_priority(task_manager.tasks)
            if priority < 0:
                return False
            days = (self.due_date - datetime.now()).days
            if days < 7:
                return True
            elif priority > 10:
                return (datetime.now().weekday() == 0)
            else:
                return (datetime.now().day == 1 or datetime.now().day == 15)
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
            days_of_week = self.recurrence_settings.get("days", [])  # e.g., ["Monday", "Wednesday"]
            if not days_of_week:
                return None
            day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
            target_days = [day_map[day] for day in days_of_week]
            current_weekday = reference_time.weekday()
            days_ahead = []
            for target in target_days:
                delta = (target - current_weekday) % 7
                if delta == 0:
                    delta = 7  # If the day matches, schedule for next week
                days_ahead.append(delta)
            min_days = min(days_ahead)
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
            target = self.recurrence_settings.get("target")  # e.g., "Wednesday", 15 (for day of month), 3 (for month of year)
            if unit == "days":
                return reference_time + timedelta(days=n)
            elif unit == "weeks":
                day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
                target_day = day_map[target]
                next_date = reference_time + timedelta(weeks=n)
                days_ahead = (target_day - next_date.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Ensure we don't schedule for the same day
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
        self.sort_column = "Priority"  # Default sort column
        self.sort_direction = "desc"  # Default sort direction: descending
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
                    # Ignore last_revival_time as it's no longer used
                    task_data.pop("last_revival_time", None)
                    task_data["safety"] = task_data.get("safety", 50)
                    task_data["hype"] = task_data.get("hype", 50)
                    task_data["impact"] = task_data.get("impact", 0)
                    task_data["impact_is_percentage"] = task_data.get("impact_is_percentage", True)
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

        # Add search bar
        search_frame = ttk.Frame(self.list_frame)
        search_frame.pack(fill=tk.X, side=tk.TOP)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_query)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_query.trace("w", lambda name, index, mode, sv=self.search_query: self.update_task_list())

        filter_frame = ttk.Frame(self.list_frame)
        filter_frame.pack(fill=tk.X, side=tk.TOP)
        ttk.Button(filter_frame, text="Actionable Only", command=partial(self.set_filter, "actionable")).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="All Tasks", command=partial(self.set_filter, "all")).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="Snoozed", command=partial(self.set_filter, "snoozed")).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="Completed/Abandoned", command=partial(self.set_filter, "completed_abandoned")).pack(side=tk.LEFT)

        self.tree = ttk.Treeview(self.list_frame, columns=("Short Desc", "Priority", "Due Date", "Completed/Abandoned Date", "State", "Snooze Duration"), show="headings")
        self.tree.heading("Short Desc", text="Description")
        self.tree.heading("Priority", text="Priority")
        self.tree.heading("Due Date", text="Due Date")
        self.tree.heading("Completed/Abandoned Date", text="Completed/Abandoned Date")
        self.tree.heading("State", text="State")
        self.tree.heading("Snooze Duration", text="Snooze Duration")
        self.tree.column("Short Desc", width=200)
        self.tree.column("Priority", width=80)
        self.tree.column("Due Date", width=100)
        self.tree.column("Completed/Abandoned Date", width=150)
        self.tree.column("State", width=50)
        self.tree.column("Snooze Duration", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bind click on column headers for sorting
        for col in self.tree["columns"]:
            self.tree.heading(col, command=lambda c=col: self.sort_by_column(c))

        button_frame = ttk.Frame(self.list_frame)
        button_frame.pack(fill=tk.X, side=tk.TOP)
        ttk.Button(button_frame, text="Add Task", command=self.add_task).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Manage People", command=self.manage_people).pack(side=tk.LEFT)

        self.detail_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.detail_frame, weight=2)
        self.detail_widgets = {}
        self.update_task_list()

    def sort_by_column(self, column):
        # Toggle sort direction if the same column is clicked, otherwise default to ascending
        if self.sort_column == column:
            self.sort_direction = "asc" if self.sort_direction == "desc" else "desc"
        else:
            self.sort_column = column
            self.sort_direction = "asc"
        self.update_task_list()

    def set_filter(self, filter_type):
        self.current_filter = filter_type
        self.update_task_list()

    def update_task_list(self):
        # Generate or update "remind delegate" tasks
        current_time = datetime.now()
        for task in [t for t in self.tasks if t.delegate and t.status == "active"]:
            days_until_due = (task.due_date - current_time).days
            reminder_freq = "daily" if days_until_due < 7 else "weekly"
            
            # Find existing reminder task for this task
            reminder_task = next((t for t in self.tasks if t.prerequisites and t.prerequisites[0] == task.id and "remind delegate" in t.short_desc), None)
            
            if reminder_freq == "weekly":
                first_active = current_time + timedelta(days=(4 - current_time.weekday()) % 7)  # Next Friday
                due_date = first_active + timedelta(days=3)  # Following Monday
                recurrence_settings = {"days": ["Friday"]}
            else:  # daily
                first_active = current_time + timedelta(days=1)
                due_date = first_active + timedelta(days=1)
                recurrence_settings = {"n": 1, "unit": "days"}
            
            if not reminder_task:
                reminder_task = Task(
                    short_desc=f"remind delegate {task.short_desc}",
                    long_desc=task.long_desc,
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
                    prerequisites=[task.id],
                    contingents=task.contingents,
                    delegate=None,
                    status="active",
                    impact_is_percentage=task.impact_is_percentage,
                    recurrence_type=reminder_freq,
                    recurrence_settings=recurrence_settings,
                    first_active_date=first_active
                )
                self.tasks.append(reminder_task)
            else:
                reminder_task.short_desc = f"remind delegate {task.short_desc}"
                reminder_task.due_date = due_date
                reminder_task.recurrence_type = reminder_freq
                reminder_task.recurrence_settings = recurrence_settings
                reminder_task.first_active_date = first_active
            self.save_data()

        for item in self.tree.get_children():
            self.tree.delete(item)

        search_text = self.search_query.get().lower().strip()
        if self.current_filter == "actionable":
            tasks = [t for t in self.tasks if t.status == "active" and t.calculate_priority(self.tasks) >= 0 and not t.is_snoozed()]
            self.tree["columns"] = ("Short Desc", "Priority", "Due Date")
            self.sort_column = "Priority"
        elif self.current_filter == "all":
            tasks = self.tasks
            self.tree["columns"] = ("Short Desc", "Priority", "Due Date", "State")
        elif self.current_filter == "snoozed":
            tasks = [t for t in self.tasks if t.is_snoozed()]
            self.tree["columns"] = ("Short Desc", "Priority", "Due Date", "Snooze Duration")
        elif self.current_filter == "completed_abandoned":
            tasks = [t for t in self.tasks if t.status in ["completed", "abandoned"]]
            self.tree["columns"] = ("Short Desc", "Due Date", "Completed/Abandoned Date", "State")
            self.sort_column = "Completed/Abandoned Date"

        # Apply search filter
        if search_text:
            tasks = [t for t in tasks if any(search_text in str(getattr(t, field)).lower() 
                                           for field in ["short_desc", "long_desc", "safety", "impact", "hype", 
                                                         "area", "entity", "maintenance_plan", "procedure_doc", 
                                                         "requestor", "project", "is_win", 
                                                         "due_date"] 
                                           if getattr(t, field) is not None)]

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100 if col in ["Due Date", "Snooze Duration"] else 150 if col == "Completed/Abandoned Date" else 80 if col == "Priority" else 50 if col == "State" else 200)

        # Sort tasks based on the selected column and direction
        if self.sort_column == "Short Desc":
            tasks.sort(key=lambda t: t.short_desc.lower() if t.short_desc else "", reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "Priority":
            tasks.sort(key=lambda t: t.calculate_priority(self.tasks) if t.status == "active" else -1, reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "Due Date":
            tasks.sort(key=lambda t: t.due_date, reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "Completed/Abandoned Date":
            # Handle None values by sorting them to the end
            tasks.sort(key=lambda t: t.completion_date if t.completion_date else datetime.min, reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "State":
            tasks.sort(key=lambda t: t.get_state(self.tasks), reverse=(self.sort_direction == "desc"))
        elif self.sort_column == "Snooze Duration":
            # Convert snooze duration to a comparable value (days as int)
            tasks.sort(key=lambda t: int(t.get_snooze_duration().split()[0]) if t.is_snoozed() else -1, reverse=(self.sort_direction == "desc"))


        tasks.sort(key=lambda t: t.calculate_priority(self.tasks) if t.status == "active" else -1, reverse=True)
        for task in tasks:
            priority = f"{task.calculate_priority(self.tasks):.2f}" if task.calculate_priority(self.tasks) >= 0 else "N/A"
            due_date = task.due_date.strftime("%Y-%m-%d")
            if self.current_filter == "all":
                values = (task.short_desc, priority, due_date, task.get_state(self.tasks))
            elif self.current_filter == "snoozed":
                values = (task.short_desc, priority, due_date, task.get_snooze_duration())
            elif self.current_filter == "completed_abandoned":
                completed_date = task.completion_date.strftime("%Y-%m-%d") if task.completion_date else "N/A"
                values = (task.short_desc, due_date, completed_date, task.get_state(self.tasks))
            else:
                values = (task.short_desc, priority, due_date)
            item = self.tree.insert("", "end", values=values)
            self.tree.item(item, tags=(task.id,))
        self.tree.bind("<ButtonRelease-1>", self.show_task_details)

    def add_task(self):
        self.show_task_details(None, new_task=True)

    def show_task_details(self, event=None, task_id=None, new_task=False):
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        if new_task:
            task = Task("", "", 50, 0, 50, datetime.now() + timedelta(days=7), impact_is_percentage=True)
        else:
            if not task_id:
                selected = self.tree.selection()
                if not selected:
                    return
                task_id = self.tree.item(selected[0], "tags")[0]
            task = next((t for t in self.tasks if t.id == task_id), None)
            if not task:
                return

        if new_task:
            ttk.Label(self.detail_frame, text="Create New Task").pack()
        else:
            ttk.Label(self.detail_frame, text="Task Details").pack()
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
            ("Impact is % if checked", "impact_is_percentage",tk.BooleanVar(value=task.impact_is_percentage)),
            ("Task is W.I.N.", "is_win", tk.BooleanVar(value=task.is_win)),
        ]

        for label, attr, var in fields:
            frame = ttk.Frame(self.detail_frame)
            frame.pack(fill=tk.X)
            ttk.Label(frame, text=label).pack(side=tk.LEFT)
            if isinstance(var, tk.BooleanVar):
                ttk.Checkbutton(frame, variable=var).pack(side=tk.LEFT)
            else:
                ttk.Entry(frame, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.detail_widgets[attr] = var

        ttk.Label(self.detail_frame, text="Long Description").pack()
        long_desc_text = tk.Text(self.detail_frame, height=5, width=40)
        long_desc_text.insert("1.0", task.long_desc)
        long_desc_text.pack(fill=tk.X)
        self.detail_widgets["long_desc"] = long_desc_text

        due_date_var = tk.StringVar(value=task.due_date.strftime("%Y-%m-%d"))
        ttk.Label(self.detail_frame, text="Due Date (YYYY-MM-DD)").pack()
        ttk.Entry(self.detail_frame, textvariable=due_date_var).pack(fill=tk.X)
        self.detail_widgets["due_date"] = due_date_var

        delegate_var = tk.StringVar()
        ttk.Label(self.detail_frame, text="Delegate").pack()
        delegate_combo = ttk.Combobox(self.detail_frame, textvariable=delegate_var, 
                                    values=[""] + [p.name for p in self.people])
        delegate_combo.pack(fill=tk.X)
        if task.delegate:
            delegate_var.set(task.delegate.name)
        self.detail_widgets["delegate"] = delegate_var

        # Recurrence Settings
        ttk.Label(self.detail_frame, text="Recurrence").pack()
        recurrence_frame = ttk.LabelFrame(self.detail_frame, text="Recurrence Settings")
        recurrence_frame.pack(fill=tk.X, padx=5, pady=5)

        recurrence_type_var = tk.StringVar(value=task.recurrence_type)
        ttk.Label(recurrence_frame, text="Recurrence Type").pack()
        recurrence_type_combo = ttk.Combobox(recurrence_frame, textvariable=recurrence_type_var, 
                                            values=["none", "weekly", "monthly", "annually", "every_n"])
        recurrence_type_combo.pack(fill=tk.X)
        self.detail_widgets["recurrence_type"] = recurrence_type_var

        first_active_date_var = tk.StringVar(value=task.first_active_date.strftime("%Y-%m-%d") if task.first_active_date else datetime.now().strftime("%Y-%m-%d"))
        ttk.Label(recurrence_frame, text="First Active Date (YYYY-MM-DD)").pack()
        ttk.Entry(recurrence_frame, textvariable=first_active_date_var).pack(fill=tk.X)
        self.detail_widgets["first_active_date"] = first_active_date_var

        settings_frame = ttk.Frame(recurrence_frame)
        settings_frame.pack(fill=tk.X)

        self.detail_widgets["recurrence_settings"] = {}
        def update_recurrence_settings(*args):
            for widget in settings_frame.winfo_children():
                widget.destroy()
            self.detail_widgets["recurrence_settings"].clear()
            r_type = recurrence_type_var.get()
            
            if r_type == "weekly":
                ttk.Label(settings_frame, text="Days of Week").pack()
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                current_days = task.recurrence_settings.get("days", [])
                for day in days:
                    var = tk.BooleanVar(value=day in current_days)
                    ttk.Checkbutton(settings_frame, text=day, variable=var).pack(side=tk.LEFT)
                    self.detail_widgets["recurrence_settings"][f"weekly_{day}"] = var

            elif r_type == "monthly":
                ttk.Label(settings_frame, text="Day of Month").pack()
                day_var = tk.IntVar(value=task.recurrence_settings.get("day", 1))
                ttk.Entry(settings_frame, textvariable=day_var).pack(fill=tk.X)
                self.detail_widgets["recurrence_settings"]["monthly_day"] = day_var

            elif r_type == "annually":
                ttk.Label(settings_frame, text="Month").pack()
                month_var = tk.IntVar(value=task.recurrence_settings.get("month", 1))
                ttk.Entry(settings_frame, textvariable=month_var).pack(fill=tk.X)
                self.detail_widgets["recurrence_settings"]["annually_month"] = month_var
                ttk.Label(settings_frame, text="Day").pack()
                day_var = tk.IntVar(value=task.recurrence_settings.get("day", 1))
                ttk.Entry(settings_frame, textvariable=day_var).pack(fill=tk.X)
                self.detail_widgets["recurrence_settings"]["annually_day"] = day_var

            elif r_type == "every_n":
                ttk.Label(settings_frame, text="Every N").pack()
                n_var = tk.IntVar(value=task.recurrence_settings.get("n", 1))
                ttk.Entry(settings_frame, textvariable=n_var).pack(fill=tk.X)
                self.detail_widgets["recurrence_settings"]["every_n_n"] = n_var
                ttk.Label(settings_frame, text="Unit").pack()
                unit_var = tk.StringVar(value=task.recurrence_settings.get("unit", "days"))
                ttk.Combobox(settings_frame, textvariable=unit_var, values=["days", "weeks", "months", "years"]).pack(fill=tk.X)
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
                        ttk.Label(target_frame, text="Day of Week").pack()
                        target_var = tk.StringVar(value=task.recurrence_settings.get("target", "Monday"))
                        ttk.Combobox(target_frame, textvariable=target_var, values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]).pack(fill=tk.X)
                        self.detail_widgets["recurrence_settings"]["every_n_target"] = target_var
                    elif unit == "months":
                        ttk.Label(target_frame, text="Day of Month").pack()
                        target_var = tk.IntVar(value=task.recurrence_settings.get("target", 1))
                        ttk.Entry(target_frame, textvariable=target_var).pack(fill=tk.X)
                        self.detail_widgets["recurrence_settings"]["every_n_target"] = target_var
                    elif unit == "years":
                        ttk.Label(target_frame, text="Month").pack()
                        target_var = tk.IntVar(value=task.recurrence_settings.get("target", 1))
                        ttk.Entry(target_frame, textvariable=target_var).pack(fill=tk.X)
                        self.detail_widgets["recurrence_settings"]["every_n_target"] = target_var
                        ttk.Label(target_frame, text="Day").pack()
                        day_var = tk.IntVar(value=task.recurrence_settings.get("day", 1))
                        ttk.Entry(target_frame, textvariable=day_var).pack(fill=tk.X)
                        self.detail_widgets["recurrence_settings"]["every_n_day"] = day_var
                unit_var.trace("w", update_target_field)
                update_target_field()

        recurrence_type_var.trace("w", update_recurrence_settings)
        update_recurrence_settings()

        ttk.Button(self.detail_frame, text="Select Related Tasks", 
                  command=partial(self.select_related_tasks, task)).pack()

        button_frame = ttk.Frame(self.detail_frame)
        button_frame.pack(fill=tk.X)
        if not new_task:
            if task.is_snoozed():
                ttk.Button(button_frame, text="Un-snooze", 
                          command=partial(self.unsnooze_task, task)).pack(side=tk.LEFT)
            else:
                snooze_frame = ttk.Frame(button_frame)
                snooze_frame.pack(side=tk.LEFT)
                ttk.Button(snooze_frame, text="Snooze", 
                          command=partial(self.snooze_task, task)).pack(side=tk.LEFT)
                snooze_days_var = tk.StringVar(value="1")
                ttk.Entry(snooze_frame, textvariable=snooze_days_var, width=5).pack(side=tk.LEFT)
                ttk.Label(snooze_frame, text="days").pack(side=tk.LEFT)
                self.detail_widgets["snooze_days"] = snooze_days_var
            ttk.Button(button_frame, text="Complete", 
                      command=partial(self.complete_task, task)).pack(side=tk.LEFT)
            ttk.Button(button_frame, text="Abandon", 
                      command=partial(self.abandon_task, task)).pack(side=tk.LEFT)
            if task.status != "active":
                ttk.Button(button_frame, text="Revive", 
                          command=partial(self.revive_task, task)).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Save", 
                  command=partial(self.save_task, task, new_task)).pack(side=tk.LEFT)

    def select_related_tasks(self, task):
        window = tk.Toplevel(self.root)
        window.title("Select Related Tasks")

        search_var = tk.StringVar()
        ttk.Label(window, text="Search").pack()
        ttk.Entry(window, textvariable=search_var).pack(fill=tk.X)

        tree_frame = ttk.Frame(window)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(tree_frame, columns=("Short Desc", "Due Date", "Prerequisite", "Contingent"), show="headings", height=10)
        tree.heading("Short Desc", text="Description")
        tree.heading("Due Date", text="Due Date")
        tree.heading("Prerequisite", text="Prereq")
        tree.heading("Contingent", text="Cont")
        tree.column("Short Desc", width=200)
        tree.column("Due Date", width=100)
        tree.column("Prerequisite", width=60)
        tree.column("Contingent", width=60)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)

        selections = {"prerequisites": {}, "contingents": {}}
        for t in self.tasks:
            if t.status not in ["completed", "abandoned"] and t.id != task.id:
                selections["prerequisites"][t.id] = tk.BooleanVar(value=t.id in task.prerequisites)
                selections["contingents"][t.id] = tk.BooleanVar(value=t.id in task.contingents)

        update_timer = None
        update_delay = 100

        def update_task_list(*args):
            nonlocal update_timer
            if update_timer is not None:
                window.after_cancel(update_timer)
            update_timer = window.after(update_delay, perform_update)

        def perform_update():
            for widget in tree_frame.winfo_children():
                if isinstance(widget, (ttk.Checkbutton, tk.Checkbutton)):
                    widget.destroy()
            for item in tree.get_children():
                tree.delete(item)

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
                    item = tree.insert("", "end", values=(t.short_desc, t.due_date.strftime("%Y-%m-%d"), "", ""))
                    tree.item(item, tags=(t.id,))
                    visible_tasks.append(t)

            update_checkboxes(visible_tasks)

        def update_checkboxes(visible_tasks):
            for widget in tree_frame.winfo_children():
                if isinstance(widget, (ttk.Checkbutton, tk.Checkbutton)):
                    widget.destroy()

            tree.update_idletasks()
            tree_height = tree.winfo_height()
            if tree_height <= 0:
                return

            row_height_pixels = 25
            num_visible_rows = tree_height // row_height_pixels
            if num_visible_rows <= 0:
                num_visible_rows = 1

            scroll_pos = tree.yview()
            scroll_offset = scroll_pos[0]
            total_tasks = len([t for t in self.tasks if t.status not in ["completed", "abandoned"] and t.id != task.id])
            visible_task_count = len(visible_tasks)

            if total_tasks > 0:
                start_index = int(scroll_offset * total_tasks)
            else:
                start_index = 0

            for idx, t in enumerate(visible_tasks):
                row_idx = idx
                row_pos_pixels = ((row_idx + 0.4) * (row_height_pixels * 0.8)) + row_height_pixels
                headerpos = row_height_pixels / tree_height
                rely = row_pos_pixels / tree_height
                if headerpos <= rely <= 1:
                    prereq_check = ttk.Checkbutton(tree_frame, variable=selections["prerequisites"][t.id])
                    cont_check = ttk.Checkbutton(tree_frame, variable=selections["contingents"][t.id])
                    prereq_check.place(in_=tree, relx=0.75, rely=rely, anchor="center")
                    cont_check.place(in_=tree, relx=0.85, rely=rely, anchor="center")

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

        search_var.trace("w", update_task_list)
        tree.bind("<Configure>", update_task_list)
        tree.bind("<MouseWheel>", update_task_list)
        tree.bind("<<TreeviewSelect>>", update_task_list)

        ttk.Button(window, text="Confirm", command=save_selections).pack()
        update_task_list()

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
            self.save_data()
            self.update_task_list()
            if new_task:
                self.show_task_details(task_id=task.id, new_task=False)
        except (ValueError, Exception) as e:
            messagebox.showerror("Error", f"Failed to save task: {str(e)}")

    def snooze_task(self, task):
        try:
            days = int(self.detail_widgets["snooze_days"].get())
        except (ValueError, KeyError):
            days = 1
        task.snooze_until = datetime.now() + timedelta(days=days)
        self.save_data()
        self.update_task_list()

    def unsnooze_task(self, task):
        task.snooze_until = None
        self.save_data()
        self.update_task_list()

    def complete_task(self, task):
        task.status = "completed"
        task.completion_date = datetime.now()

        if task.recurrence_type != "none":
            next_revival = task.get_next_revival_time()
            if next_revival:
                # Calculate the time difference between the original due date and first active date
                time_diff = task.due_date - task.first_active_date if task.first_active_date else timedelta(days=0)
                # Create a new task with the same properties
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
                    snooze_until=next_revival
                )
                self.tasks.append(new_task)

        self.save_data()
        self.update_task_list()

    def abandon_task(self, task):
        task.status = "abandoned"
        task.completion_date = datetime.now()
        self.save_data()
        self.update_task_list()

    def revive_task(self, task):
        task.status = "active"
        task.completion_date = None
        task.snooze_until = None
        self.save_data()
        self.update_task_list()

    def manage_people(self):
        people_window = tk.Toplevel(self.root)
        people_window.title("Manage People")
        tree = ttk.Treeview(people_window, columns=("Name", "Job Title", "Department"), show="headings")
        tree.heading("Name", text="Name")
        tree.heading("Job Title", text="Job Title")
        tree.heading("Department", text="Department")
        tree.pack(fill=tk.BOTH, expand=True)
        for person in self.people:
            tree.insert("", "end", values=(person.name, person.job_title, person.department))
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
        ttk.Button(form_frame, text="Add Person", command=partial(self.add_person, fields)).pack()

    def add_person(self, fields):
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
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add person: {str(e)}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    task_manager = TaskManager()
    task_manager.run()
