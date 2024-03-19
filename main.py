from todoist_api_python.api import TodoistAPI
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

api = TodoistAPI("f33e38b843a30cdd91e534313f8cbec8969a3c22")

mydb = mysql.connector.connect(
  host=os.getenv('HOSTNAME'),
  user=os.getenv('USER'),
  password=os.getenv('PASSWORD'), 
  database="strategicus"
)

mycursor = mydb.cursor()
tables = []
mycursor.execute("SHOW TABLES")
tables = [i[0] for i in mycursor.fetchall()]

if "goals_projects" not in tables:
    mycursor.execute("CREATE TABLE goals_projects (pid BIGINT PRIMARY KEY, name VARCHAR(255))")

if "goals_sections" not in tables:
    mycursor.execute("CREATE TABLE goals_sections (sid BIGINT PRIMARY KEY, name VARCHAR(255), pid BIGINT, FOREIGN KEY (pid) REFERENCES goals_projects(pid))")

if "goals_tasks" not in tables:
    mycursor.execute("""CREATE TABLE goals_tasks (
                     tid BIGINT PRIMARY KEY, 
                     content VARCHAR(255), 
                     priority INT, 
                     due_date DATE, 
                     pid BIGINT, 
                     sid BIGINT, 
                     parent_id BIGINT, 
                     FOREIGN KEY (pid) REFERENCES goals_projects(pid), 
                     FOREIGN KEY (sid) REFERENCES goals_sections(sid), 
                     FOREIGN KEY (parent_id) REFERENCES goals_tasks(tid))
                     """)



allProjects = []
allSections = []
allTasks = []
# allSubtasks = []


class Project:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.sections = []
        self.tasks = []

    def __str__(self):
        sSections = ''
        sTasks = ''
        for i in self.sections:
            sSections += i.name + ', '
        for i in self.tasks:
            sTasks += i.content + ', '
        return f'Project: {self.name}; Sections: [{sSections}]; Tasks: [{sTasks}]'

class Section:
    def __init__(self, id, name, project_id):
        self.id = id
        self.name = name
        self.tasks = []
        self.project_id = project_id
        for i in allProjects:
            if i.id == project_id:
                i.sections.append(self)
    
    def __str__(self):
        sTasks = ''
        for i in self.tasks:
            sTasks += i.content + ', '
        return f'Section: {self.name}; Tasks: [{sTasks}]'

class Task:
    def __init__(self, id, content, priority, labels, due_date, project_id, section_id, parent_id):
        self.id = id
        self.content = content
        self.priority = priority
        self.labels = labels
        self.due_date = due_date
        self.project_id = project_id
        self.section_id = section_id
        self.parent_id = parent_id
        self.subtasks = []
        for i in allProjects:
            if i.id == project_id:
                i.tasks.append(self)
        for i in allSections:
            if i.id == section_id:
                i.tasks.append(self)
        for i in allTasks:
            if i.id == parent_id:
                i.subtasks.append(i)

    def __str__(self):
        return f'Task: {self.content}, Priority: {self.priority}, Labels: {self.labels}, Due Date: {self.due_date}'

def dlProjects():
    try :
        projects = api.get_projects()
        for project in projects:
            allProjects.append(Project(project.id, project.name))
        return projects
    except Exception as error:
        print(error)
        return None
    
def dlSections():
    try:
        sections = api.get_sections()
        for section in sections:
            allSections.append(Section(section.id, section.name, section.project_id))
        return sections
    except Exception as error:
        print(error)
        return None

def dlTasks():
    try:
        tasks = api.get_tasks()
        for task in tasks:
            # if task.parent_id is not None:
            #     allSubtasks.append(Task(task.id, task.content, task.priority, task.labels, task.due.date, task.project_id, task.section_id, task.parent_id))
            # else:
            if task.due is None:
                allTasks.append(Task(task.id, task.content, task.priority, task.labels, task.due, task.project_id, task.section_id, task.parent_id)) #getting task.due.date causes errors and prevents subtasks from being gathered, since some tasks don't have a due date
            else:
                allTasks.append(Task(task.id, task.content, task.priority, task.labels, task.due.date, task.project_id, task.section_id, task.parent_id))
        return tasks
    except Exception as error:
        print(error)
        return None




dlProjects()
dlSections()
dlTasks()
sql = "INSERT INTO goals_projects (pid, name) VALUES (%s, %s)"
val = []
pInserted = []
mycursor.execute("SELECT pid FROM goals_projects")
pInserted = [i[0] for i in mycursor.fetchall()]
for i in allProjects:
    # print(i)
    if int(i.id) not in pInserted:
        pInserted.append(i.id)
        val.append((int(i.id), i.name))
mycursor.executemany(sql, val)
mydb.commit()
print(mycursor.rowcount, "was inserted.")  

sql = "INSERT INTO goals_sections (sid, name, pid) VALUES (%s, %s, %s)"
val = []
sInserted = []
mycursor.execute("SELECT sid FROM goals_sections")
sInserted = [i[0] for i in mycursor.fetchall()]
for i in allSections:
    if int(i.id) not in sInserted:
        sInserted.append(i.id)
        val.append((int(i.id), i.name, int(i.project_id)))
mycursor.executemany(sql, val)
mydb.commit()
print(mycursor.rowcount, "was inserted.")


sql = "INSERT INTO goals_tasks (tid, content, priority, due_date, pid, sid, parent_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
val = []
tInserted = []
mycursor.execute("SELECT tid FROM goals_tasks")
tInserted = [i[0] for i in mycursor.fetchall()]
for i in allTasks:
    if int(i.id) not in tInserted:
        tInserted.append(i.id)
        val.append((int(i.id), i.content, i.priority, i.due_date, i.project_id, i.section_id, i.parent_id))
mycursor.executemany(sql, val)
mydb.commit()
print(mycursor.rowcount, "was inserted.")
# for i in allSections:
#     print(i)
# for i in allTasks:
#     print(i)
# print('SUBTASKS')
# for i in allSubtasks:
#     print(i)
