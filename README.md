# Task-Prioritizer
Schedules tasks and presents a to-do list, showing strictly actionable items sorted by priority.

I've got waaaay too much going on. I have too many meetings for calendar to be useful as a tool to help me schedule. Teams tasks don't have any way to sort by priority or actionability (e.g. contingent tasks). My one-note is getting cluttered and unmanageable if I try to use it to track tasks. I hate hate hate hate Microsoft Project, SAP, Enablon, and every MOC tool in the world. I need something that will just tell me what the next highest priority actionable task is.

Hence this tool. Here are the current features:

- Accounts for contingent/prerequisite relationships between tasks to determine actionability.
- Records task completion dates.
- Can handle automatically recurring tasks.
- Calculates priority based on a combination of safety, hype, $ impact, and the time until the due date.
- allows tasks to be delegated to other people (includes a people manager for adding other people).
- Automatically creates a "remind delegate" task on a weekly basis for each delegated task.
- Can search for tasks based on partial match with any string field in task definition
- Can backdate task completion dates
- Can archive/purge old tasks to clean up the completed task list
- Weekly Schedule "to-do" list: automatically populates weekly/daily recurring items, with a quick-add area for tasks to be done on the current day.

<img width="1606" height="798" alt="Task SS" src="https://github.com/user-attachments/assets/abe33162-86f2-407a-9f3d-b0050fbc1265" />

The above image shows most of the features before the Weekly Schedule was added. The new week-in-advance list is shown in the screenshot below. Past days are grayed-out but can be expanded to show completed tasks for that day. Tasks entered using the quick-add in the Weekly Schedule and then completed are added to history at the beginning of the next day, auto-filled with generic task details. The Weekly Schedule only shows the current week and next Monday.

<img width="1676" height="825" alt="Screenshot 2026-08-18 132535" src="https://github.com/user-attachments/assets/be3c7859-6f81-4249-9e73-fc814b015faa" />

The task manager sends an idle adventurer on a quest each time you complete a task, and awards xp based on the results of the quest and the priority level of the task. I had several AI work together to write me lists of enemies and items, ascii flavoring, and some story and non-story events to pepper into the "adventures":

<img width="749" height="672" alt="Task SS 2" src="https://github.com/user-attachments/assets/12f22c4a-009e-48c2-a9b8-12d0b8f5af01" />

Planned features/fixes:

- Add a settings page for user to tweak things like the dollar ammount he considers high for impact, etc..
- Use a calendar/date-picker instead of typing in the dates
- User can "log in" (persistent to workstation). Actionable tasks are those delegated to himself.
- Task and people lists sync with server over network.
- People hierarchy (lead for area, lead for department)
- Department/area hierarchy (sub-departments)
- Tasks can be delegated to a department or area rather than a user. In this case, a "delegate new task" task will be assigned to the leader of that department or area.
- Email integration? Maybe a button to email delegates a canned reminder and complete "remind delegate" tasks automatically?
