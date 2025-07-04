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
- Sends an idle adventurer on a quest each time you complete a task, and awards xp based on the results of the quest and the priority level of the task.

![Prioritizer Screenshot 1](https://github.com/user-attachments/assets/29c02aec-b444-4a0d-9dc7-8591e472237f)

Planned features/fixes:

- Add a settings page for user to tweak things like the dollar ammount he considers high for impact, etc..
- Use a calendar/date-picker instead of typing in the dates
- User can "log in" (persistent to workstation). Actionable tasks are those delegated to himself.
- Task and people lists sync with server over network.
- People hierarchy (lead for area, lead for department)
- Department/area hierarchy (sub-departments)
- Tasks can be delegated to a department or area rather than a user. In this case, a "delegate new task" task will be assigned to the leader of that department or area.
- Email integration? Maybe a button to email delegates a canned reminder and complete "remind delegate" tasks automatically?
